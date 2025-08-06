import os
import logging
import time
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
import openai
from pathlib import Path
import json
import numpy as np
from src.core.supabase_client import get_supabase_manager

logger = logging.getLogger(__name__)

@dataclass
class RetrievedDocument:
    """Represents a retrieved document with metadata"""
    content: str
    source: str
    score: float
    metadata: Dict
    category: str
    title: str

class RAGService:
    """
    Retrieval-Augmented Generation service for WhatsApp chatbot using Supabase pgvector
    Integrates seamlessly with existing customer context and CRM data
    """
    
    def __init__(self, knowledge_base_path: str = "knowledge_base"):
        self.knowledge_base_path = Path(knowledge_base_path)
        self.supabase = None
        self.openai_client = None
        self.initialize_rag_system()
    
    def initialize_rag_system(self):
        """Initialize Supabase pgvector and OpenAI client"""
        try:
            # Initialize Supabase connection (reuse existing)
            self.supabase = get_supabase_manager()
            if not self.supabase.is_connected():
                raise Exception("Supabase connection failed")
            
            # Initialize OpenAI client for embeddings
            self.openai_client = openai.OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
            
            logger.info("RAG system initialized successfully with Supabase pgvector")
            
        except Exception as e:
            logger.error(f"Failed to initialize RAG system: {e}")
            raise
    
    def ingest_knowledge_base(self) -> bool:
        """
        Ingest all markdown files from knowledge base directory into Supabase
        Uses upsert to handle updates efficiently
        """
        try:
            documents_processed = 0
            
            # Process all markdown files
            for md_file in self.knowledge_base_path.rglob("*.md"):
                content = self._process_markdown_file(md_file)
                if content:
                    # Generate embedding using OpenAI
                    embedding = self._generate_embedding(content)
                    if embedding is None:
                        continue
                    
                    # Prepare document data
                    doc_data = {
                        'content': content,
                        'source': str(md_file.relative_to(self.knowledge_base_path)),
                        'category': md_file.parent.name,
                        'title': self._extract_title_from_content(content),
                        'metadata': {
                            "filename": md_file.name,
                            "last_modified": str(md_file.stat().st_mtime),
                            "file_size": len(content),
                            "word_count": len(content.split())
                        },
                        'embedding': embedding
                    }
                    
                    # Insert into Supabase (upsert to handle updates)
                    result = self.supabase.client.table('knowledge_documents')\
                        .upsert(doc_data, on_conflict='source')\
                        .execute()
                    
                    if result.data:
                        documents_processed += 1
                        logger.debug(f"Ingested: {md_file.name}")
            
            if documents_processed > 0:
                logger.info(f"Successfully ingested {documents_processed} documents into knowledge base")
                return True
            else:
                logger.warning("No documents found to ingest")
                return False
                
        except Exception as e:
            logger.error(f"Failed to ingest knowledge base: {e}")
            return False
    
    def _generate_embedding(self, text: str) -> Optional[List[float]]:
        """Generate embedding using OpenAI API with retry logic"""
        max_retries = 3
        for attempt in range(max_retries):
            try:
                response = self.openai_client.embeddings.create(
                    model="text-embedding-3-small",
                    input=text[:8000],  # Limit input size
                    encoding_format="float"
                )
                return response.data[0].embedding
            except Exception as e:
                logger.warning(f"Embedding generation attempt {attempt + 1} failed: {e}")
                if attempt == max_retries - 1:
                    logger.error(f"Failed to generate embedding after {max_retries} attempts")
                    return None
                time.sleep(2 ** attempt)  # Exponential backoff
    
    def _process_markdown_file(self, file_path: Path) -> Optional[str]:
        """Process a markdown file and extract content"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Basic preprocessing
            content = content.strip()
            if len(content) < 50:  # Skip very short files
                return None
                
            return content
            
        except Exception as e:
            logger.error(f"Failed to process file {file_path}: {e}")
            return None
    
    def _extract_title_from_content(self, content: str) -> str:
        """Extract title from markdown content"""
        lines = content.split('\n')
        for line in lines:
            if line.startswith('# '):
                return line[2:].strip()
        return "Untitled Document"
    
    def query_knowledge_base(self, 
                           query: str, 
                           customer_context: Optional[Dict] = None,
                           top_k: int = 5) -> List[RetrievedDocument]:
        """
        Query the knowledge base for relevant documents using Supabase pgvector
        Enhanced with customer context for better personalization
        
        Args:
            query: User's question or message
            customer_context: Customer information from CRM
            top_k: Number of documents to retrieve
            
        Returns:
            List of relevant documents with scores
        """
        try:
            # Start timing for performance monitoring
            start_time = time.time()
            
            # Enhance query with customer context
            enhanced_query = self._enhance_query_with_context(query, customer_context)
            
            # Generate embedding for the query
            query_embedding = self._generate_embedding(enhanced_query)
            if query_embedding is None:
                return []
            
            # Build the query with optional customer context filtering
            similarity_threshold = 0.5  # Lowered further for better document recall
            
            # Base query using pgvector cosine similarity
            base_query = """
                SELECT 
                    content,
                    source,
                    category,
                    title,
                    metadata,
                    1 - (embedding <=> %s::vector) as similarity_score
                FROM knowledge_documents
                WHERE 1 - (embedding <=> %s::vector) > %s
            """
            
            params = [query_embedding, query_embedding, similarity_threshold]
            
            # Add customer context filtering if available
            if customer_context:
                industry = customer_context.get('industry')
                lead_status = customer_context.get('lead_status')
                company_size = self._determine_company_size(customer_context)
                
                # Filter by industry if available
                if industry and industry.lower() in ['healthcare', 'finance', 'financial', 'ecommerce', 'retail', 'manufacturing']:
                    base_query += " AND (category = %s OR category = 'services')"
                    params.append(industry.lower())
                
                # Prioritize pricing and sales content for qualified leads
                if lead_status in ['qualified', 'hot', 'proposal', 'negotiation']:
                    base_query += " AND (category IN ('services', 'pricing', 'sales') OR metadata->>'category' = 'pricing')"
            
            # Order by similarity and limit results
            base_query += " ORDER BY similarity_score DESC LIMIT %s"
            params.append(top_k)
            
            # Execute query
            result = self.supabase.execute_raw_sql(base_query, tuple(params))
            
            # Convert to RetrievedDocument objects
            retrieved_docs = []
            for row in result:
                retrieved_docs.append(RetrievedDocument(
                    content=row['content'],
                    source=row['source'],
                    score=float(row['similarity_score']),
                    metadata=row['metadata'] or {},
                    category=row['category'],
                    title=row['title'] or 'Untitled'
                ))
            
            # Log query for analytics
            self._log_rag_query(query, customer_context, len(retrieved_docs), time.time() - start_time)
            
            logger.info(f"Retrieved {len(retrieved_docs)} documents for query: {query[:50]}... (took {time.time() - start_time:.2f}s)")
            return retrieved_docs
            
        except Exception as e:
            logger.error(f"Failed to query knowledge base: {e}")
            return []
    
    def _enhance_query_with_context(self, query: str, customer_context: Optional[Dict]) -> str:
        """Enhance query with customer context for better retrieval"""
        if not customer_context:
            return query
        
        context_parts = [query]
        
        # Add industry context
        if customer_context.get('industry'):
            context_parts.append(f"industry: {customer_context['industry']}")
        
        # Add company size context
        company_size = self._determine_company_size(customer_context)
        if company_size:
            context_parts.append(f"company size: {company_size}")
        
        # Add lead status context for relevant content
        if customer_context.get('lead_status') in ['qualified', 'hot']:
            context_parts.append("pricing information services")
        
        return " ".join(context_parts)
    
    def _determine_company_size(self, customer_context: Dict) -> Optional[str]:
        """Determine company size from customer context"""
        # Check if company size is directly available
        if customer_context.get('company_size'):
            return customer_context['company_size']
        
        # Try to infer from deals or other context
        deals = customer_context.get('deals', [])
        if deals:
            max_deal_value = max([deal.get('value', 0) for deal in deals])
            if max_deal_value > 50000:
                return 'large'
            elif max_deal_value > 10000:
                return 'medium'
            else:
                return 'small'
        
        return None
    
    def get_contextual_prompt(self, 
                            query: str, 
                            retrieved_docs: List[RetrievedDocument],
                            customer_context: Optional[Dict] = None) -> str:
        """
        Build enhanced prompt with retrieved knowledge and customer context
        Integrates seamlessly with existing customer personalization
        """
        # Base system prompt
        system_prompt = """You are the AI Assistant for Rian Infotech, specializing in AI automation solutions.

IMPORTANT: Use the following business knowledge to provide accurate, helpful responses. Always prioritize information from the retrieved documents over general knowledge.

RETRIEVED BUSINESS KNOWLEDGE:
"""
        
        # Add retrieved documents (limit to top 3 for context window management)
        for i, doc in enumerate(retrieved_docs[:3]):
            system_prompt += f"\n--- Document {i+1}: {doc.title} (Category: {doc.category}) ---\n"
            # Limit content length to manage context window
            content_preview = doc.content[:1200] if len(doc.content) > 1200 else doc.content
            system_prompt += content_preview
            if len(doc.content) > 1200:
                system_prompt += "\n[Content truncated for brevity]"
            system_prompt += "\n"
        
        # Add customer personalization (integrates with existing system)
        if customer_context and customer_context.get('name'):
            customer_name = customer_context['name']
            company = customer_context.get('company', '')
            lead_status = customer_context.get('lead_status', 'new')
            industry = customer_context.get('industry', '')
            
            system_prompt += f"""
CUSTOMER CONTEXT:
- Name: {customer_name}
- Company: {company}
- Industry: {industry}
- Lead Status: {lead_status}

RESPONSE GUIDELINES:
1. Address the customer by name: "{customer_name}"
2. Reference their company when relevant: "{company}"
3. Use the retrieved business knowledge to provide specific, accurate information
4. If discussing pricing, reference appropriate packages based on their company size/needs
5. For {industry} industry, highlight relevant industry-specific solutions
6. Be helpful, professional, and personalized
7. If you don't have specific information in the knowledge base, acknowledge it and offer to connect them with our team
8. Always provide actionable next steps when appropriate

CRITICAL: Base your responses on the retrieved business knowledge above. Do not make up information not contained in the documents.
"""
        else:
            system_prompt += """
RESPONSE GUIDELINES:
1. Use the retrieved business knowledge to provide accurate information
2. Be helpful, professional, and concise
3. Focus on Rian Infotech's actual services and capabilities
4. If you don't have specific information, acknowledge it and offer to connect them with our team
5. Always provide actionable next steps when appropriate

CRITICAL: Base your responses on the retrieved business knowledge above. Do not make up information not contained in the documents.
"""
        
        return system_prompt
    
    def _log_rag_query(self, query: str, customer_context: Optional[Dict], 
                      documents_retrieved: int, response_time: float):
        """Log RAG query for analytics and optimization"""
        try:
            log_data = {
                'query_text': query,
                'customer_phone': customer_context.get('phone_number') if customer_context else None,
                'customer_context': customer_context,
                'documents_retrieved': documents_retrieved,
                'response_generated': documents_retrieved > 0,
                'response_time_ms': int(response_time * 1000)
            }
            
            self.supabase.client.table('rag_query_logs').insert(log_data).execute()
            
        except Exception as e:
            logger.warning(f"Failed to log RAG query: {e}")
    
    def get_knowledge_stats(self) -> Dict:
        """Get statistics about the knowledge base"""
        try:
            # Get document count and categories
            stats_query = """
                SELECT 
                    COUNT(*) as total_documents,
                    COUNT(DISTINCT category) as total_categories,
                    MAX(updated_at) as last_updated,
                    AVG(LENGTH(content)) as avg_content_length
                FROM knowledge_documents
            """
            
            result = self.supabase.execute_raw_sql(stats_query)
            
            if result:
                stats = result[0]
                
                # Get category breakdown
                category_query = """
                    SELECT category, COUNT(*) as count 
                    FROM knowledge_documents 
                    GROUP BY category 
                    ORDER BY count DESC
                """
                category_result = self.supabase.execute_raw_sql(category_query)
                
                categories = {row['category']: row['count'] for row in category_result}
                
                return {
                    "total_documents": stats['total_documents'],
                    "total_categories": stats['total_categories'],
                    "categories": categories,
                    "avg_content_length": int(stats['avg_content_length']) if stats['avg_content_length'] else 0,
                    "status": "healthy" if stats['total_documents'] > 0 else "empty",
                    "last_updated": str(stats['last_updated']) if stats['last_updated'] else "never"
                }
            else:
                return {"total_documents": 0, "status": "empty"}
                
        except Exception as e:
            logger.error(f"Failed to get knowledge stats: {e}")
            return {"error": str(e)}
    
    def update_document(self, source: str, content: str, category: str) -> bool:
        """Update a specific document in the knowledge base"""
        try:
            # Generate new embedding
            embedding = self._generate_embedding(content)
            if embedding is None:
                return False
            
            # Update document
            doc_data = {
                'content': content,
                'source': source,
                'category': category,
                'title': self._extract_title_from_content(content),
                'embedding': embedding,
                'metadata': {
                    "last_modified": str(time.time()),
                    "file_size": len(content),
                    "word_count": len(content.split())
                }
            }
            
            result = self.supabase.client.table('knowledge_documents')\
                .upsert(doc_data, on_conflict='source')\
                .execute()
            
            if result.data:
                logger.info(f"Updated document: {source}")
                return True
            else:
                return False
            
        except Exception as e:
            logger.error(f"Failed to update document {source}: {e}")
            return False

# Global RAG service instance
_rag_service = None

def get_rag_service() -> RAGService:
    """Get global RAG service instance"""
    global _rag_service
    if _rag_service is None:
        _rag_service = RAGService()
    return _rag_service 
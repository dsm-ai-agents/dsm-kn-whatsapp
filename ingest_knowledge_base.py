#!/usr/bin/env python3
"""
Knowledge Base Ingestion Script for RAG System
Ingests markdown documents into Supabase pgvector for AI chatbot
"""

import os
import sys
import logging
from pathlib import Path

# Add the src directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.services.rag_service import get_rag_service

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    """Main ingestion function"""
    print("🧠 RAG Knowledge Base Ingestion")
    print("=" * 50)
    
    try:
        # Initialize RAG service
        print("📡 Initializing RAG service...")
        rag_service = get_rag_service()
        
        # Check current knowledge base status
        print("📊 Checking current knowledge base status...")
        stats = rag_service.get_knowledge_stats()
        print(f"Current documents: {stats.get('total_documents', 0)}")
        print(f"Categories: {stats.get('total_categories', 0)}")
        
        if stats.get('total_documents', 0) > 0:
            response = input("\n⚠️  Knowledge base already contains documents. Continue? (y/N): ")
            if response.lower() != 'y':
                print("Ingestion cancelled.")
                return
        
        # Start ingestion
        print("\n📚 Starting knowledge base ingestion...")
        success = rag_service.ingest_knowledge_base()
        
        if success:
            print("\n✅ Knowledge base ingestion completed successfully!")
            
            # Show updated stats
            print("\n📊 Updated knowledge base statistics:")
            updated_stats = rag_service.get_knowledge_stats()
            print(f"Total documents: {updated_stats.get('total_documents', 0)}")
            print(f"Total categories: {updated_stats.get('total_categories', 0)}")
            print(f"Categories breakdown:")
            
            categories = updated_stats.get('categories', {})
            for category, count in categories.items():
                print(f"  - {category}: {count} documents")
            
            print(f"Average content length: {updated_stats.get('avg_content_length', 0)} characters")
            print(f"Status: {updated_stats.get('status', 'unknown')}")
            
        else:
            print("\n❌ Knowledge base ingestion failed!")
            return 1
            
    except Exception as e:
        logger.error(f"Ingestion failed: {e}")
        print(f"\n❌ Error during ingestion: {e}")
        return 1
    
    print("\n🎉 RAG system is ready for use!")
    return 0

def test_rag_system():
    """Test the RAG system with sample queries"""
    print("\n🧪 Testing RAG system...")
    
    try:
        rag_service = get_rag_service()
        
        # Test queries
        test_queries = [
            "What are your pricing packages?",
            "Do you have healthcare solutions?",
            "What AI automation services do you offer?",
            "How much does the Business Package cost?",
            "Tell me about your company"
        ]
        
        for query in test_queries:
            print(f"\n🔍 Testing query: '{query}'")
            
            # Test with sample customer context
            customer_context = {
                'name': 'Test Customer',
                'company': 'Test Corp',
                'industry': 'healthcare',
                'lead_status': 'qualified'
            }
            
            docs = rag_service.query_knowledge_base(query, customer_context, top_k=3)
            
            if docs:
                print(f"  ✅ Found {len(docs)} relevant documents")
                for i, doc in enumerate(docs[:2]):
                    print(f"    {i+1}. {doc.title} (Score: {doc.score:.3f}, Category: {doc.category})")
            else:
                print("  ❌ No relevant documents found")
        
        print("\n✅ RAG system testing completed!")
        
    except Exception as e:
        print(f"\n❌ RAG testing failed: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit_code = main()
    
    if exit_code == 0:
        # Run tests if ingestion was successful
        test_exit_code = test_rag_system()
        exit_code = max(exit_code, test_exit_code)
    
    sys.exit(exit_code) 
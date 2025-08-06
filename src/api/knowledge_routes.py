from flask import Blueprint, request, jsonify
from src.services.rag_service import get_rag_service
from src.utils.auth import require_auth
import logging

logger = logging.getLogger(__name__)

knowledge_bp = Blueprint('knowledge', __name__)

@knowledge_bp.route('/api/knowledge/stats', methods=['GET'])
@require_auth
def get_knowledge_stats():
    """Get knowledge base statistics"""
    try:
        rag_service = get_rag_service()
        stats = rag_service.get_knowledge_stats()
        
        return jsonify({
            'status': 'success',
            'data': stats
        })
        
    except Exception as e:
        logger.error(f"Failed to get knowledge stats: {e}")
        return jsonify({
            'status': 'error',
            'message': 'Failed to retrieve knowledge base statistics'
        }), 500

@knowledge_bp.route('/api/knowledge/search', methods=['POST'])
@require_auth
def search_knowledge():
    """Search knowledge base for testing"""
    try:
        data = request.get_json()
        query = data.get('query', '')
        customer_context = data.get('customer_context', {})
        top_k = data.get('top_k', 5)
        
        if not query:
            return jsonify({
                'status': 'error',
                'message': 'Query is required'
            }), 400
        
        rag_service = get_rag_service()
        results = rag_service.query_knowledge_base(query, customer_context, top_k=top_k)
        
        # Format results for API response
        formatted_results = []
        for doc in results:
            formatted_results.append({
                'title': doc.title,
                'content': doc.content[:500] + '...' if len(doc.content) > 500 else doc.content,
                'source': doc.source,
                'category': doc.category,
                'score': doc.score,
                'metadata': doc.metadata
            })
        
        return jsonify({
            'status': 'success',
            'data': {
                'query': query,
                'customer_context': customer_context,
                'results': formatted_results,
                'total_results': len(formatted_results)
            }
        })
        
    except Exception as e:
        logger.error(f"Failed to search knowledge base: {e}")
        return jsonify({
            'status': 'error',
            'message': 'Failed to search knowledge base'
        }), 500

@knowledge_bp.route('/api/knowledge/refresh', methods=['POST'])
@require_auth
def refresh_knowledge_base():
    """Refresh knowledge base by re-ingesting all documents"""
    try:
        rag_service = get_rag_service()
        success = rag_service.ingest_knowledge_base()
        
        if success:
            # Get updated stats
            stats = rag_service.get_knowledge_stats()
            
            return jsonify({
                'status': 'success',
                'message': 'Knowledge base refreshed successfully',
                'data': stats
            })
        else:
            return jsonify({
                'status': 'error',
                'message': 'Failed to refresh knowledge base'
            }), 500
            
    except Exception as e:
        logger.error(f"Failed to refresh knowledge base: {e}")
        return jsonify({
            'status': 'error',
            'message': 'Failed to refresh knowledge base'
        }), 500

@knowledge_bp.route('/api/knowledge/test-rag', methods=['POST'])
@require_auth
def test_rag_response():
    """Test RAG-enhanced response generation"""
    try:
        data = request.get_json()
        message = data.get('message', '')
        customer_context = data.get('customer_context', {})
        
        if not message:
            return jsonify({
                'status': 'error',
                'message': 'Message is required'
            }), 400
        
        # Import here to avoid circular imports
        from src.handlers.ai_handler_rag import generate_ai_response_with_rag
        
        # Generate RAG-enhanced response
        response = generate_ai_response_with_rag(
            message_text=message,
            customer_context=customer_context
        )
        
        # Also get the raw knowledge retrieval for debugging
        rag_service = get_rag_service()
        retrieved_docs = rag_service.query_knowledge_base(message, customer_context, top_k=3)
        
        return jsonify({
            'status': 'success',
            'data': {
                'message': message,
                'response': response,
                'customer_context': customer_context,
                'retrieved_documents': [
                    {
                        'title': doc.title,
                        'category': doc.category,
                        'score': doc.score,
                        'source': doc.source
                    } for doc in retrieved_docs
                ],
                'rag_used': len(retrieved_docs) > 0
            }
        })
        
    except Exception as e:
        logger.error(f"Failed to test RAG response: {e}")
        return jsonify({
            'status': 'error',
            'message': 'Failed to generate RAG response'
        }), 500

@knowledge_bp.route('/api/knowledge/update-document', methods=['POST'])
@require_auth
def update_document():
    """Update a specific document in the knowledge base"""
    try:
        data = request.get_json()
        source = data.get('source', '')
        content = data.get('content', '')
        category = data.get('category', '')
        
        if not source or not content or not category:
            return jsonify({
                'status': 'error',
                'message': 'Source, content, and category are required'
            }), 400
        
        rag_service = get_rag_service()
        success = rag_service.update_document(source, content, category)
        
        if success:
            return jsonify({
                'status': 'success',
                'message': f'Document {source} updated successfully'
            })
        else:
            return jsonify({
                'status': 'error',
                'message': 'Failed to update document'
            }), 500
            
    except Exception as e:
        logger.error(f"Failed to update document: {e}")
        return jsonify({
            'status': 'error',
            'message': 'Failed to update document'
        }), 500

@knowledge_bp.route('/api/knowledge/analytics', methods=['GET'])
@require_auth
def get_rag_analytics():
    """Get RAG usage analytics"""
    try:
        # Get analytics from the database
        from src.core.supabase_client import get_supabase_manager
        supabase = get_supabase_manager()
        
        # Get query statistics
        analytics_query = """
            SELECT 
                COUNT(*) as total_queries,
                COUNT(CASE WHEN documents_retrieved > 0 THEN 1 END) as successful_queries,
                AVG(response_time_ms) as avg_response_time,
                AVG(documents_retrieved) as avg_documents_retrieved,
                DATE_TRUNC('day', created_at) as query_date,
                COUNT(*) as daily_queries
            FROM rag_query_logs 
            WHERE created_at >= NOW() - INTERVAL '7 days'
            GROUP BY DATE_TRUNC('day', created_at)
            ORDER BY query_date DESC
        """
        
        result = supabase.execute_raw_sql(analytics_query)
        
        # Get top queries
        top_queries_sql = """
            SELECT 
                query_text,
                COUNT(*) as frequency,
                AVG(documents_retrieved) as avg_docs,
                AVG(response_time_ms) as avg_time
            FROM rag_query_logs 
            WHERE created_at >= NOW() - INTERVAL '7 days'
            GROUP BY query_text
            ORDER BY frequency DESC
            LIMIT 10
        """
        
        top_queries = supabase.execute_raw_sql(top_queries_sql)
        
        return jsonify({
            'status': 'success',
            'data': {
                'daily_stats': result,
                'top_queries': top_queries,
                'summary': {
                    'total_queries': sum(row['daily_queries'] for row in result),
                    'success_rate': (sum(row['successful_queries'] for row in result) / 
                                   max(sum(row['total_queries'] for row in result), 1)) * 100,
                    'avg_response_time': sum(row['avg_response_time'] or 0 for row in result) / max(len(result), 1)
                }
            }
        })
        
    except Exception as e:
        logger.error(f"Failed to get RAG analytics: {e}")
        return jsonify({
            'status': 'error',
            'message': 'Failed to retrieve analytics'
        }), 500 
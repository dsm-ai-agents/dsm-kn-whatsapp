"""
Analytics Dashboard API Routes for Phase 3A
Provides endpoints for viewing business intelligence and analytics data
"""

from flask import Blueprint, request, jsonify
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import logging

from src.services.analytics_service import get_analytics_service
from src.utils.auth import require_auth

logger = logging.getLogger(__name__)

analytics_bp = Blueprint('analytics', __name__)

@analytics_bp.route('/api/analytics/dashboard', methods=['GET'])
@require_auth
def get_analytics_dashboard():
    """
    Get comprehensive analytics dashboard data
    
    Query Parameters:
        days: Number of days to include (default: 7)
        phone_number: Filter by specific phone number (optional)
    """
    try:
        days = int(request.args.get('days', 7))
        phone_number = request.args.get('phone_number')
        
        analytics_service = get_analytics_service()
        
        # Get business intelligence summary
        bi_summary = analytics_service.get_business_intelligence_summary(days=days)
        
        # Get recent conversation analytics
        conversation_analytics = analytics_service.get_conversation_analytics(
            phone_number=phone_number,
            start_date=datetime.utcnow() - timedelta(days=days),
            limit=50
        )
        
        # Get top lead scores
        lead_scoring = analytics_service.get_lead_scoring_analytics(
            min_score=50.0,
            limit=20
        )
        
        # Calculate key metrics
        dashboard_data = {
            'summary': bi_summary,
            'recent_conversations': conversation_analytics,
            'top_leads': lead_scoring,
            'period': {
                'days': days,
                'start_date': (datetime.utcnow() - timedelta(days=days)).isoformat(),
                'end_date': datetime.utcnow().isoformat()
            }
        }
        
        return jsonify({
            'status': 'success',
            'data': dashboard_data
        })
        
    except Exception as e:
        logger.error(f"Failed to get analytics dashboard: {e}")
        return jsonify({
            'status': 'error',
            'message': 'Failed to retrieve analytics dashboard'
        }), 500

@analytics_bp.route('/api/analytics/conversations', methods=['GET'])
@require_auth
def get_conversation_analytics():
    """
    Get detailed conversation analytics
    
    Query Parameters:
        phone_number: Filter by phone number (optional)
        start_date: Start date filter (ISO format, optional)
        end_date: End date filter (ISO format, optional)
        limit: Maximum records to return (default: 100)
    """
    try:
        phone_number = request.args.get('phone_number')
        start_date_str = request.args.get('start_date')
        end_date_str = request.args.get('end_date')
        limit = int(request.args.get('limit', 100))
        
        # Parse dates
        start_date = None
        end_date = None
        if start_date_str:
            start_date = datetime.fromisoformat(start_date_str.replace('Z', '+00:00'))
        if end_date_str:
            end_date = datetime.fromisoformat(end_date_str.replace('Z', '+00:00'))
        
        analytics_service = get_analytics_service()
        conversations = analytics_service.get_conversation_analytics(
            phone_number=phone_number,
            start_date=start_date,
            end_date=end_date,
            limit=limit
        )
        
        return jsonify({
            'status': 'success',
            'data': {
                'conversations': conversations,
                'total_count': len(conversations),
                'filters': {
                    'phone_number': phone_number,
                    'start_date': start_date_str,
                    'end_date': end_date_str,
                    'limit': limit
                }
            }
        })
        
    except Exception as e:
        logger.error(f"Failed to get conversation analytics: {e}")
        return jsonify({
            'status': 'error',
            'message': 'Failed to retrieve conversation analytics'
        }), 500

@analytics_bp.route('/api/analytics/leads', methods=['GET'])
@require_auth
def get_lead_analytics():
    """
    Get lead scoring analytics
    
    Query Parameters:
        min_score: Minimum lead score filter (default: 0)
        limit: Maximum records to return (default: 100)
    """
    try:
        min_score = float(request.args.get('min_score', 0))
        limit = int(request.args.get('limit', 100))
        
        analytics_service = get_analytics_service()
        leads = analytics_service.get_lead_scoring_analytics(
            min_score=min_score,
            limit=limit
        )
        
        # Calculate lead distribution
        score_ranges = {
            'high_quality': [l for l in leads if l.get('overall_score', 0) >= 80],
            'medium_quality': [l for l in leads if 50 <= l.get('overall_score', 0) < 80],
            'low_quality': [l for l in leads if l.get('overall_score', 0) < 50]
        }
        
        return jsonify({
            'status': 'success',
            'data': {
                'leads': leads,
                'distribution': {
                    'high_quality_count': len(score_ranges['high_quality']),
                    'medium_quality_count': len(score_ranges['medium_quality']),
                    'low_quality_count': len(score_ranges['low_quality']),
                    'total_count': len(leads)
                },
                'filters': {
                    'min_score': min_score,
                    'limit': limit
                }
            }
        })
        
    except Exception as e:
        logger.error(f"Failed to get lead analytics: {e}")
        return jsonify({
            'status': 'error',
            'message': 'Failed to retrieve lead analytics'
        }), 500

@analytics_bp.route('/api/analytics/performance', methods=['GET'])
@require_auth
def get_performance_analytics():
    """
    Get system performance analytics
    
    Query Parameters:
        endpoint: Filter by endpoint (optional)
        hours: Number of hours to include (default: 24)
    """
    try:
        endpoint = request.args.get('endpoint')
        hours = int(request.args.get('hours', 24))
        
        analytics_service = get_analytics_service()
        
        # Query performance tracking data using Supabase
        start_time = (datetime.utcnow() - timedelta(hours=hours)).isoformat()
        
        query = analytics_service.supabase.client.table('performance_tracking')\
            .select('*')\
            .gte('timestamp', start_time)\
            .order('timestamp', desc=True)\
            .limit(500)
        
        if endpoint:
            query = query.eq('endpoint', endpoint)
        
        result = query.execute()
        performance_data = result.data or []
        
        # Calculate performance metrics
        if performance_data:
            execution_times = [p.get('execution_time_ms', 0) for p in performance_data]
            avg_execution_time = sum(execution_times) / len(execution_times)
            max_execution_time = max(execution_times)
            min_execution_time = min(execution_times)
            
            success_count = len([p for p in performance_data if p.get('status') == 'success'])
            error_count = len([p for p in performance_data if p.get('status') == 'error'])
            success_rate = (success_count / len(performance_data)) * 100 if performance_data else 0
        else:
            avg_execution_time = 0
            max_execution_time = 0
            min_execution_time = 0
            success_rate = 0
            success_count = 0
            error_count = 0
        
        return jsonify({
            'status': 'success',
            'data': {
                'performance_records': performance_data,
                'metrics': {
                    'avg_execution_time_ms': round(avg_execution_time, 2),
                    'max_execution_time_ms': max_execution_time,
                    'min_execution_time_ms': min_execution_time,
                    'success_rate_percent': round(success_rate, 2),
                    'success_count': success_count,
                    'error_count': error_count,
                    'total_requests': len(performance_data)
                },
                'filters': {
                    'endpoint': endpoint,
                    'hours': hours,
                    'start_time': start_time
                }
            }
        })
        
    except Exception as e:
        logger.error(f"Failed to get performance analytics: {e}")
        return jsonify({
            'status': 'error',
            'message': 'Failed to retrieve performance analytics'
        }), 500

@analytics_bp.route('/api/analytics/business-intelligence', methods=['GET'])
@require_auth
def get_business_intelligence():
    """
    Get comprehensive business intelligence metrics
    
    Query Parameters:
        days: Number of days to include (default: 30)
    """
    try:
        days = int(request.args.get('days', 30))
        
        analytics_service = get_analytics_service()
        
        # Get business intelligence summary
        bi_summary = analytics_service.get_business_intelligence_summary(days=days)
        
        # Get daily breakdown from database
        start_date = (datetime.utcnow() - timedelta(days=days)).date().isoformat()
        
        result = analytics_service.supabase.client.table('business_intelligence_metrics')\
            .select('*')\
            .gte('metric_date', start_date)\
            .order('metric_date', desc=True)\
            .execute()
        
        daily_metrics = result.data or []
        
        # Calculate trends
        if len(daily_metrics) >= 2:
            latest = daily_metrics[0]
            previous = daily_metrics[1]
            
            trends = {
                'conversations_trend': _calculate_trend(
                    latest.get('total_conversations', 0),
                    previous.get('total_conversations', 0)
                ),
                'leads_trend': _calculate_trend(
                    latest.get('leads_generated', 0),
                    previous.get('leads_generated', 0)
                ),
                'conversion_trend': _calculate_trend(
                    latest.get('conversion_rate', 0),
                    previous.get('conversion_rate', 0)
                )
            }
        else:
            trends = {
                'conversations_trend': 0,
                'leads_trend': 0,
                'conversion_trend': 0
            }
        
        return jsonify({
            'status': 'success',
            'data': {
                'summary': bi_summary,
                'daily_metrics': daily_metrics,
                'trends': trends,
                'period': {
                    'days': days,
                    'start_date': start_date,
                    'end_date': datetime.utcnow().date().isoformat()
                }
            }
        })
        
    except Exception as e:
        logger.error(f"Failed to get business intelligence: {e}")
        return jsonify({
            'status': 'error',
            'message': 'Failed to retrieve business intelligence'
        }), 500

@analytics_bp.route('/api/analytics/update-daily-metrics', methods=['POST'])
@require_auth
def update_daily_metrics():
    """
    Manually trigger daily metrics calculation
    
    Body Parameters:
        date: Date to calculate metrics for (ISO format, optional, defaults to today)
    """
    try:
        data = request.get_json() or {}
        date_str = data.get('date')
        
        if date_str:
            metric_date = datetime.fromisoformat(date_str).date()
        else:
            metric_date = datetime.utcnow().date()
        
        analytics_service = get_analytics_service()
        success = analytics_service.update_daily_metrics(metric_date)
        
        if success:
            return jsonify({
                'status': 'success',
                'message': f'Daily metrics updated for {metric_date.isoformat()}'
            })
        else:
            return jsonify({
                'status': 'error',
                'message': 'Failed to update daily metrics'
            }), 500
        
    except Exception as e:
        logger.error(f"Failed to update daily metrics: {e}")
        return jsonify({
            'status': 'error',
            'message': 'Failed to update daily metrics'
        }), 500

@analytics_bp.route('/api/analytics/journey-funnel', methods=['GET'])
@require_auth
def get_journey_funnel():
    """
    Get customer journey funnel analytics
    """
    try:
        analytics_service = get_analytics_service()
        
        # Get journey stage distribution from contacts
        result = analytics_service.supabase.client.table('contacts')\
            .select('journey_stage', count='exact')\
            .execute()
        
        contacts = result.data or []
        
        # Count by journey stage
        journey_counts = {
            'discovery': 0,
            'interest': 0,
            'evaluation': 0,
            'decision': 0
        }
        
        for contact in contacts:
            stage = contact.get('journey_stage', 'discovery')
            if stage in journey_counts:
                journey_counts[stage] += 1
        
        # Calculate conversion rates
        total_contacts = sum(journey_counts.values())
        if total_contacts > 0:
            conversion_rates = {
                'discovery_to_interest': (journey_counts['interest'] / max(journey_counts['discovery'], 1)) * 100,
                'interest_to_evaluation': (journey_counts['evaluation'] / max(journey_counts['interest'], 1)) * 100,
                'evaluation_to_decision': (journey_counts['decision'] / max(journey_counts['evaluation'], 1)) * 100,
                'overall_conversion': (journey_counts['decision'] / total_contacts) * 100
            }
        else:
            conversion_rates = {
                'discovery_to_interest': 0,
                'interest_to_evaluation': 0,
                'evaluation_to_decision': 0,
                'overall_conversion': 0
            }
        
        return jsonify({
            'status': 'success',
            'data': {
                'journey_counts': journey_counts,
                'conversion_rates': conversion_rates,
                'total_contacts': total_contacts,
                'funnel_data': [
                    {'stage': 'Discovery', 'count': journey_counts['discovery'], 'percentage': 100},
                    {'stage': 'Interest', 'count': journey_counts['interest'], 'percentage': round(conversion_rates['discovery_to_interest'], 1)},
                    {'stage': 'Evaluation', 'count': journey_counts['evaluation'], 'percentage': round(conversion_rates['interest_to_evaluation'], 1)},
                    {'stage': 'Decision', 'count': journey_counts['decision'], 'percentage': round(conversion_rates['evaluation_to_decision'], 1)}
                ]
            }
        })
        
    except Exception as e:
        logger.error(f"Failed to get journey funnel: {e}")
        return jsonify({
            'status': 'error',
            'message': 'Failed to retrieve journey funnel'
        }), 500

def _calculate_trend(current: float, previous: float) -> float:
    """Calculate percentage trend between two values"""
    if previous == 0:
        return 100.0 if current > 0 else 0.0
    return ((current - previous) / previous) * 100
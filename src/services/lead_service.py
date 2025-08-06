"""
Lead Management Service
======================
Handles all lead-related business logic and database operations.
"""

from datetime import datetime
from typing import Dict, List, Optional
from src.core.supabase_client import get_supabase_manager
from src.utils.error_handling import APIError

class LeadService:
    def __init__(self):
        self.supabase = get_supabase_manager()
        
    def get_leads(self, filters: Dict, page: int, per_page: int) -> Dict:
        """Get paginated leads with filters"""
        # Build base query conditions
        def apply_filters(query):
            if filters.get('status'):
                query = query.eq('lead_status', filters['status'])
            if filters.get('source'):
                query = query.eq('lead_source', filters['source'])
            if filters.get('search'):
                search = filters['search']
                query = query.or_(f"company_name.ilike.%{search}%")
            return query
        
        # Get total count
        count_query = self.supabase.client.table('lead_details').select('*', count='exact')
        count_query = apply_filters(count_query)
        count_result = count_query.execute()
        total = count_result.count
        
        # Get paginated results
        data_query = self.supabase.client.table('lead_details').select('*')
        data_query = apply_filters(data_query)
        paginated_result = data_query.range((page - 1) * per_page, page * per_page - 1).execute()
        leads = paginated_result.data
        
        return {
            'leads': leads,
            'total': total,
            'page': page,
            'per_page': per_page
        }
        
    def get_lead_details(self, lead_id: str) -> Dict:
        """Get detailed information about a specific lead"""
        lead = self.supabase.client.table('lead_details').select('*').eq('id', lead_id).execute()
        
        if not lead.data:
            raise APIError(f"Lead not found: {lead_id}", 404)
            
        return lead.data[0]
        
    def create_lead(self, data: Dict) -> Dict:
        """Create a new lead"""
        # Validate required fields
        required_fields = ['contact_id', 'lead_source']
        for field in required_fields:
            if field not in data:
                raise APIError(f"Missing required field: {field}", 400)
        # Only keep allowed fields
        allowed_fields = [
            'contact_id', 'company_name', 'job_title', 'industry', 'company_size', 'annual_revenue', 'location',
            'lead_source', 'lead_status', 'lead_score', 'budget_range', 'timeline', 'specific_needs',
            'technical_requirements', 'preferred_contact_method', 'preferred_contact_time', 'timezone'
        ]
        data = {k: v for k, v in data.items() if k in allowed_fields}
        # Add timestamps
        data['created_at'] = datetime.utcnow().isoformat()
        data['updated_at'] = data['created_at']
        # Insert lead
        result = self.supabase.client.table('lead_details').insert(data).execute()
        if not result.data:
            raise APIError("Failed to create lead", 500)
        return result.data[0]
        
    def update_lead(self, lead_id: str, data: Dict) -> Dict:
        """Update an existing lead"""
        # Check if lead exists
        lead = self.get_lead_details(lead_id)
        # Only keep allowed fields
        allowed_fields = [
            'contact_id', 'company_name', 'job_title', 'industry', 'company_size', 'annual_revenue', 'location',
            'lead_source', 'lead_status', 'lead_score', 'budget_range', 'timeline', 'specific_needs',
            'technical_requirements', 'preferred_contact_method', 'preferred_contact_time', 'timezone'
        ]
        data = {k: v for k, v in data.items() if k in allowed_fields}
        # Update timestamps
        data['updated_at'] = datetime.utcnow().isoformat()
        # Update lead
        result = self.supabase.client.table('lead_details').update(data).eq('id', lead_id).execute()
        if not result.data:
            raise APIError("Failed to update lead", 500)
        return result.data[0]
        
    def get_lead_interactions(self, lead_id: str) -> List[Dict]:
        """Get interaction history for a lead"""
        interactions = self.supabase.client.table('lead_interactions').select('*').eq('lead_id', lead_id).execute()
        return interactions.data
        
    def add_lead_interaction(self, lead_id: str, data: Dict) -> Dict:
        """Add a new interaction for a lead"""
        # Validate lead exists
        self.get_lead_details(lead_id)
        # Only keep allowed fields
        allowed_fields = [
            'interaction_type', 'summary', 'follow_up_actions', 'next_follow_up_date'
        ]
        data = {k: v for k, v in data.items() if k in allowed_fields}
        # Add lead_id and timestamps
        data['lead_id'] = lead_id
        data['created_at'] = datetime.utcnow().isoformat()
        # Insert interaction
        result = self.supabase.client.table('lead_interactions').insert(data).execute()
        if not result.data:
            raise APIError("Failed to add interaction", 500)
        return result.data[0]
        
    def get_lead_requirements(self, lead_id: str) -> List[Dict]:
        """Get requirements for a lead"""
        requirements = self.supabase.client.table('lead_requirements').select('*').eq('lead_id', lead_id).execute()
        return requirements.data
        
    def add_lead_requirement(self, lead_id: str, data: Dict) -> Dict:
        """Add a new requirement for a lead"""
        # Validate lead exists
        self.get_lead_details(lead_id)
        # Only keep allowed fields
        allowed_fields = [
            'requirement_type', 'requirement_details', 'priority', 'status', 'deadline'
        ]
        data = {k: v for k, v in data.items() if k in allowed_fields}
        # Add lead_id and timestamps
        data['lead_id'] = lead_id
        data['created_at'] = datetime.utcnow().isoformat()
        # Insert requirement
        result = self.supabase.client.table('lead_requirements').insert(data).execute()
        if not result.data:
            raise APIError("Failed to add requirement", 500)
        return result.data[0]
        
    def get_lead_analytics(self) -> Dict:
        """Get lead analytics and metrics"""
        # Get total leads
        total_leads = self.supabase.client.table('lead_details').select('id', count='exact').execute()
        
        # Get leads by status
        status_counts = self.supabase.client.table('lead_details').select('lead_status', count='exact').execute()
        
        # Get leads by source
        source_counts = self.supabase.client.table('lead_details').select('lead_source', count='exact').execute()
        
        # Calculate conversion rate
        converted = sum(1 for s in status_counts.data if s['lead_status'] == 'Converted')
        conversion_rate = (converted / total_leads.count) * 100 if total_leads.count > 0 else 0
        
        return {
            'total_leads': total_leads.count,
            'status_distribution': status_counts.data,
            'source_distribution': source_counts.data,
            'conversion_rate': round(conversion_rate, 2)
        }
        
    def delete_lead(self, lead_id: str) -> bool:
        """Delete a lead by id"""
        result = self.supabase.client.table('lead_details').delete().eq('id', lead_id).execute()
        if result.count == 0:
            raise APIError(f"Lead not found: {lead_id}", 404)
        return True 
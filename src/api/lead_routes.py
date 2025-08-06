"""
Lead Management API Routes
=========================
Handles all lead-related API endpoints for the WhatsApp CRM system.
"""

from flask import Blueprint, request, jsonify
from src.services.lead_service import LeadService
from src.utils.auth import require_auth
from src.utils.error_handling import handle_api_error

lead_bp = Blueprint('leads', __name__)
lead_service = LeadService()

@lead_bp.route('/leads', methods=['GET'])
@require_auth
@handle_api_error
def get_leads():
    """Get all leads with filtering and pagination"""
    filters = request.args.to_dict()
    page = int(request.args.get('page', 1))
    per_page = int(request.args.get('per_page', 10))
    
    leads = lead_service.get_leads(filters, page, per_page)
    return jsonify(leads)

@lead_bp.route('/leads/<lead_id>', methods=['GET'])
@require_auth
@handle_api_error
def get_lead(lead_id):
    """Get detailed information about a specific lead"""
    lead = lead_service.get_lead_details(lead_id)
    return jsonify(lead)

@lead_bp.route('/leads', methods=['POST'])
@require_auth
@handle_api_error
def create_lead():
    """Create a new lead"""
    data = request.json
    lead = lead_service.create_lead(data)
    return jsonify(lead), 201

@lead_bp.route('/leads/<lead_id>', methods=['PUT'])
@require_auth
@handle_api_error
def update_lead(lead_id):
    """Update an existing lead"""
    data = request.json
    lead = lead_service.update_lead(lead_id, data)
    return jsonify(lead)

@lead_bp.route('/leads/<lead_id>/interactions', methods=['GET'])
@require_auth
@handle_api_error
def get_lead_interactions(lead_id):
    """Get interaction history for a lead"""
    interactions = lead_service.get_lead_interactions(lead_id)
    return jsonify(interactions)

@lead_bp.route('/leads/<lead_id>/interactions', methods=['POST'])
@require_auth
@handle_api_error
def add_lead_interaction(lead_id):
    """Add a new interaction for a lead"""
    data = request.json
    interaction = lead_service.add_lead_interaction(lead_id, data)
    return jsonify(interaction), 201

@lead_bp.route('/leads/<lead_id>/requirements', methods=['GET'])
@require_auth
@handle_api_error
def get_lead_requirements(lead_id):
    """Get requirements for a lead"""
    requirements = lead_service.get_lead_requirements(lead_id)
    return jsonify(requirements)

@lead_bp.route('/leads/<lead_id>/requirements', methods=['POST'])
@require_auth
@handle_api_error
def add_lead_requirement(lead_id):
    """Add a new requirement for a lead"""
    data = request.json
    requirement = lead_service.add_lead_requirement(lead_id, data)
    return jsonify(requirement), 201

@lead_bp.route('/leads/analytics', methods=['GET'])
@require_auth
@handle_api_error
def get_lead_analytics():
    """Get lead analytics and metrics"""
    analytics = lead_service.get_lead_analytics()
    return jsonify(analytics) 
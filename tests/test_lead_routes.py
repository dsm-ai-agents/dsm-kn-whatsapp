import unittest
import json
from app import app
from src.services.lead_service import LeadService
from src.core.supabase_client import get_supabase_manager

class TestLeadRoutes(unittest.TestCase):
    def setUp(self):
        self.app = app.test_client()
        self.supabase = get_supabase_manager()
        self.lead_service = LeadService()
        # Create a test contact
        self.test_contact = {
            'phone_number': '+1234567890',
            'name': 'Test Contact',
            'email': 'test@example.com',
            'tags': ['lead'],
        }
        contact_result = self.supabase.table('contacts').insert(self.test_contact).execute()
        self.contact_id = contact_result.data[0]['id']
        # Create a test lead
        self.test_lead = {
            'contact_id': self.contact_id,
            'name': 'Test Lead',
            'company_name': 'Test Company',
            'email': 'test@example.com',
            'phone': '+1234567890',
            'lead_status': 'New',
            'lead_source': 'Website',
            'notes': 'Test notes'
        }
        self.created_lead = self.lead_service.create_lead(self.test_lead)

    def tearDown(self):
        try:
            self.lead_service.delete_lead(self.created_lead['id'])
        except:
            pass
        try:
            self.supabase.table('contacts').delete().eq('id', self.contact_id).execute()
        except:
            pass

    def test_get_leads(self):
        """Test getting all leads"""
        response = self.app.get('/api/leads')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIn('leads', data)
        self.assertIn('total', data)
        self.assertIn('page', data)
        self.assertIn('per_page', data)

    def test_get_lead_details(self):
        """Test getting lead details"""
        response = self.app.get(f'/api/leads/{self.created_lead["id"]}')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data['id'], self.created_lead['id'])
        self.assertEqual(data['name'], self.test_lead['name'])

    def test_create_lead(self):
        """Test creating a new lead"""
        new_lead = {
            'contact_id': self.contact_id,
            'name': 'New Lead',
            'company_name': 'New Company',
            'email': 'new@example.com',
            'phone': '+1987654321',
            'lead_status': 'New',
            'lead_source': 'Website'
        }
        
        response = self.app.post('/api/leads',
                               data=json.dumps(new_lead),
                               content_type='application/json')
        
        self.assertEqual(response.status_code, 201)
        data = json.loads(response.data)
        self.assertEqual(data['name'], new_lead['name'])
        self.assertEqual(data['company_name'], new_lead['company_name'])
        
        # Clean up
        self.lead_service.delete_lead(data['id'])

    def test_update_lead(self):
        """Test updating a lead"""
        update_data = {
            'name': 'Updated Lead',
            'lead_status': 'Contacted'
        }
        
        response = self.app.put(f'/api/leads/{self.created_lead["id"]}',
                              data=json.dumps(update_data),
                              content_type='application/json')
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data['name'], update_data['name'])
        self.assertEqual(data['lead_status'], update_data['lead_status'])

    def test_get_lead_interactions(self):
        """Test getting lead interactions"""
        # Add an interaction first
        interaction_data = {
            'type': 'Call',
            'description': 'Initial contact call'
        }
        self.lead_service.add_lead_interaction(self.created_lead['id'], interaction_data)
        
        response = self.app.get(f'/api/leads/{self.created_lead["id"]}/interactions')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertTrue(any(i['type'] == interaction_data['type'] for i in data))

    def test_add_lead_interaction(self):
        """Test adding a lead interaction"""
        interaction_data = {
            'type': 'Email',
            'description': 'Follow-up email'
        }
        
        response = self.app.post(f'/api/leads/{self.created_lead["id"]}/interactions',
                               data=json.dumps(interaction_data),
                               content_type='application/json')
        
        self.assertEqual(response.status_code, 201)
        data = json.loads(response.data)
        self.assertEqual(data['type'], interaction_data['type'])
        self.assertEqual(data['description'], interaction_data['description'])

    def test_get_lead_requirements(self):
        """Test getting lead requirements"""
        # Add a requirement first
        requirement_data = {
            'title': 'Initial Requirement',
            'description': 'Need to implement feature X',
            'status': 'Pending'
        }
        self.lead_service.add_lead_requirement(self.created_lead['id'], requirement_data)
        
        response = self.app.get(f'/api/leads/{self.created_lead["id"]}/requirements')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertTrue(any(r['title'] == requirement_data['title'] for r in data))

    def test_add_lead_requirement(self):
        """Test adding a lead requirement"""
        requirement_data = {
            'title': 'New Requirement',
            'description': 'Need to implement feature Y',
            'status': 'Pending'
        }
        
        response = self.app.post(f'/api/leads/{self.created_lead["id"]}/requirements',
                               data=json.dumps(requirement_data),
                               content_type='application/json')
        
        self.assertEqual(response.status_code, 201)
        data = json.loads(response.data)
        self.assertEqual(data['title'], requirement_data['title'])
        self.assertEqual(data['description'], requirement_data['description'])

    def test_get_lead_analytics(self):
        """Test getting lead analytics"""
        response = self.app.get('/api/leads/analytics')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIn('total_leads', data)
        self.assertIn('status_distribution', data)
        self.assertIn('source_distribution', data)
        self.assertIn('conversion_rate', data)

    def test_error_handling(self):
        """Test error handling"""
        # Test getting non-existent lead
        response = self.app.get('/api/leads/non-existent-id')
        self.assertEqual(response.status_code, 404)
        
        # Test updating non-existent lead
        response = self.app.put('/api/leads/non-existent-id',
                              data=json.dumps({'name': 'Test'}),
                              content_type='application/json')
        self.assertEqual(response.status_code, 404)
        
        # Test creating lead with missing required fields
        response = self.app.post('/api/leads',
                               data=json.dumps({'lead_source': 'Website'}),
                               content_type='application/json')
        self.assertEqual(response.status_code, 400)

if __name__ == '__main__':
    unittest.main() 
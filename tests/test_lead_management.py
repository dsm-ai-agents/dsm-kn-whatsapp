import unittest
from datetime import datetime
from src.services.lead_service import LeadService
from src.utils.error_handling import APIError
from src.core.supabase_client import get_supabase_manager
import uuid

class TestLeadManagement(unittest.TestCase):
    def setUp(self):
        self.supabase = get_supabase_manager()
        self.lead_service = LeadService()
        # Create a test contact using the correct method
        self.test_contact = {
            'phone_number': '+1234567890',
            'name': 'Test Contact',
            'email': 'test@example.com',
            'tags': ['lead'],
        }
        contact = self.supabase.get_or_create_contact(
            phone_number=self.test_contact['phone_number'],
            name=self.test_contact['name'],
            email=self.test_contact['email'],
            tags=self.test_contact['tags']
        )
        self.contact_id = contact['id']
        # Create a test lead
        self.test_lead = {
            'contact_id': self.contact_id,
            'company_name': 'Test Company',
            'job_title': 'Manager',
            'industry': 'IT',
            'company_size': '50-100',
            'annual_revenue': 1000000,
            'location': 'Test City',
            'lead_source': 'website',
            'lead_status': 'new',
            'lead_score': 50,
            'budget_range': '10k-20k',
            'timeline': 'Q3',
            'specific_needs': 'CRM integration',
            'technical_requirements': 'API access',
            'preferred_contact_method': 'email',
            'preferred_contact_time': 'morning',
            'timezone': 'UTC'
        }
        self.created_lead = self.lead_service.create_lead(self.test_lead)

    def tearDown(self):
        # Clean up test data
        try:
            self.lead_service.delete_lead(self.created_lead['id'])
        except:
            pass
        try:
            self.supabase.table('contacts').delete().eq('id', self.contact_id).execute()
        except:
            pass

    def test_create_lead(self):
        """Test creating a new lead"""
        lead_data = {
            'contact_id': self.contact_id,
            'company_name': 'New Test Company',
            'job_title': 'Developer',
            'industry': 'Finance',
            'company_size': '10-20',
            'annual_revenue': 500000,
            'location': 'New City',
            'lead_source': 'website',
            'lead_status': 'new',
            'lead_score': 60,
            'budget_range': '5k-10k',
            'timeline': 'Q4',
            'specific_needs': 'Automation',
            'technical_requirements': 'Webhook',
            'preferred_contact_method': 'phone',
            'preferred_contact_time': 'afternoon',
            'timezone': 'Asia/Kolkata'
        }
        
        lead = self.lead_service.create_lead(lead_data)
        
        self.assertIsNotNone(lead)
        self.assertEqual(lead['company_name'], lead_data['company_name'])
        self.assertEqual(lead['job_title'], lead_data['job_title'])
        self.assertEqual(lead['industry'], lead_data['industry'])
        self.assertEqual(lead['company_size'], lead_data['company_size'])
        self.assertEqual(lead['annual_revenue'], lead_data['annual_revenue'])
        self.assertEqual(lead['location'], lead_data['location'])
        self.assertEqual(lead['lead_source'], lead_data['lead_source'])
        self.assertEqual(lead['lead_status'], lead_data['lead_status'])
        self.assertEqual(lead['lead_score'], lead_data['lead_score'])
        self.assertEqual(lead['budget_range'], lead_data['budget_range'])
        self.assertEqual(lead['timeline'], lead_data['timeline'])
        self.assertEqual(lead['specific_needs'], lead_data['specific_needs'])
        self.assertEqual(lead['technical_requirements'], lead_data['technical_requirements'])
        self.assertEqual(lead['preferred_contact_method'], lead_data['preferred_contact_method'])
        self.assertEqual(lead['preferred_contact_time'], lead_data['preferred_contact_time'])
        self.assertEqual(lead['timezone'], lead_data['timezone'])
        
        # Clean up
        self.lead_service.delete_lead(lead['id'])

    def test_get_lead(self):
        """Test retrieving a lead"""
        lead = self.lead_service.get_lead_details(self.created_lead['id'])
        
        self.assertIsNotNone(lead)
        self.assertEqual(lead['id'], self.created_lead['id'])
        self.assertEqual(lead['company_name'], self.test_lead['company_name'])

    def test_update_lead(self):
        """Test updating a lead"""
        update_data = {
            'company_name': 'Updated Company',
            'lead_status': 'contacted',
            'lead_score': 80
        }
        
        updated_lead = self.lead_service.update_lead(self.created_lead['id'], update_data)
        
        self.assertIsNotNone(updated_lead)
        self.assertEqual(updated_lead['company_name'], update_data['company_name'])
        self.assertEqual(updated_lead['lead_status'], update_data['lead_status'])
        self.assertEqual(updated_lead['lead_score'], update_data['lead_score'])

    def test_get_leads_with_filters(self):
        """Test getting leads with filters"""
        # Create another lead with different status
        lead_data = {
            'contact_id': self.contact_id,
            'company_name': 'Another Company',
            'job_title': 'Analyst',
            'industry': 'Retail',
            'company_size': '5-10',
            'annual_revenue': 200000,
            'location': 'Another City',
            'lead_source': 'referral',
            'lead_status': 'contacted',
            'lead_score': 30,
            'budget_range': '1k-5k',
            'timeline': 'Q2',
            'specific_needs': 'Reporting',
            'technical_requirements': 'Dashboard',
            'preferred_contact_method': 'whatsapp',
            'preferred_contact_time': 'evening',
            'timezone': 'Europe/London'
        }
        another_lead = self.lead_service.create_lead(lead_data)
        
        try:
            # Test status filter
            filtered_leads = self.lead_service.get_leads({'status': 'new'}, 1, 10)
            self.assertTrue(any(l['lead_status'] == 'new' for l in filtered_leads['leads']))
            
            # Test source filter
            filtered_leads = self.lead_service.get_leads({'source': 'referral'}, 1, 10)
            self.assertTrue(any(l['lead_source'] == 'referral' for l in filtered_leads['leads']))
            
            # Test search
            filtered_leads = self.lead_service.get_leads({'search': 'Another'}, 1, 10)
            self.assertTrue(any(l['company_name'] == 'Another Company' for l in filtered_leads['leads']))
        finally:
            # Clean up
            self.lead_service.delete_lead(another_lead['id'])

    def test_lead_interactions(self):
        """Test lead interactions"""
        interaction_data = {
            'interaction_type': 'call',
            'summary': 'Initial contact call',
            'follow_up_actions': 'Send proposal',
            'next_follow_up_date': None
        }
        # Test adding interaction
        interaction = self.lead_service.add_lead_interaction(self.created_lead['id'], interaction_data)
        self.assertIsNotNone(interaction)
        self.assertEqual(interaction['interaction_type'], interaction_data['interaction_type'])
        self.assertEqual(interaction['summary'], interaction_data['summary'])
        # Test getting interactions
        interactions = self.lead_service.get_lead_interactions(self.created_lead['id'])
        self.assertTrue(any(i['interaction_type'] == interaction_data['interaction_type'] for i in interactions))

    def test_lead_requirements(self):
        """Test lead requirements"""
        requirement_data = {
            'requirement_type': 'feature',
            'requirement_details': 'Need to implement feature X',
            'priority': 'high',
            'status': 'open',
            'deadline': None
        }
        # Test adding requirement
        requirement = self.lead_service.add_lead_requirement(self.created_lead['id'], requirement_data)
        self.assertIsNotNone(requirement)
        self.assertEqual(requirement['requirement_type'], requirement_data['requirement_type'])
        self.assertEqual(requirement['requirement_details'], requirement_data['requirement_details'])
        self.assertEqual(requirement['status'], requirement_data['status'])
        # Test getting requirements
        requirements = self.lead_service.get_lead_requirements(self.created_lead['id'])
        self.assertTrue(any(r['requirement_type'] == requirement_data['requirement_type'] for r in requirements))

    def test_lead_analytics(self):
        """Test lead analytics"""
        analytics = self.lead_service.get_lead_analytics()
        
        self.assertIsNotNone(analytics)
        self.assertIn('total_leads', analytics)
        self.assertIn('status_distribution', analytics)
        self.assertIn('source_distribution', analytics)
        self.assertIn('conversion_rate', analytics)

    def test_error_handling(self):
        """Test error handling"""
        # Test creating lead with missing required fields
        with self.assertRaises(APIError) as context:
            self.lead_service.create_lead({'lead_source': 'website'})
        self.assertEqual(context.exception.status_code, 400)

        # Test getting non-existent lead with valid UUID
        fake_id = str(uuid.uuid4())
        with self.assertRaises(APIError) as context:
            self.lead_service.get_lead_details(fake_id)
        self.assertEqual(context.exception.status_code, 404)

if __name__ == '__main__':
    unittest.main() 
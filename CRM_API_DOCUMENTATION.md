# 🚀 CRM API Documentation - WhatsApp AI Chatbot
*Complete Customer Relationship Management API Guide*

---

## 📋 Table of Contents

1. [CRM Overview](#-crm-overview)
2. [Contact Management APIs](#-contact-management-apis)
3. [Deal Management APIs](#-deal-management-apis)
4. [Task Management APIs](#-task-management-apis)
5. [Activity Tracking APIs](#-activity-tracking-apis)
6. [Lead Scoring APIs](#-lead-scoring-apis)
7. [Complete Workflows](#-complete-workflows)
8. [Integration Examples](#-integration-examples)
9. [Best Practices](#-best-practices)

---

## 🎯 CRM Overview

The WhatsApp AI Chatbot includes a powerful CRM system that automatically manages:

- **📱 Contact Management**: Store and organize customer information
- **💼 Deal Pipeline**: Track sales opportunities and revenue
- **✅ Task Management**: Manage follow-ups and activities
- **📊 Lead Scoring**: Automatically score leads based on engagement
- **📈 Activity Tracking**: Log all customer interactions
- **🎯 Sales Analytics**: Track performance and conversion rates

### 🏗️ Data Structure

```
Contact (Customer)
├── Basic Info (name, phone, email)
├── CRM Data (company, position, source)
├── Lead Info (status, score, notes)
├── Deals (sales opportunities)
├── Tasks (follow-ups, reminders)
└── Activities (calls, meetings, emails)
```

---

## 👥 Contact Management APIs

### 1. Get CRM Contacts
**Endpoint**: `GET /api/crm/contacts`

**Description**: Retrieve contacts with complete CRM information including lead scores, statuses, and business details.

**Query Parameters**:
```
limit: 20 (max 100)
offset: 0  
status: qualified|new|hot|cold|customer
```

**Sample Request**:
```bash
curl -X GET "http://localhost:5001/api/crm/contacts?limit=20&offset=0&status=qualified"
```

**Sample Response**:
```json
{
  "status": "success",
  "data": [
    {
      "id": "contact_12345",
      "phone_number": "919876543210_s_whatsapp_net",
      "name": "John Doe",
      "email": "john.doe@techcorp.com",
      "company": "Tech Corp Solutions",
      "position": "Senior Manager",
      "lead_status": "qualified",
      "lead_score": 85,
      "source": "website",
      "notes": "Interested in enterprise package. Mentioned budget of $50k.",
      "last_contacted_at": "2024-06-12T10:30:00Z",
      "next_follow_up_at": "2024-06-15T14:00:00Z",
      "created_at": "2024-06-10T08:00:00Z"
    },
    {
      "id": "contact_12346",
      "phone_number": "918765432109_s_whatsapp_net",
      "name": "Sarah Johnson",
      "email": "sarah@innovatetech.com",
      "company": "Innovate Technologies",
      "position": "CTO",
      "lead_status": "hot",
      "lead_score": 92,
      "source": "referral",
      "notes": "Ready to sign. Needs demo next week.",
      "last_contacted_at": "2024-06-12T15:45:00Z",
      "next_follow_up_at": "2024-06-13T10:00:00Z",
      "created_at": "2024-06-08T12:30:00Z"
    }
  ],
  "pagination": {
    "limit": 20,
    "offset": 0,
    "count": 2
  }
}
```

**Lead Status Values**:
- `new` - Fresh lead, first contact
- `qualified` - Showed interest, has potential
- `hot` - Ready to buy, high priority
- `cold` - Low interest, long-term nurture
- `customer` - Already purchased

### 2. Update CRM Contact
**Endpoint**: `PUT /api/crm/contact/{contact_id}`

**Description**: Update contact's CRM information including lead status, company details, and follow-up schedules.

**Sample Request**:
```bash
curl -X PUT "http://localhost:5001/api/crm/contact/contact_12345" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "John Doe",
    "email": "john.doe@techcorp.com",
    "company": "Tech Corp Solutions Inc",
    "position": "Senior Manager",
    "lead_status": "hot",
    "lead_score": 90,
    "source": "referral",
    "notes": "Very interested in premium package. Meeting scheduled for next week.",
    "next_follow_up_at": "2024-06-15T14:00:00Z"
  }'
```

**Sample Response**:
```json
{
  "status": "success",
  "message": "Contact updated successfully"
}
```

---

## 💼 Deal Management APIs

### 3. Get CRM Deals
**Endpoint**: `GET /api/crm/deals`

**Description**: Retrieve deals in your sales pipeline with contact information and stage details.

**Query Parameters**:
```
contact_id: specific contact
stage: prospecting|qualification|proposal|negotiation|closed_won|closed_lost
limit: 20 (max 100)
```

**Sample Request**:
```bash
curl -X GET "http://localhost:5001/api/crm/deals?stage=proposal&limit=20"
```

**Sample Response**:
```json
{
  "status": "success",
  "data": [
    {
      "id": "deal_67890",
      "contact_id": "contact_12345",
      "title": "Enterprise Software License",
      "description": "Annual enterprise license for 100 users with premium support",
      "value": 50000.00,
      "currency": "USD",
      "stage": "proposal",
      "probability": 75,
      "expected_close_date": "2024-06-30",
      "created_at": "2024-06-10T09:00:00Z",
      "contact": {
        "name": "John Doe",
        "company": "Tech Corp Solutions",
        "phone_number": "919876543210_s_whatsapp_net"
      }
    },
    {
      "id": "deal_67891",
      "contact_id": "contact_12346",
      "title": "Startup Package",
      "description": "Complete startup solution with 6-month support",
      "value": 25000.00,
      "currency": "USD",
      "stage": "proposal",
      "probability": 90,
      "expected_close_date": "2024-06-20",
      "created_at": "2024-06-08T14:30:00Z",
      "contact": {
        "name": "Sarah Johnson",
        "company": "Innovate Technologies",
        "phone_number": "918765432109_s_whatsapp_net"
      }
    }
  ]
}
```

**Deal Stages**:
- `prospecting` - Initial contact, gathering requirements
- `qualification` - Validating fit and budget
- `proposal` - Formal proposal submitted
- `negotiation` - Terms and pricing discussion
- `closed_won` - Deal successfully closed
- `closed_lost` - Deal lost to competitor or cancelled

### 4. Create CRM Deal
**Endpoint**: `POST /api/crm/deals`

**Description**: Create a new deal in the sales pipeline.

**Sample Request**:
```bash
curl -X POST "http://localhost:5001/api/crm/deals" \
  -H "Content-Type: application/json" \
  -d '{
    "contact_id": "contact_12345",
    "title": "Enterprise Software License",
    "description": "Annual enterprise license for 100 users with premium support",
    "value": 50000.00,
    "currency": "USD",
    "stage": "prospecting",
    "probability": 25,
    "expected_close_date": "2024-07-30"
  }'
```

**Sample Response**:
```json
{
  "status": "success",
  "message": "Deal created successfully",
  "deal_id": "deal_67892"
}
```

### 5. Update CRM Deal
**Endpoint**: `PUT /api/crm/deal/{deal_id}`

**Description**: Update deal information, stage, probability, or value.

**Sample Request**:
```bash
curl -X PUT "http://localhost:5001/api/crm/deal/deal_67890" \
  -H "Content-Type: application/json" \
  -d '{
    "stage": "negotiation",
    "probability": 85,
    "value": 55000.00,
    "expected_close_date": "2024-06-25",
    "description": "Upgraded to premium package with additional features"
  }'
```

**Sample Response**:
```json
{
  "status": "success",
  "message": "Deal updated successfully"
}
```

---

## ✅ Task Management APIs

### 6. Get CRM Tasks
**Endpoint**: `GET /api/crm/tasks`

**Description**: Retrieve tasks and follow-ups with contact and deal context.

**Query Parameters**:
```
contact_id: specific contact
status: pending|completed|overdue
limit: 20 (max 100)
```

**Sample Request**:
```bash
curl -X GET "http://localhost:5001/api/crm/tasks?status=pending&limit=20"
```

**Sample Response**:
```json
{
  "status": "success",
  "data": [
    {
      "id": "task_11111",
      "contact_id": "contact_12345",
      "deal_id": "deal_67890",
      "title": "Follow up on proposal",
      "description": "Call to discuss proposal feedback and address any concerns",
      "task_type": "follow_up",
      "priority": "high",
      "status": "pending",
      "due_date": "2024-06-15T14:00:00Z",
      "created_at": "2024-06-12T09:00:00Z",
      "contact": {
        "name": "John Doe",
        "company": "Tech Corp Solutions",
        "phone_number": "919876543210_s_whatsapp_net"
      },
      "deal": {
        "title": "Enterprise Software License",
        "value": 50000.00,
        "stage": "proposal"
      }
    },
    {
      "id": "task_11112",
      "contact_id": "contact_12346",
      "deal_id": "deal_67891",
      "title": "Send contract for signature",
      "description": "Email final contract with digital signature link",
      "task_type": "document",
      "priority": "urgent",
      "status": "pending",
      "due_date": "2024-06-13T10:00:00Z",
      "created_at": "2024-06-12T16:30:00Z",
      "contact": {
        "name": "Sarah Johnson",
        "company": "Innovate Technologies",
        "phone_number": "918765432109_s_whatsapp_net"
      },
      "deal": {
        "title": "Startup Package",
        "value": 25000.00,
        "stage": "negotiation"
      }
    }
  ]
}
```

**Task Types**:
- `follow_up` - Call or message follow-up
- `meeting` - Schedule or attend meeting
- `document` - Send documents or contracts
- `demo` - Product demonstration
- `proposal` - Prepare or send proposal
- `support` - Customer support activity

**Priority Levels**:
- `urgent` - Needs immediate attention
- `high` - Important, do today
- `medium` - Do this week
- `low` - Do when time permits

### 7. Create CRM Task
**Endpoint**: `POST /api/crm/tasks`

**Description**: Create a new task for follow-up or action item.

**Sample Request**:
```bash
curl -X POST "http://localhost:5001/api/crm/tasks" \
  -H "Content-Type: application/json" \
  -d '{
    "contact_id": "contact_12345",
    "deal_id": "deal_67890",
    "title": "Follow up on proposal",
    "description": "Call to discuss proposal feedback and next steps",
    "task_type": "follow_up",
    "priority": "high",
    "due_date": "2024-06-15T14:00:00Z"
  }'
```

**Sample Response**:
```json
{
  "status": "success",
  "message": "Task created successfully",
  "task_id": "task_11113"
}
```

### 8. Complete CRM Task
**Endpoint**: `POST /api/crm/task/{task_id}/complete`

**Description**: Mark a task as completed.

**Sample Request**:
```bash
curl -X POST "http://localhost:5001/api/crm/task/task_11111/complete"
```

**Sample Response**:
```json
{
  "status": "success",
  "message": "Task completed successfully"
}
```

### 9. Delete CRM Task
**Endpoint**: `DELETE /api/crm/task/{task_id}`

**Description**: Delete a task that's no longer needed.

**Sample Request**:
```bash
curl -X DELETE "http://localhost:5001/api/crm/task/task_11111"
```

**Sample Response**:
```json
{
  "status": "success",
  "message": "Task deleted successfully"
}
```

---

## 📊 Activity Tracking APIs

### 10. Get Contact Activities
**Endpoint**: `GET /api/crm/contact/{contact_id}/activities`

**Description**: Get all activities and interactions for a specific contact.

**Query Parameters**:
```
limit: 20 (max 100)
```

**Sample Request**:
```bash
curl -X GET "http://localhost:5001/api/crm/contact/contact_12345/activities?limit=20"
```

**Sample Response**:
```json
{
  "status": "success",
  "data": [
    {
      "id": "activity_22222",
      "contact_id": "contact_12345",
      "deal_id": "deal_67890",
      "activity_type": "call",
      "title": "Discovery call",
      "description": "Discussed requirements, timeline, and budget. Customer interested in enterprise features.",
      "duration_minutes": 45,
      "outcome": "positive",
      "created_at": "2024-06-12T14:00:00Z",
      "contact": {
        "name": "John Doe",
        "company": "Tech Corp Solutions"
      },
      "deal": {
        "title": "Enterprise Software License",
        "stage": "proposal"
      }
    },
    {
      "id": "activity_22223",
      "contact_id": "contact_12345",
      "deal_id": "deal_67890",
      "activity_type": "email",
      "title": "Sent proposal",
      "description": "Emailed detailed proposal with pricing and implementation timeline",
      "duration_minutes": null,
      "outcome": "sent",
      "created_at": "2024-06-11T16:30:00Z",
      "contact": {
        "name": "John Doe",
        "company": "Tech Corp Solutions"
      },
      "deal": {
        "title": "Enterprise Software License",
        "stage": "proposal"
      }
    }
  ]
}
```

**Activity Types**:
- `call` - Phone call
- `email` - Email communication
- `meeting` - In-person or video meeting
- `whatsapp` - WhatsApp message
- `demo` - Product demonstration
- `proposal` - Proposal related activity

**Outcome Types**:
- `positive` - Good response, moving forward
- `neutral` - No clear direction
- `negative` - Not interested or objection
- `scheduled` - Next meeting scheduled
- `sent` - Document or message sent

### 11. Log CRM Activity
**Endpoint**: `POST /api/crm/activity`

**Description**: Log a new activity or interaction with a contact.

**Sample Request**:
```bash
curl -X POST "http://localhost:5001/api/crm/activity" \
  -H "Content-Type: application/json" \
  -d '{
    "contact_id": "contact_12345",
    "deal_id": "deal_67890",
    "activity_type": "call",
    "title": "Discovery call",
    "description": "Discussed requirements, timeline, and budget. Customer very interested.",
    "duration_minutes": 45,
    "outcome": "positive"
  }'
```

**Sample Response**:
```json
{
  "status": "success",
  "message": "Activity logged successfully"
}
```

---

## 🎯 Lead Scoring APIs

### 12. Calculate Lead Score
**Endpoint**: `POST /api/crm/lead-score/{contact_id}`

**Description**: Calculate and update the lead score for a contact based on their profile and engagement.

**Sample Request**:
```bash
curl -X POST "http://localhost:5001/api/crm/lead-score/contact_12345"
```

**Sample Response**:
```json
{
  "status": "success",
  "message": "Lead score calculated successfully",
  "lead_score": 85
}
```

**Lead Scoring Factors**:
- **Email provided**: +20 points
- **Company information**: +15 points
- **Job position**: +10 points
- **Multiple conversations**: +10 points
- **Quick response time**: +5 points
- **Asked about pricing**: +25 points
- **Requested demo**: +20 points
- **Downloaded resources**: +15 points

**Score Ranges**:
- **90-100**: Excellent lead (hot)
- **75-89**: Good lead (qualified)
- **50-74**: Average lead (qualified)
- **25-49**: Weak lead (cold)
- **0-24**: Poor lead (cold)

---

## 🔄 Complete Workflows

### Workflow 1: New Lead Management
```
1. Contact comes via WhatsApp → Automatically created in contacts
2. Bot engages and collects info → Contact profile updated
3. Lead score calculated → Score assigned based on engagement
4. Task created for follow-up → Sales team notified
5. Deal created if qualified → Pipeline tracking begins
```

**API Sequence**:
```bash
# 1. Contact created automatically via webhook
# 2. Update contact with collected info
PUT /api/crm/contact/{contact_id}

# 3. Calculate lead score
POST /api/crm/lead-score/{contact_id}

# 4. Create follow-up task
POST /api/crm/tasks

# 5. Create deal if qualified
POST /api/crm/deals
```

### Workflow 2: Deal Progression
```
1. Deal created → Initial stage: prospecting
2. Discovery call → Log activity, update deal to qualification
3. Proposal sent → Update stage to proposal
4. Negotiation → Update stage and probability
5. Closed won/lost → Final update with outcome
```

**API Sequence**:
```bash
# 1. Create deal
POST /api/crm/deals

# 2. Log discovery call
POST /api/crm/activity

# 3. Update deal stage
PUT /api/crm/deal/{deal_id}

# 4. Continue updating as deal progresses
PUT /api/crm/deal/{deal_id}
```

### Workflow 3: Task Management
```
1. Task created → Due date set
2. Reminder notifications → System tracks due dates
3. Task completed → Mark as done, log outcome
4. Follow-up tasks → Create next actions if needed
```

**API Sequence**:
```bash
# 1. Create task
POST /api/crm/tasks

# 2. Complete task
POST /api/crm/task/{task_id}/complete

# 3. Log activity outcome
POST /api/crm/activity

# 4. Create follow-up task if needed
POST /api/crm/tasks
```

---

## 💻 Integration Examples

### React Component Example
```javascript
import React, { useState, useEffect } from 'react';

const CRMDashboard = () => {
  const [contacts, setContacts] = useState([]);
  const [deals, setDeals] = useState([]);
  const [tasks, setTasks] = useState([]);

  useEffect(() => {
    // Fetch CRM data
    fetchContacts();
    fetchDeals();
    fetchTasks();
  }, []);

  const fetchContacts = async () => {
    try {
      const response = await fetch('/api/crm/contacts?limit=10&status=qualified');
      const data = await response.json();
      setContacts(data.data);
    } catch (error) {
      console.error('Error fetching contacts:', error);
    }
  };

  const fetchDeals = async () => {
    try {
      const response = await fetch('/api/crm/deals?stage=proposal&limit=10');
      const data = await response.json();
      setDeals(data.data);
    } catch (error) {
      console.error('Error fetching deals:', error);
    }
  };

  const fetchTasks = async () => {
    try {
      const response = await fetch('/api/crm/tasks?status=pending&limit=10');
      const data = await response.json();
      setTasks(data.data);
    } catch (error) {
      console.error('Error fetching tasks:', error);
    }
  };

  const updateContactStatus = async (contactId, newStatus) => {
    try {
      await fetch(`/api/crm/contact/${contactId}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ lead_status: newStatus })
      });
      fetchContacts(); // Refresh data
    } catch (error) {
      console.error('Error updating contact:', error);
    }
  };

  return (
    <div className="crm-dashboard">
      {/* Contacts Section */}
      <section>
        <h2>Top Qualified Leads</h2>
        {contacts.map(contact => (
          <div key={contact.id} className="contact-card">
            <h3>{contact.name}</h3>
            <p>Score: {contact.lead_score}</p>
            <p>Company: {contact.company}</p>
            <button onClick={() => updateContactStatus(contact.id, 'hot')}>
              Mark as Hot Lead
            </button>
          </div>
        ))}
      </section>

      {/* Deals Section */}
      <section>
        <h2>Active Deals</h2>
        {deals.map(deal => (
          <div key={deal.id} className="deal-card">
            <h3>{deal.title}</h3>
            <p>Value: ${deal.value.toLocaleString()}</p>
            <p>Stage: {deal.stage}</p>
            <p>Probability: {deal.probability}%</p>
          </div>
        ))}
      </section>

      {/* Tasks Section */}
      <section>
        <h2>Pending Tasks</h2>
        {tasks.map(task => (
          <div key={task.id} className="task-card">
            <h3>{task.title}</h3>
            <p>Contact: {task.contact.name}</p>
            <p>Due: {new Date(task.due_date).toLocaleDateString()}</p>
            <p>Priority: {task.priority}</p>
          </div>
        ))}
      </section>
    </div>
  );
};

export default CRMDashboard;
```

### Python Integration Example
```python
import requests
import json
from datetime import datetime, timedelta

class CRMIntegration:
    def __init__(self, base_url="http://localhost:5001"):
        self.base_url = base_url
    
    def get_hot_leads(self):
        """Get contacts with high lead scores"""
        response = requests.get(f"{self.base_url}/api/crm/contacts?status=hot&limit=50")
        if response.status_code == 200:
            return response.json()['data']
        return []
    
    def create_follow_up_task(self, contact_id, deal_id, days_from_now=1):
        """Create a follow-up task"""
        due_date = (datetime.now() + timedelta(days=days_from_now)).isoformat()
        
        task_data = {
            "contact_id": contact_id,
            "deal_id": deal_id,
            "title": "Follow up on proposal",
            "description": "Check on proposal status and answer any questions",
            "task_type": "follow_up",
            "priority": "high",
            "due_date": due_date
        }
        
        response = requests.post(
            f"{self.base_url}/api/crm/tasks",
            headers={"Content-Type": "application/json"},
            data=json.dumps(task_data)
        )
        
        return response.status_code == 201
    
    def update_deal_stage(self, deal_id, new_stage, probability=None):
        """Update deal stage and probability"""
        update_data = {"stage": new_stage}
        if probability:
            update_data["probability"] = probability
        
        response = requests.put(
            f"{self.base_url}/api/crm/deal/{deal_id}",
            headers={"Content-Type": "application/json"},
            data=json.dumps(update_data)
        )
        
        return response.status_code == 200
    
    def log_sales_call(self, contact_id, deal_id, outcome, duration_minutes, notes):
        """Log a sales call activity"""
        activity_data = {
            "contact_id": contact_id,
            "deal_id": deal_id,
            "activity_type": "call",
            "title": "Sales call",
            "description": notes,
            "duration_minutes": duration_minutes,
            "outcome": outcome
        }
        
        response = requests.post(
            f"{self.base_url}/api/crm/activity",
            headers={"Content-Type": "application/json"},
            data=json.dumps(activity_data)
        )
        
        return response.status_code == 201

# Usage example
crm = CRMIntegration()

# Get hot leads for today's calls
hot_leads = crm.get_hot_leads()
print(f"Found {len(hot_leads)} hot leads to contact today")

# Log a successful sales call
crm.log_sales_call(
    contact_id="contact_12345",
    deal_id="deal_67890",
    outcome="positive",
    duration_minutes=30,
    notes="Customer is interested, requested formal proposal"
)

# Update deal stage after sending proposal
crm.update_deal_stage("deal_67890", "proposal", probability=75)

# Create follow-up task
crm.create_follow_up_task("contact_12345", "deal_67890", days_from_now=2)
```

---

## 📈 Best Practices

### 1. Lead Scoring Optimization
- **Regular Recalculation**: Update lead scores weekly or after major interactions
- **Custom Rules**: Adjust scoring rules based on your business model
- **Score Thresholds**: Set clear thresholds for different lead statuses
- **A/B Testing**: Test different scoring models to improve conversion

### 2. Deal Management
- **Clear Stages**: Define specific criteria for each deal stage
- **Probability Guidelines**: Set standard probabilities for each stage
- **Regular Updates**: Update deals weekly or after major milestones
- **Lost Deal Analysis**: Track why deals are lost to improve process

### 3. Task Management
- **Specific Titles**: Use clear, actionable task titles
- **Realistic Due Dates**: Set achievable deadlines
- **Priority Levels**: Use priorities consistently across team
- **Follow-up Chains**: Create sequences of related tasks

### 4. Activity Logging
- **Immediate Logging**: Log activities right after they happen
- **Detailed Notes**: Include specific outcomes and next steps
- **Consistent Categories**: Use standard activity types and outcomes
- **Regular Review**: Review activity patterns to improve sales process

### 5. Data Quality
- **Required Fields**: Ensure key contact information is complete
- **Data Validation**: Validate email addresses and phone numbers
- **Duplicate Prevention**: Check for duplicate contacts before creating
- **Regular Cleanup**: Remove or merge duplicate entries

### 6. Integration Tips
- **Error Handling**: Always handle API errors gracefully
- **Rate Limiting**: Respect API rate limits in bulk operations
- **Data Pagination**: Use pagination for large data sets
- **Consistent Updates**: Keep local data synchronized with API

---

## 🔗 Related Resources

- **[Complete API Reference](ALL_APIS_REFERENCE.md)** - All 25 APIs
- **[Main Documentation](API_DOCUMENTATION.md)** - Full system documentation
- **[Quick Reference](API_QUICK_REFERENCE.md)** - Quick lookup guide

---

## 📞 Support

For CRM API support or questions:
- **Email**: support@rianinfotech.com
- **Documentation**: Check this guide first
- **API Status**: Monitor health check endpoint `/health`

---

*This documentation covers all CRM functionality in your WhatsApp AI Chatbot system. The APIs provide complete customer relationship management capabilities from lead capture through deal closure.* 🚀
# Complete API Reference - WhatsApp AI Chatbot
*Accurate as per actual server code structure*

## Base URL
- **Development**: `http://localhost:5001`
- **Production**: Your deployed domain

---

## 1. Core Application APIs

### 1.1 API Information
**Endpoint**: `GET /`
**Description**: Returns API information and available endpoints

**Sample Response**:
```json
{
  "message": "WhatsApp AI Chatbot API",
  "version": "2.1",
  "status": "active",
  "endpoints": {
    "health": "/health",
    "webhook": "/webhook",
    "send_message": "/send-message",
    "start_conversation": "/start-conversation",
    "bulk_message": "/send-bulk-message",
    "api_routes": "/api/*"
  },
  "documentation": "See API_DOCUMENTATION.md for complete API docs"
}
```

### 1.2 Health Check
**Endpoint**: `GET /health`
**Description**: Health check to verify bot status and service connections

**Sample Response**:
```json
{
  "status": "healthy",
  "bot_name": "Rian Assistant",
  "openai_configured": true,
  "wasender_configured": true,
  "supabase_connected": true
}
```

### 1.3 WhatsApp Webhook
**Endpoint**: `POST /webhook`
**Description**: Receives incoming WhatsApp messages from WaSender API

**Sample Request Body**:
```json
{
  "event": "messages.upsert",
  "sessionId": "59a3db5777eacaabad160fa7b284b694c058f205f3c206975f09b7cfd27bac45",
  "data": {
    "messages": {
      "key": {
        "remoteJid": "919876543210@s.whatsapp.net",
        "fromMe": false,
        "id": "3EB0..."
      },
      "messageType": "conversation",
      "conversation": "Hello, I need help with my order"
    }
  }
}
```

**Sample Response**:
```json
{
  "status": "success",
  "message": "Message processed successfully"
}
```

### 1.4 Send Individual Message
**Endpoint**: `POST /send-message`
**Description**: Send a message to a specific WhatsApp number

**Sample Request Body**:
```json
{
  "phone_number": "919876543210",
  "message": "Hello! This is a test message from Rian Infotech bot."
}
```

**Sample Response**:
```json
{
  "status": "success",
  "message": "Message sent successfully to 919876543210",
  "recipient": "919876543210"
}
```

### 1.5 Start AI Conversation
**Endpoint**: `POST /start-conversation`
**Description**: Start an AI conversation with introduction message

**Sample Request Body**:
```json
{
  "phone_number": "919876543210",
  "custom_intro": "Hi! Welcome to Rian Infotech. How can I assist you today?"
}
```

**Sample Response**:
```json
{
  "status": "success",
  "message": "AI conversation started with 919876543210",
  "recipient": "919876543210",
  "intro_message": "Hi! Welcome to Rian Infotech. How can I assist you today?"
}
```

### 1.6 Send Bulk Message
**Endpoint**: `POST /send-bulk-message`
**Description**: Send the same message to multiple WhatsApp numbers

**Sample Request Body**:
```json
{
  "contacts": "919876543210\n918765432109\n917654321098",
  "message": "Hello everyone! This is an important update from Rian Infotech.",
  "campaign_name": "Monthly Newsletter"
}
```

**Sample Response**:
```json
{
  "status": "success",
  "job_id": "bulk_job_20240612_123456",
  "campaign_id": "cam_12345",
  "total_contacts": 3,
  "successful_sends": 2,
  "failed_sends": 1,
  "summary": "Bulk message job completed: 2/3 messages sent successfully",
  "failed_contacts": [
    {
      "contact": "917654321098",
      "error": "Invalid phone number format"
    }
  ]
}
```

---

## 2. Dashboard & Statistics APIs

### 2.1 Dashboard Statistics
**Endpoint**: `GET /api/dashboard-stats`
**Description**: Get comprehensive dashboard statistics

**Sample Response**:
```json
{
  "status": "success",
  "data": {
    "total_contacts": 150,
    "total_conversations": 89,
    "total_messages": 1247,
    "total_campaigns": 12,
    "recent_messages": 45,
    "active_conversations": 23,
    "response_rate": 85.5,
    "avg_response_time": "2.3 minutes"
  }
}
```

### 2.2 Get Contacts
**Endpoint**: `GET /api/contacts?limit=20&offset=0`
**Description**: Get paginated contacts list

**Sample Response**:
```json
{
  "status": "success",
  "data": [
    {
      "id": "contact_123",
      "phone_number": "919876543210_s_whatsapp_net",
      "name": "John Doe",
      "last_message_at": "2024-06-12T10:30:00Z",
      "message_count": 5,
      "created_at": "2024-06-10T08:00:00Z"
    }
  ],
  "pagination": {
    "limit": 20,
    "offset": 0,
    "count": 1
  }
}
```

### 2.3 Get Campaigns
**Endpoint**: `GET /api/campaigns?limit=10`
**Description**: Get recent bulk campaigns

**Sample Response**:
```json
{
  "status": "success",
  "data": [
    {
      "id": "cam_123",
      "name": "Monthly Newsletter",
      "status": "completed",
      "total_contacts": 100,
      "successful_sends": 95,
      "failed_sends": 5,
      "created_at": "2024-06-12T09:00:00Z",
      "message_content": "Hello everyone! This is our monthly update..."
    }
  ]
}
```

### 2.4 Get Campaign Details
**Endpoint**: `GET /api/campaign/{campaign_id}`
**Description**: Get detailed information about a specific campaign

**Sample Response**:
```json
{
  "status": "success",
  "data": {
    "id": "cam_123",
    "name": "Monthly Newsletter",
    "status": "completed",
    "message_content": "Hello everyone! This is our monthly update...",
    "total_contacts": 100,
    "successful_sends": 95,
    "failed_sends": 5,
    "created_at": "2024-06-12T09:00:00Z",
    "completed_at": "2024-06-12T09:15:00Z",
    "message_results": [
      {
        "phone_number": "919876543210",
        "success": true,
        "sent_at": "2024-06-12T09:01:00Z"
      }
    ]
  }
}
```

---

## 3. Conversations APIs

### 3.1 Get Conversations
**Endpoint**: `GET /api/conversations?limit=50&offset=0`
**Description**: Get all conversations with contact details

**Sample Response**:
```json
{
  "status": "success",
  "data": [
    {
      "id": "conv_123",
      "contact": {
        "phone_number": "919876543210_s_whatsapp_net",
        "name": "John Doe",
        "created_at": "2024-06-10T08:00:00Z"
      },
      "last_message_at": "2024-06-12T10:30:00Z",
      "message_count": 5,
      "last_message_preview": "Thank you for your help. I will contact you...",
      "last_message_role": "user"
    }
  ],
  "pagination": {
    "limit": 50,
    "offset": 0,
    "count": 1
  }
}
```

### 3.2 Get Conversation Details
**Endpoint**: `GET /api/conversation/{conversation_id}`
**Description**: Get detailed conversation messages

**Sample Response**:
```json
{
  "status": "success",
  "data": {
    "id": "conv_123",
    "contact": {
      "phone_number": "919876543210_s_whatsapp_net",
      "name": "John Doe",
      "created_at": "2024-06-10T08:00:00Z"
    },
    "messages": [
      {
        "role": "user",
        "content": "Hello, I need help with my order",
        "timestamp": "2024-06-12T10:25:00Z"
      },
      {
        "role": "assistant",
        "content": "Hi! I'm here to help. What's your order number?",
        "timestamp": "2024-06-12T10:26:00Z"
      }
    ],
    "last_message_at": "2024-06-12T10:30:00Z",
    "created_at": "2024-06-12T10:25:00Z"
  }
}
```

### 3.3 Search Conversations
**Endpoint**: `GET /api/conversation/search?q=john`
**Description**: Search conversations by contact name or phone number

**Sample Response**:
```json
{
  "status": "success",
  "data": [
    {
      "id": "conv_123",
      "contact": {
        "phone_number": "919876543210_s_whatsapp_net",
        "name": "John Doe",
        "created_at": "2024-06-10T08:00:00Z"
      },
      "last_message_at": "2024-06-12T10:30:00Z",
      "message_count": 5,
      "last_message_preview": "Thank you for your help...",
      "last_message_role": "user"
    }
  ],
  "query": "john"
}
```

---

## 4. CRM APIs

### 4.1 Get CRM Contacts
**Endpoint**: `GET /api/crm/contacts?limit=20&offset=0&status=qualified`
**Description**: Get contacts with CRM information

**Sample Response**:
```json
{
  "status": "success",
  "data": [
    {
      "id": "contact_123",
      "phone_number": "919876543210_s_whatsapp_net",
      "name": "John Doe",
      "email": "john@example.com",
      "company": "Tech Corp",
      "position": "Manager",
      "lead_status": "qualified",
      "lead_score": 85,
      "source": "website",
      "notes": "Interested in enterprise solution",
      "last_contacted_at": "2024-06-12T10:00:00Z",
      "next_follow_up_at": "2024-06-15T14:00:00Z",
      "created_at": "2024-06-10T08:00:00Z"
    }
  ],
  "pagination": {
    "limit": 20,
    "offset": 0,
    "count": 1
  }
}
```

### 4.2 Update CRM Contact
**Endpoint**: `PUT /api/crm/contact/{contact_id}`
**Description**: Update contact CRM information

**Sample Request Body**:
```json
{
  "name": "John Doe",
  "email": "john.doe@example.com",
  "company": "Tech Solutions Inc",
  "position": "Senior Manager",
  "lead_status": "qualified",
  "lead_score": 90,
  "source": "referral",
  "notes": "Very interested in premium package",
  "next_follow_up_at": "2024-06-15T14:00:00Z"
}
```

**Sample Response**:
```json
{
  "status": "success",
  "message": "Contact updated successfully"
}
```

### 4.3 Get CRM Deals
**Endpoint**: `GET /api/crm/deals?contact_id=contact_123&stage=proposal&limit=20`
**Description**: Get deals with contact information

**Sample Response**:
```json
{
  "status": "success",
  "data": [
    {
      "id": "deal_123",
      "contact_id": "contact_123",
      "title": "Enterprise Software License",
      "description": "Annual enterprise license for 100 users",
      "value": 50000.00,
      "currency": "USD",
      "stage": "proposal",
      "probability": 75,
      "expected_close_date": "2024-06-30",
      "created_at": "2024-06-10T08:00:00Z",
      "contact": {
        "name": "John Doe",
        "company": "Tech Corp"
      }
    }
  ]
}
```

### 4.4 Create CRM Deal
**Endpoint**: `POST /api/crm/deals`
**Description**: Create a new deal

**Sample Request Body**:
```json
{
  "contact_id": "contact_123",
  "title": "Enterprise Software License",
  "description": "Annual enterprise license for 100 users",
  "value": 50000.00,
  "currency": "USD",
  "stage": "prospecting",
  "probability": 25,
  "expected_close_date": "2024-07-30"
}
```

**Sample Response**:
```json
{
  "status": "success",
  "message": "Deal created successfully",
  "deal_id": "deal_124"
}
```

### 4.5 Update CRM Deal
**Endpoint**: `PUT /api/crm/deal/{deal_id}`
**Description**: Update a deal

**Sample Request Body**:
```json
{
  "stage": "negotiation",
  "probability": 85,
  "value": 55000.00,
  "expected_close_date": "2024-06-25"
}
```

**Sample Response**:
```json
{
  "status": "success",
  "message": "Deal updated successfully"
}
```

### 4.6 Get CRM Tasks
**Endpoint**: `GET /api/crm/tasks?contact_id=contact_123&status=pending&limit=20`
**Description**: Get tasks with contact and deal information

**Sample Response**:
```json
{
  "status": "success",
  "data": [
    {
      "id": "task_123",
      "contact_id": "contact_123",
      "deal_id": "deal_123",
      "title": "Follow up on proposal",
      "description": "Call to discuss proposal feedback",
      "task_type": "follow_up",
      "priority": "high",
      "status": "pending",
      "due_date": "2024-06-15T14:00:00Z",
      "created_at": "2024-06-12T09:00:00Z",
      "contact": {
        "name": "John Doe",
        "company": "Tech Corp"
      },
      "deal": {
        "title": "Enterprise Software License"
      }
    }
  ]
}
```

### 4.7 Create CRM Task
**Endpoint**: `POST /api/crm/tasks`
**Description**: Create a new task

**Sample Request Body**:
```json
{
  "contact_id": "contact_123",
  "deal_id": "deal_123",
  "title": "Follow up on proposal",
  "description": "Call to discuss proposal feedback",
  "task_type": "follow_up",
  "priority": "high",
  "due_date": "2024-06-15T14:00:00Z"
}
```

**Sample Response**:
```json
{
  "status": "success",
  "message": "Task created successfully",
  "task_id": "task_124"
}
```

### 4.8 Complete CRM Task
**Endpoint**: `POST /api/crm/task/{task_id}/complete`
**Description**: Mark a task as completed

**Sample Response**:
```json
{
  "status": "success",
  "message": "Task completed successfully"
}
```

### 4.9 Delete CRM Task
**Endpoint**: `DELETE /api/crm/task/{task_id}`
**Description**: Delete a task

**Sample Response**:
```json
{
  "status": "success",
  "message": "Task deleted successfully"
}
```

### 4.10 Get Contact Activities
**Endpoint**: `GET /api/crm/contact/{contact_id}/activities?limit=20`
**Description**: Get activities for a specific contact

**Sample Response**:
```json
{
  "status": "success",
  "data": [
    {
      "id": "activity_123",
      "contact_id": "contact_123",
      "deal_id": "deal_123",
      "activity_type": "call",
      "title": "Discovery call",
      "description": "Discussed requirements and timeline",
      "duration_minutes": 30,
      "outcome": "positive",
      "created_at": "2024-06-12T14:00:00Z",
      "contact": {
        "name": "John Doe"
      },
      "deal": {
        "title": "Enterprise Software License"
      }
    }
  ]
}
```

### 4.11 Log CRM Activity
**Endpoint**: `POST /api/crm/activity`
**Description**: Log a new activity

**Sample Request Body**:
```json
{
  "contact_id": "contact_123",
  "deal_id": "deal_123",
  "activity_type": "call",
  "title": "Discovery call",
  "description": "Discussed requirements and timeline",
  "duration_minutes": 30,
  "outcome": "positive"
}
```

**Sample Response**:
```json
{
  "status": "success",
  "message": "Activity logged successfully"
}
```

### 4.12 Calculate Lead Score
**Endpoint**: `POST /api/crm/lead-score/{contact_id}`
**Description**: Calculate and update lead score for a contact

**Sample Response**:
```json
{
  "status": "success",
  "message": "Lead score calculated successfully",
  "lead_score": 85
}
```

---

## Error Responses

All APIs follow consistent error response format:

**Sample Error Response** (400 Bad Request):
```json
{
  "status": "error",
  "message": "phone_number is required"
}
```

**Sample Error Response** (500 Internal Server Error):
```json
{
  "status": "error",
  "message": "Internal server error occurred"
}
```

**Sample Error Response** (404 Not Found):
```json
{
  "status": "error",
  "message": "Conversation not found"
}
```

---

## API Summary

**Total APIs**: 25

**Categories**:
- Core Application APIs: 6
- Dashboard & Statistics APIs: 4  
- Conversations APIs: 3
- CRM APIs: 12

**Authentication**: None currently (consider implementing for production)

**CORS**: Configured for Next.js frontend (`localhost:3000`)

**Rate Limiting**: Not implemented (consider adding for production)

All APIs return JSON responses with consistent `status` and `message`/`data` fields.
# 📱 WhatsApp Group Messaging API Documentation

A comprehensive API for managing WhatsApp group messaging, bulk campaigns, and scheduled messages.

## 🚀 **Quick Start**

### **Base URL**
```
http://localhost:5000/api/group-messaging
```

### **Authentication**
The API uses your existing Wasender API token from the `WASENDER_API_TOKEN` environment variable.

---

## 📋 **API Endpoints**

### **1. Health Check**
Check if the group messaging service is running.

```http
GET /api/group-messaging/health
```

**Response:**
```json
{
  "success": true,
  "service": "group_messaging",
  "status": "healthy",
  "timestamp": "2024-01-15T10:30:00.000Z"
}
```

---

### **2. Get All Groups**
Fetch all WhatsApp groups from Wasender API and sync with database.

```http
GET /api/group-messaging/groups
```

**Response:**
```json
{
  "success": true,
  "data": {
    "groups": [
      {
        "id": "uuid-here",
        "group_jid": "123456789-987654321@g.us",
        "name": "My WhatsApp Group",
        "img_url": null,
        "status": "active",
        "member_count": 0,
        "created_at": "2024-01-15T10:00:00Z",
        "updated_at": "2024-01-15T10:00:00Z"
      }
    ],
    "total": 1
  }
}
```

---

### **3. Create New Group**
Create a new WhatsApp group with participants.

```http
POST /api/group-messaging/groups
```

**Request Body:**
```json
{
  "name": "New Test Group",
  "participants": ["+1234567890", "+0987654321"]
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "id": "uuid-here",
    "group_jid": "123456789-987654321@g.us",
    "name": "New Test Group",
    "member_count": 2,
    "created_at": "2024-01-15T10:30:00Z"
  }
}
```

---

### **4. Send Message to Group**
Send a message to a specific WhatsApp group.

```http
POST /api/group-messaging/groups/{group_jid}/send-message
```

**Request Body:**
```json
{
  "message_content": "Hello everyone! 👋",
  "message_type": "text",
  "media_url": null
}
```

**Supported message types:**
- `text` - Plain text message
- `image` - Image with imageUrl
- `video` - Video with videoUrl  
- `document` - Document with documentUrl
- `audio` - Audio/voice note with audioUrl
- `sticker` - Sticker with stickerUrl

**Response:**
```json
{
  "success": true,
  "data": {
    "message_id": "uuid-here",
    "group_jid": "123456789-987654321@g.us",
    "status": "sent",
    "wasender_message_id": "100000",
    "sent_at": "2024-01-15T10:30:00Z",
    "error_message": null
  }
}
```

---

### **5. Bulk Send to Multiple Groups**
Send the same message to multiple groups at once.

```http
POST /api/group-messaging/bulk-send
```

**Request Body:**
```json
{
  "group_jids": [
    "123456789-987654321@g.us",
    "987654321-123456789@g.us"
  ],
  "message_content": "📢 Important announcement for all groups!",
  "message_type": "text",
  "media_url": null,
  "campaign_name": "Monthly Newsletter"
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "campaign_id": "uuid-here",
    "total_groups": 2,
    "successful_sends": 2,
    "failed_sends": 0,
    "results": [
      {
        "group_jid": "123456789-987654321@g.us",
        "status": "sent",
        "wasender_message_id": "100001",
        "error_message": null
      },
      {
        "group_jid": "987654321-123456789@g.us", 
        "status": "sent",
        "wasender_message_id": "100002",
        "error_message": null
      }
    ]
  }
}
```

---

### **6. Schedule Message**
Schedule a message for future delivery with optional recurring pattern.

```http
POST /api/group-messaging/schedule-message
```

**Request Body:**
```json
{
  "message_content": "⏰ This is a scheduled message!",
  "target_groups": ["123456789-987654321@g.us"],
  "scheduled_at": "2024-01-15T15:30:00Z",
  "message_type": "text",
  "media_url": null,
  "recurring_pattern": "daily",
  "recurring_interval": 1
}
```

**Recurring patterns:**
- `daily` - Every N days
- `weekly` - Every N weeks  
- `monthly` - Every N months (approximately 30 days)

**Response:**
```json
{
  "success": true,
  "data": {
    "scheduled_message_id": "uuid-here",
    "scheduled_at": "2024-01-15T15:30:00Z",
    "next_send_at": "2024-01-16T15:30:00Z",
    "target_groups": ["123456789-987654321@g.us"],
    "recurring_pattern": "daily",
    "status": "pending"
  }
}
```

---

### **7. Get Scheduled Messages**
Get all scheduled messages (placeholder endpoint).

```http
GET /api/group-messaging/scheduled-messages?status=pending
```

**Response:**
```json
{
  "success": true,
  "data": {
    "scheduled_messages": [],
    "total": 0
  }
}
```

---

### **8. Cancel Scheduled Message**
Cancel a pending scheduled message.

```http
DELETE /api/group-messaging/scheduled-messages/{message_id}
```

**Response:**
```json
{
  "success": true,
  "message": "Scheduled message cancelled successfully"
}
```

---

### **9. Get Group Message History**
Get message history for a specific group.

```http
GET /api/group-messaging/groups/{group_jid}/messages?limit=50
```

**Response:**
```json
{
  "success": true,
  "data": {
    "group_jid": "123456789-987654321@g.us",
    "messages": [
      {
        "id": "uuid-here",
        "message_content": "Hello everyone! 👋",
        "message_type": "text",
        "status": "sent",
        "sent_at": "2024-01-15T10:30:00Z",
        "error_message": null
      }
    ],
    "total": 1
  }
}
```

---

### **10. Process Scheduled Messages**
Manually trigger processing of pending scheduled messages.

```http
POST /api/group-messaging/process-scheduled
```

**Response:**
```json
{
  "success": true,
  "data": {
    "processed_count": 3,
    "message": "Processed 3 scheduled messages"
  }
}
```

---

## 🛠️ **Testing**

### **Run the Test Suite**
```bash
# Make sure your Flask app is running first
python app.py

# In another terminal, run tests
python test_group_messaging.py

# Or test against a different URL
python test_group_messaging.py http://your-server.com:5000
```

### **Test Individual Endpoints**
```bash
# Health check
curl http://localhost:5000/api/group-messaging/health

# Get groups  
curl http://localhost:5000/api/group-messaging/groups

# Send message
curl -X POST http://localhost:5000/api/group-messaging/groups/GROUP_JID_HERE/send-message \
  -H "Content-Type: application/json" \
  -d '{"message_content": "Test message", "message_type": "text"}'
```

---

## ⚙️ **Configuration**

### **Environment Variables**
```bash
# Required
WASENDER_API_TOKEN=your_wasender_api_token_here

# Optional (defaults shown)
WHATSAPP_API_URL=https://wasenderapi.com/api
DATABASE_PROVIDER=supabase
```

### **Database Tables Created**
- `groups` - WhatsApp group information
- `group_messages` - Message history and status
- `scheduled_messages` - Scheduled and recurring messages
- `group_campaigns` - Bulk messaging campaigns
- `group_campaign_results` - Results of bulk campaigns

---

## 🚨 **Error Handling**

All endpoints return consistent error responses:

```json
{
  "success": false,
  "error": "validation_error",
  "message": "Message content is required"
}
```

**Error Types:**
- `validation_error` (400) - Invalid request data
- `api_error` (500) - Wasender API issues
- `group_messaging_error` (500) - Module-specific errors
- `internal_error` (500) - Unexpected server errors

---

## 📈 **Features**

✅ **Complete Group Management**
- Fetch all groups from Wasender API
- Create new groups with participants
- Send messages to individual groups

✅ **Bulk Messaging**
- Send same message to multiple groups
- Campaign tracking and statistics
- Success/failure reporting per group

✅ **Message Scheduling**
- Schedule messages for future delivery
- Recurring patterns (daily, weekly, monthly)
- Cancel pending scheduled messages

✅ **Database Integration**
- All data stored in Supabase
- Message history and status tracking
- Campaign analytics

✅ **Modular Architecture**
- Standalone module design
- Easy to extract for other projects
- Clean separation of concerns

---

## 🔄 **Next Steps**

1. **Background Scheduler**: Implement APScheduler or Celery for automatic processing
2. **Frontend Integration**: Create UI components for group messaging
3. **Advanced Scheduling**: Add more recurring patterns and timezone support
4. **Media Support**: Full implementation of image, video, document messaging
5. **Analytics Dashboard**: Reporting and analytics for campaigns

---

## 📞 **Support**

For issues or questions about the Group Messaging API:
1. Check the test results: `python test_group_messaging.py`
2. Verify your `WASENDER_API_TOKEN` is valid
3. Ensure your WhatsApp account has groups to test with
4. Check the Flask application logs for detailed error messages 
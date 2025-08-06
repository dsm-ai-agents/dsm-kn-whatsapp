# 🤝 Bot-to-Human Handover System Guide

## Overview

The Bot-to-Human Handover System is an intelligent feature that automatically detects when users want to speak with a human agent and seamlessly transitions conversations from AI bot responses to human agent management. This system includes comprehensive CRM integration for lead management, activity tracking, and customer support workflow automation.

## 🎯 Key Features

### 1. **AI-Powered Intent Detection**
- Uses OpenAI GPT-3.5-turbo to analyze user messages
- Detects handover requests with confidence scoring (0.0 - 1.0)
- Fallback pattern matching for reliability
- Logs all AI decisions for monitoring and improvement

### 2. **Automatic CRM Integration**
- **Lead Creation**: Automatically creates qualified leads
- **Activity Logging**: Records handover requests with full context
- **Contact Updates**: Boosts lead scores and updates status
- **Task Generation**: Creates follow-up tasks for agents (planned)

### 3. **Conversation Management**
- **Bot Disabling**: Automatically turns off bot responses
- **Status Tracking**: Updates conversation status in real-time
- **Message Handling**: Prevents duplicate messages and conflicts

## 🚀 How It Works

### Step 1: User Requests Human Support
User sends a message expressing need for human assistance:
```
Examples:
- "I need to speak with a human"
- "Can I talk to customer service?"
- "I want to speak with an agent"
- "Connect me to a human please"
- "I need urgent help with my order"
```

### Step 2: AI Intent Analysis
The system analyzes the message using AI:
- **AI Model**: GPT-3.5-turbo analyzes intent
- **Confidence Scoring**: Returns confidence level (0.0-1.0)
- **Threshold**: Default 0.7 confidence required for handover
- **Fallback**: Pattern matching if AI fails

### Step 3: CRM Integration Triggers
When handover is detected, the system:

#### 🏢 **Contact Management**
- Gets or creates contact record
- Updates lead status to "qualified"
- Boosts lead score (+25 points)
- Records last contact timestamp

#### 🎯 **Lead Creation**
- Creates new lead with high priority
- Sets lead status to "qualified"
- Records handover trigger message
- Assigns "whatsapp" as lead source

#### 📊 **Activity Logging**
- Logs handover request activity
- Records full message context
- Timestamps the interaction
- Stores metadata for analysis

### Step 4: Bot Deactivation
- Disables bot responses for the conversation
- Updates conversation status
- Ensures no AI interference with human agents

### Step 5: Agent Notification
- Sends admin alert about handover request
- Records webhook event for monitoring
- Updates frontend status indicators

## 📋 Database Schema

### Enhanced Tables

#### `conversations` Table
```sql
ALTER TABLE conversations ADD COLUMN handover_requested BOOLEAN DEFAULT FALSE;
ALTER TABLE conversations ADD COLUMN handover_timestamp TIMESTAMPTZ;
ALTER TABLE conversations ADD COLUMN handover_reason TEXT;
```

#### `lead_details` Table
```sql
ALTER TABLE lead_details ADD COLUMN handover_requested BOOLEAN DEFAULT FALSE;
ALTER TABLE lead_details ADD COLUMN handover_trigger TEXT;
ALTER TABLE lead_details ADD COLUMN handover_timestamp TIMESTAMPTZ;
ALTER TABLE lead_details ADD COLUMN priority VARCHAR(20) DEFAULT 'medium';
```

#### `activities` Table
```sql
ALTER TABLE activities ADD COLUMN metadata JSONB;
```

#### `intent_analysis_log` Table
```sql
CREATE TABLE intent_analysis_log (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    created_at timestamp with time zone DEFAULT now(),
    message_text text,
    handover_needed boolean,
    confidence_score real,
    reason text,
    final_decision boolean,
    model_used text
);
```

## ⚙️ Configuration

### Environment Variables

```bash
# AI Intent Detection Settings
AI_INTENT_CONFIDENCE_THRESHOLD=0.7
AI_INTENT_DETECTION_ENABLED=true
AI_INTENT_MODEL=gpt-3.5-turbo
AI_INTENT_LOGGING_ENABLED=true

# OpenAI API (required for AI intent detection)
OPENAI_API_KEY=your_openai_api_key

# Supabase (required for CRM integration)
SUPABASE_URL=your_supabase_url
SUPABASE_SERVICE_ROLE_KEY=your_service_role_key
```

### Customization Options

#### Confidence Threshold
Adjust the AI confidence threshold:
```python
# In config.py
AI_INTENT_CONFIDENCE_THRESHOLD = 0.7  # 70% confidence required
```

#### Pattern Matching Fallback
Customize fallback patterns in `message_processor.py`:
```python
high_confidence_triggers = [
    "speak to human", "speak to a human", "talk to human", "talk to a human",
    "connect to human", "connect to a human", "connect me to human",
    "i want to speak with human", "human agent", "customer service",
    "live agent", "real person"
]
```

## 🔧 Usage Guide

### For End Users (WhatsApp)

Users can request human support by sending any of these messages:

**Direct Requests:**
- "I want to speak with a human"
- "Can I talk to customer service?"
- "Connect me to an agent"

**Urgent Requests:**
- "I need urgent help with my order"
- "This is urgent, can someone help me?"
- "I need immediate assistance"

**Support Requests:**
- "I have a problem with my delivery"
- "My order is late, I need help"
- "I need to report an issue"

### For Agents (CRM Frontend)

#### Monitoring Handover Requests
1. **Conversations Page**: Shows bot status toggle
2. **Lead Management**: New qualified leads appear automatically
3. **Activity Feed**: Handover activities are logged
4. **Task Dashboard**: Follow-up tasks are created

#### Taking Over Conversations
1. Navigate to Conversations page
2. Look for conversations with "Human Mode" indicator
3. Bot responses are automatically disabled
4. Begin responding directly to the customer

### For Administrators

#### Monitoring System Performance
```sql
-- Check AI intent detection accuracy
SELECT 
    handover_needed,
    AVG(confidence_score) as avg_confidence,
    COUNT(*) as total_requests
FROM intent_analysis_log 
WHERE created_at >= NOW() - INTERVAL '24 hours'
GROUP BY handover_needed;
```

#### Analyzing Handover Triggers
```sql
-- Most common handover triggers
SELECT 
    handover_trigger,
    COUNT(*) as frequency
FROM lead_details 
WHERE handover_requested = true
GROUP BY handover_trigger
ORDER BY frequency DESC
LIMIT 10;
```

## 📊 Monitoring & Analytics

### Key Metrics to Track

1. **Handover Rate**: Percentage of conversations that request human support
2. **AI Accuracy**: Confidence scores and false positive/negative rates
3. **Response Time**: Time from handover to first agent response
4. **Lead Quality**: Conversion rate of handover leads
5. **Customer Satisfaction**: Follow-up surveys on handover experience

### Log Analysis

#### Intent Analysis Logs
```sql
-- Recent AI decisions
SELECT 
    message_text,
    handover_needed,
    confidence_score,
    reason,
    created_at
FROM intent_analysis_log 
ORDER BY created_at DESC 
LIMIT 20;
```

#### CRM Activity Tracking
```sql
-- Handover activities in last 24 hours
SELECT 
    c.phone_number,
    a.title,
    a.description,
    a.created_at
FROM activities a
JOIN contacts c ON a.contact_id = c.id
WHERE a.activity_type = 'support_request'
    AND a.created_at >= NOW() - INTERVAL '24 hours'
ORDER BY a.created_at DESC;
```

## 🛠️ Technical Implementation

### Core Components

#### 1. Message Processor (`message_processor.py`)
- Handles incoming WhatsApp messages
- Triggers handover detection
- Manages CRM integration
- Controls bot enable/disable logic

#### 2. AI Intent Detection
```python
def detect_user_handover_request_ai(message_text: str) -> tuple[bool, float, str]:
    """
    Use AI to detect if user wants to speak with human.
    Returns: (handover_needed, confidence, reason)
    """
```

#### 3. CRM Integration
```python
def handle_user_handover_request(phone_number: str, trigger_message: str) -> tuple[bool, str]:
    """
    Handle handover request with full CRM integration.
    Returns: (success, status_message)
    """
```

### API Endpoints

#### Webhook Endpoint
```http
POST /webhook
Content-Type: application/json

{
  "event": "messages.upsert",
  "data": {
    "messages": [{
      "key": {
        "remoteJid": "1234567890@s.whatsapp.net",
        "fromMe": false,
        "id": "message_id"
      },
      "message": {
        "conversation": "I need to speak with a human"
      }
    }]
  }
}
```

#### Bot Status API
```http
GET /api/bot/status/{phone_number}
POST /api/bot/toggle/{phone_number}
```

## 🚨 Troubleshooting

### Common Issues

#### 1. AI Intent Detection Not Working
**Symptoms**: Handover requests not detected
**Solutions**:
- Check OpenAI API key configuration
- Verify `AI_INTENT_DETECTION_ENABLED=true`
- Review confidence threshold setting
- Check intent analysis logs

#### 2. CRM Integration Failures
**Symptoms**: Leads not created, activities not logged
**Solutions**:
- Verify Supabase connection
- Check database schema migrations
- Review lead creation constraints
- Validate required fields

#### 3. Bot Not Disabling
**Symptoms**: Bot continues responding after handover
**Solutions**:
- Check conversation update queries
- Verify phone number normalization
- Review bot toggle API responses
- Check for duplicate conversation records

#### 4. Frontend Not Updating
**Symptoms**: UI doesn't show handover status
**Solutions**:
- Verify API endpoint responses
- Check frontend WebSocket connections
- Review conversation list queries
- Refresh browser cache

### Debugging Commands

#### Test Handover Detection
```bash
curl -X POST http://localhost:5001/webhook \
  -H "Content-Type: application/json" \
  -d '{
    "event": "messages.upsert",
    "data": {
      "messages": [{
        "key": {
          "remoteJid": "test@s.whatsapp.net",
          "fromMe": false,
          "id": "test_id"
        },
        "message": {
          "conversation": "I need to speak with a human"
        }
      }]
    }
  }'
```

#### Check Bot Status
```bash
curl http://localhost:5001/api/bot/status/1234567890
```

## 🔜 Future Enhancements

### Planned Features

1. **Automatic Task Creation**: Follow-up tasks with SLA tracking
2. **Agent Assignment**: Smart routing to available agents
3. **Escalation Rules**: Automatic escalation for urgent requests
4. **Customer Feedback**: Post-handover satisfaction surveys
5. **Analytics Dashboard**: Real-time handover metrics
6. **Multi-language Support**: Intent detection in multiple languages

### Integration Roadmap

1. **CRM Platforms**: Salesforce, HubSpot integration
2. **Ticketing Systems**: Zendesk, Freshdesk integration
3. **Communication Tools**: Slack, Teams notifications
4. **Analytics**: Google Analytics, Mixpanel tracking

## 📞 Support

For technical support or questions about the handover system:

1. **Documentation**: Check this guide first
2. **Logs**: Review server logs for error details
3. **Database**: Query intent_analysis_log for AI decisions
4. **Testing**: Use the webhook test commands above

## 📝 Changelog

### Version 2.1.0 (Current)
- ✅ AI-powered intent detection with OpenAI
- ✅ Comprehensive CRM integration
- ✅ Activity logging and lead creation
- ✅ Contact scoring and status updates
- ✅ Real-time bot disable/enable
- ✅ Enhanced monitoring and analytics

### Version 2.0.0
- ✅ Basic handover detection with pattern matching
- ✅ Bot disable functionality
- ✅ Frontend integration

### Version 1.0.0
- ✅ Initial WhatsApp bot implementation

---

**Last Updated**: July 28, 2025  
**Version**: 2.1.0  
**Author**: AI Assistant  
**Status**: Production Ready 
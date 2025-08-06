# Flask WhatsApp AI Chatbot Backend - Complete Guide for Students

## Table of Contents
1. [Overview](#overview)
2. [Project Architecture](#project-architecture)
3. [Technology Stack](#technology-stack)
4. [Directory Structure](#directory-structure)
5. [Core Components](#core-components)
6. [API Endpoints](#api-endpoints)
7. [Database Design](#database-design)
8. [Key Features](#key-features)
9. [Setup and Installation](#setup-and-installation)
10. [How It Works](#how-it-works)
11. [Code Examples](#code-examples)
12. [Best Practices](#best-practices)
13. [Troubleshooting](#troubleshooting)

---

## Overview

This is a **Flask-based WhatsApp AI Chatbot Backend** built by Rian Infotech. It's a production-ready system that enables businesses to:

- 🤖 **Automatically respond** to WhatsApp messages using AI (OpenAI GPT)
- 💬 **Manage conversations** with customers through a web dashboard
- 📊 **Track customer data** with integrated CRM functionality
- 📱 **Send bulk messages** for marketing campaigns
- 🔄 **Toggle between bot and human** handling of conversations
- 📈 **Analytics and reporting** for business insights

**What makes this special for students:**
- **Modular architecture** - Easy to understand and extend
- **Real-world application** - Used in actual businesses
- **Modern practices** - Follows industry standards
- **Well-documented** - Every component explained

---

## Project Architecture

### High-Level Architecture
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   WhatsApp      │    │   Flask API     │    │   Supabase      │
│   (WaSender)    │◄──►│   Backend       │◄──►│   Database      │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                              │
                              ▼
                       ┌─────────────────┐
                       │   OpenAI API    │
                       │   (GPT-4)       │
                       └─────────────────┘
```

### Request Flow
1. **WhatsApp message** comes in via webhook
2. **Flask processes** the message
3. **AI generates** response using OpenAI
4. **Response sent** back to WhatsApp
5. **Conversation saved** to database

---

## Technology Stack

### Backend Technologies
- **Flask** - Python web framework (lightweight and flexible)
- **Flask-CORS** - Cross-Origin Resource Sharing for frontend integration
- **Supabase** - PostgreSQL database with real-time features
- **OpenAI API** - GPT-4 for AI responses
- **WaSender API** - WhatsApp messaging service
- **Gunicorn** - Production WSGI server

### Why These Technologies?

1. **Flask** - Simple to learn, perfect for APIs, great for students
2. **Supabase** - Modern alternative to Firebase, SQL-based
3. **OpenAI** - State-of-the-art AI for natural conversations
4. **PostgreSQL** - Robust, scalable database

---

## Directory Structure

```
whatsapp-python-chatbot/
├── app.py                          # Main Flask application entry point
├── requirements.txt                # Python dependencies
├── persona.json                    # Bot personality configuration
├── Procfile                       # Deployment configuration
├── src/                           # Source code (modular structure)
│   ├── api/                       # API route handlers
│   │   ├── api_routes.py          # Main API endpoints
│   │   ├── bot_control_routes.py  # Bot toggle functionality
│   │   └── lead_routes.py         # Lead management APIs
│   ├── config/                    # Configuration management
│   │   ├── config.py              # Environment variables & settings
│   │   └── persona_manager.py     # Bot personality loader
│   ├── core/                      # Core business logic
│   │   ├── conversation_manager.py # Conversation handling
│   │   └── supabase_client.py     # Database operations
│   ├── handlers/                  # Message processing
│   │   ├── ai_handler.py          # OpenAI integration
│   │   ├── message_processor.py   # Incoming message logic
│   │   └── whatsapp_handler.py    # WhatsApp API integration
│   ├── services/                  # Business services
│   │   └── lead_service.py        # Lead management logic
│   └── utils/                     # Utility functions
│       ├── auth.py                # Authentication helpers
│       ├── bulk_messaging.py      # Bulk message handling
│       └── error_handling.py      # Error management
├── docs/                          # Documentation
│   └── database_schema.sql        # Database structure
└── tests/                         # Unit tests
    ├── test_lead_management.py
    └── test_lead_routes.py
```

### Why This Structure?

- **Separation of Concerns** - Each folder has a specific purpose
- **Scalability** - Easy to add new features
- **Maintainability** - Easy to find and fix issues
- **Team Collaboration** - Multiple developers can work simultaneously

---

## Core Components

### 1. Main Application (`app.py`)

**Purpose:** Entry point of the Flask application

**Key Features:**
- Flask app initialization
- CORS configuration for frontend
- Blueprint registration
- Error handling
- Core webhook endpoint

**Code Structure:**
```python
# Flask app setup
app = Flask(__name__)

# CORS for Next.js frontend
CORS(app, origins=["http://localhost:3000"])

# Register API blueprints
app.register_blueprint(api_bp, url_prefix='/api')
app.register_blueprint(bot_control_bp, url_prefix='/api')
app.register_blueprint(lead_bp, url_prefix='/api')

# Main webhook endpoint
@app.route('/webhook', methods=['POST'])
def webhook():
    # Process incoming WhatsApp messages
```

### 2. Configuration (`src/config/`)

**Purpose:** Centralized configuration management

**Files:**
- `config.py` - Environment variables, API keys, settings
- `persona_manager.py` - Bot personality and behavior

**Key Concepts:**
```python
# Environment variables
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
WASENDER_API_TOKEN = os.getenv('WASENDER_API_TOKEN')

# Bot configuration
MAX_LINES_PER_MESSAGE = 3
MESSAGE_DELAY = 2.0
```

### 3. Core Logic (`src/core/`)

#### Supabase Client (`supabase_client.py`)
**Purpose:** Database operations and CRM functionality

**Key Methods:**
- `get_customer_context_by_phone()` - Fetch customer data
- `save_conversation_history()` - Store chat history
- `create_bulk_campaign()` - Bulk messaging campaigns
- `get_dashboard_stats()` - Analytics data

#### Conversation Manager (`conversation_manager.py`)
**Purpose:** Handle conversation state and history

**Key Functions:**
- Load/save conversation history
- Sanitize user IDs
- Manage conversation context

### 4. Message Handlers (`src/handlers/`)

#### AI Handler (`ai_handler.py`)
**Purpose:** OpenAI integration and response generation

**Key Features:**
- Personalized responses using customer context
- Conversation history awareness
- Error handling for AI failures

```python
def generate_ai_response(message_text, conversation_history, customer_context):
    # Create personalized system prompt
    # Call OpenAI API
    # Return AI response
```

#### Message Processor (`message_processor.py`)
**Purpose:** Process incoming WhatsApp messages

**Workflow:**
1. Validate message (not self-sent, not system message)
2. Extract text content
3. Load conversation history
4. Check if bot is enabled
5. Get customer context
6. Generate AI response
7. Send response
8. Save conversation

#### WhatsApp Handler (`whatsapp_handler.py`)
**Purpose:** Send messages via WhatsApp API

**Features:**
- Message splitting for long responses
- Retry logic for failed sends
- Support for different message types (text, image, etc.)

### 5. API Routes (`src/api/`)

#### Main API Routes (`api_routes.py`)
**Purpose:** RESTful API endpoints for the frontend

**Categories:**
- **Dashboard APIs** - Statistics and system status
- **Conversation APIs** - Chat management
- **CRM APIs** - Customer relationship management
- **Campaign APIs** - Bulk messaging

#### Bot Control Routes (`bot_control_routes.py`)
**Purpose:** Toggle bot on/off for specific conversations

**Key Endpoints:**
- `GET /api/bot/status/<conversation_id>` - Get bot status
- `POST /api/bot/toggle/<conversation_id>` - Toggle bot
- `POST /api/bot/toggle-by-phone` - Toggle by phone number

---

## API Endpoints

### Core Endpoints

| Method | Endpoint | Purpose |
|--------|----------|---------|
| `POST` | `/webhook` | Receive WhatsApp messages |
| `GET` | `/health` | System health check |
| `POST` | `/send-message` | Send outbound message |
| `POST` | `/start-conversation` | Initiate AI conversation |
| `POST` | `/send-bulk-message` | Send bulk messages |

### Dashboard APIs

| Method | Endpoint | Purpose |
|--------|----------|---------|
| `GET` | `/api/dashboard-stats` | Get dashboard statistics |
| `GET` | `/api/system-status` | System component status |
| `GET` | `/api/contacts` | List contacts with pagination |
| `GET` | `/api/campaigns` | Recent bulk campaigns |

### Conversation APIs

| Method | Endpoint | Purpose |
|--------|----------|---------|
| `GET` | `/api/conversations` | List all conversations |
| `GET` | `/api/conversation/<id>` | Get conversation details |
| `GET` | `/api/conversation/search` | Search conversations |

### CRM APIs

| Method | Endpoint | Purpose |
|--------|----------|---------|
| `GET` | `/api/crm/contacts` | List CRM contacts |
| `POST` | `/api/crm/contacts` | Create new contact |
| `PUT` | `/api/crm/contact/<id>` | Update contact |
| `GET` | `/api/crm/deals` | List deals |
| `POST` | `/api/crm/deals` | Create new deal |

### Bot Control APIs

| Method | Endpoint | Purpose |
|--------|----------|---------|
| `GET` | `/api/bot/status/<id>` | Get bot status |
| `POST` | `/api/bot/toggle/<id>` | Toggle bot for conversation |
| `POST` | `/api/bot/toggle-by-phone` | Toggle bot by phone number |

---

## Database Design

### Core Tables

#### 1. Contacts Table
```sql
CREATE TABLE contacts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    phone_number VARCHAR(20) UNIQUE NOT NULL,
    name VARCHAR(255),
    email VARCHAR(255),
    company VARCHAR(255),
    position VARCHAR(255),
    lead_status VARCHAR(50) DEFAULT 'new',
    lead_score INTEGER DEFAULT 0,
    tags TEXT[],
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

#### 2. Conversations Table
```sql
CREATE TABLE conversations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    contact_id UUID REFERENCES contacts(id),
    messages JSONB NOT NULL DEFAULT '[]',
    bot_enabled BOOLEAN DEFAULT true,
    last_message_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    unread_count INTEGER DEFAULT 0
);
```

#### 3. Bulk Campaigns Table
```sql
CREATE TABLE bulk_campaigns (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255),
    message_content TEXT NOT NULL,
    total_contacts INTEGER NOT NULL,
    successful_sends INTEGER DEFAULT 0,
    failed_sends INTEGER DEFAULT 0,
    status VARCHAR(50) DEFAULT 'pending'
);
```

### Relationships
- **One-to-Many:** Contact → Conversations
- **One-to-Many:** Campaign → Message Results
- **Many-to-Many:** Contacts ↔ Contact Lists

---

## Key Features

### 1. AI-Powered Responses
- **Personalized responses** based on customer data
- **Context awareness** from conversation history
- **Configurable personality** via persona.json
- **Fallback handling** when AI fails

### 2. CRM Integration
- **Customer profiles** with lead scoring
- **Deal tracking** and pipeline management
- **Task management** for follow-ups
- **Activity logging** for all interactions

### 3. Bot Control System
- **Human takeover** - Disable bot for specific conversations
- **Bulk toggle** - Control multiple conversations
- **Status tracking** - Monitor bot activity
- **Reason logging** - Track why bot was disabled

### 4. Bulk Messaging
- **Campaign management** - Create and track campaigns
- **Contact parsing** - Import from text/CSV
- **Delivery tracking** - Success/failure rates
- **Analytics** - Campaign performance metrics

### 5. Real-time Dashboard
- **Live statistics** - Active conversations, response rates
- **System monitoring** - API status, database health
- **Performance metrics** - Message volume, success rates

---

## Setup and Installation

### Prerequisites
- Python 3.8+
- Supabase account
- OpenAI API key
- WaSender API token

### Step 1: Clone and Install
```bash
git clone <repository>
cd whatsapp-python-chatbot
pip install -r requirements.txt
```

### Step 2: Environment Variables
Create `.env` file:
```env
OPENAI_API_KEY=your_openai_key
WASENDER_API_TOKEN=your_wasender_token
SUPABASE_URL=your_supabase_url
SUPABASE_ANON_KEY=your_supabase_key
```

### Step 3: Database Setup
```bash
# Run the SQL schema in Supabase
psql -f docs/database_schema.sql
```

### Step 4: Configure Bot Persona
Edit `persona.json`:
```json
{
  "name": "Your Bot Name",
  "description": "Bot personality description",
  "base_prompt": "System prompt for AI"
}
```

### Step 5: Run Application
```bash
# Development
python app.py

# Production
gunicorn app:app
```

---

## How It Works

### Message Flow Diagram
```
WhatsApp Message → Webhook → Message Processor → AI Handler → Response → WhatsApp
                     ↓           ↓                ↓           ↓
                 Validation → History → Customer Context → Database
```

### Detailed Process

1. **Message Reception**
   - WhatsApp sends message to `/webhook` endpoint
   - Flask receives and validates the message
   - Extracts sender info and message content

2. **Message Processing**
   - Check if message is from bot (prevent loops)
   - Validate message type (text only)
   - Load conversation history from database

3. **Bot Status Check**
   - Query database for bot_enabled status
   - If disabled, save message but don't respond
   - If enabled, proceed with AI processing

4. **Customer Context Loading**
   - Fetch customer data from CRM
   - Load recent deals, tasks, activities
   - Generate context summary for AI

5. **AI Response Generation**
   - Create personalized system prompt
   - Include conversation history
   - Call OpenAI API with context
   - Handle errors and fallbacks

6. **Response Delivery**
   - Send response via WhatsApp API
   - Handle message splitting for long responses
   - Retry failed sends
   - Log delivery status

7. **Data Persistence**
   - Save conversation to database
   - Update contact last_contacted_at
   - Log activity for CRM tracking

---

## Code Examples

### 1. Processing Incoming Messages
```python
@app.route('/webhook', methods=['POST'])
def webhook():
    webhook_data = request.json
    
    if webhook_data.get('event') == 'messages.upsert':
        message_info = webhook_data['data']['messages']
        success, status = process_incoming_message(message_info)
        
        return jsonify({
            'status': 'success' if success else 'error',
            'message': status
        })
```

### 2. Generating AI Responses
```python
def generate_ai_response(message_text, conversation_history, customer_context):
    if not openai_client:
        return "Sorry, AI is not available right now."
    
    # Create personalized system prompt
    system_prompt = create_personalized_prompt(customer_context)
    
    messages = [
        {"role": "system", "content": system_prompt},
        *conversation_history,
        {"role": "user", "content": message_text}
    ]
    
    response = openai_client.chat.completions.create(
        model="gpt-4o-mini",
        messages=messages,
        max_tokens=1000,
        temperature=0.7
    )
    
    return response.choices[0].message.content
```

### 3. Database Operations
```python
def get_customer_context_by_phone(self, phone_number):
    # Find contact
    contact_result = self.client.table('contacts')\
        .select('*')\
        .eq('phone_number', phone_number)\
        .execute()
    
    if not contact_result.data:
        return None
    
    contact = contact_result.data[0]
    
    # Get related data
    deals = self.get_contact_deals(contact['id'])
    tasks = self.get_contact_tasks(contact['id'])
    
    return {
        'contact': contact,
        'deals': deals,
        'tasks': tasks,
        'context_summary': self.generate_context_summary(contact, deals, tasks)
    }
```

### 4. Bot Toggle Functionality
```python
@bot_control_bp.route('/bot/toggle/<conversation_id>', methods=['POST'])
def toggle_bot_status(conversation_id):
    data = request.json or {}
    new_status = data.get('enabled', None)
    
    # Get current status
    current = get_conversation_bot_status(conversation_id)
    
    # Toggle or set specific status
    if new_status is None:
        new_status = not current['bot_enabled']
    
    # Update database
    update_bot_status(conversation_id, new_status)
    
    return jsonify({
        'status': 'success',
        'new_status': new_status,
        'message': f"Bot {'enabled' if new_status else 'disabled'}"
    })
```

---

## Best Practices

### 1. Code Organization
- **Use Blueprints** for organizing routes
- **Separate concerns** - handlers, services, utils
- **Configuration management** - centralized settings
- **Error handling** - consistent error responses

### 2. Database Best Practices
- **Use indexes** for frequently queried columns
- **Normalize data** to avoid redundancy
- **Use UUIDs** for primary keys
- **Implement soft deletes** for important data

### 3. API Design
- **RESTful conventions** - proper HTTP methods
- **Consistent response format** - status, data, message
- **Pagination** for large datasets
- **Input validation** - sanitize all inputs

### 4. Security
- **Environment variables** for sensitive data
- **Input sanitization** to prevent injection
- **Rate limiting** to prevent abuse
- **CORS configuration** for frontend access

### 5. Performance
- **Database connection pooling**
- **Caching** for frequently accessed data
- **Async operations** where possible
- **Optimize database queries**

---

## Troubleshooting

### Common Issues

#### 1. Webhook Not Receiving Messages
**Symptoms:** No messages coming in
**Solutions:**
- Check WaSender webhook configuration
- Verify HTTPS endpoint is accessible
- Check Flask app is running on correct port
- Validate webhook URL in WaSender dashboard

#### 2. AI Responses Not Working
**Symptoms:** Generic error messages instead of AI responses
**Solutions:**
- Verify OPENAI_API_KEY is set correctly
- Check OpenAI account has sufficient credits
- Review error logs for API failures
- Test with simple messages first

#### 3. Database Connection Issues
**Symptoms:** 503 errors, "Database not connected"
**Solutions:**
- Verify Supabase URL and key
- Check network connectivity
- Review Supabase project status
- Validate database schema is created

#### 4. WhatsApp Messages Not Sending
**Symptoms:** Messages not delivered to WhatsApp
**Solutions:**
- Check WASENDER_API_TOKEN is valid
- Verify WaSender account is active
- Review phone number format
- Check WaSender API rate limits

### Debugging Tips

1. **Enable Debug Logging**
```python
logging.basicConfig(level=logging.DEBUG)
```

2. **Check Environment Variables**
```python
print(f"OpenAI Key: {'✓' if OPENAI_API_KEY else '✗'}")
print(f"WaSender Token: {'✓' if WASENDER_API_TOKEN else '✗'}")
```

3. **Test Individual Components**
```python
# Test database connection
supabase = get_supabase_manager()
print(f"Database connected: {supabase.is_connected()}")

# Test AI
response = generate_ai_response("Hello", [], None)
print(f"AI response: {response}")
```

4. **Monitor Logs**
```bash
tail -f logs/app.log
```

---

## Next Steps for Students

### Beginner Level
1. **Understand the flow** - Trace a message from WhatsApp to response
2. **Modify the persona** - Change bot personality in persona.json
3. **Add simple endpoints** - Create basic GET/POST routes
4. **Explore the database** - Run queries in Supabase

### Intermediate Level
1. **Add new features** - Implement new API endpoints
2. **Customize AI prompts** - Create specialized bot behaviors
3. **Enhance CRM** - Add new contact fields or deal stages
4. **Improve error handling** - Add better error messages

### Advanced Level
1. **Add new integrations** - Connect to other services
2. **Implement caching** - Redis for performance
3. **Add authentication** - JWT or OAuth
4. **Deploy to production** - AWS, Heroku, or Railway

### Learning Resources
- **Flask Documentation:** https://flask.palletsprojects.com/
- **Supabase Docs:** https://supabase.com/docs
- **OpenAI API Guide:** https://platform.openai.com/docs
- **REST API Best Practices:** https://restfulapi.net/

---

## Conclusion

This Flask backend is a **production-ready, scalable WhatsApp AI chatbot system** that demonstrates modern web development practices. It's designed to be:

- **Educational** - Perfect for learning Flask and API development
- **Practical** - Solves real business problems
- **Extensible** - Easy to add new features
- **Professional** - Follows industry standards

By studying this codebase, students will learn:
- Flask web framework
- RESTful API design
- Database integration
- AI API integration
- Real-time messaging
- CRM systems
- Production deployment

**Happy coding! 🚀**

---

*This documentation is maintained by Rian Infotech. For questions or contributions, please refer to the main repository.* 
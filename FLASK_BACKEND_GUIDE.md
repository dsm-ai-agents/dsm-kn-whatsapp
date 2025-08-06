# Flask WhatsApp AI Chatbot Backend - Student Guide

## 📚 Table of Contents
1. [What is This Project?](#what-is-this-project)
2. [Technology Stack](#technology-stack)
3. [Project Architecture](#project-architecture)
4. [Directory Structure](#directory-structure)
5. [Core Components](#core-components)
6. [Database Design](#database-design)
7. [API Endpoints](#api-endpoints)
8. [Setup Guide](#setup-guide)
9. [How It Works](#how-it-works)
10. [Code Examples](#code-examples)

---

## 🤖 What is This Project?

This is a **production-ready WhatsApp AI Chatbot Backend** built with Flask. Think of it as a smart assistant that:

- **Receives WhatsApp messages** from customers
- **Understands what they're asking** using AI (ChatGPT)
- **Responds automatically** with helpful answers
- **Manages customer data** like a CRM system
- **Allows humans to take over** when needed
- **Sends bulk messages** for marketing

### Real-World Use Cases
- **Customer Support:** Answer common questions 24/7
- **Lead Generation:** Qualify potential customers automatically
- **Marketing:** Send promotional messages to thousands of contacts
- **Sales:** Track deals and follow up with prospects

---

## 🛠 Technology Stack

### Backend Technologies
| Technology | Purpose | Why We Use It |
|------------|---------|---------------|
| **Flask** | Web framework | Simple, lightweight, perfect for APIs |
| **Python** | Programming language | Easy to learn, great for AI/ML |
| **Supabase** | Database | Modern PostgreSQL with real-time features |
| **OpenAI API** | AI responses | GPT-4 for natural conversations |
| **WaSender API** | WhatsApp integration | Send/receive WhatsApp messages |

### Supporting Libraries
- **Flask-CORS** - Allow frontend to connect
- **Requests** - Make HTTP API calls
- **python-dotenv** - Manage environment variables
- **Gunicorn** - Production web server

---

## 🏗 Project Architecture

### High-Level Overview
```
📱 WhatsApp ↔️ 🌐 WaSender API ↔️ 🐍 Flask Backend ↔️ 🗄️ Supabase DB
                                        ↕️
                                    🤖 OpenAI API
```

### Request Flow
1. **Customer sends WhatsApp message** → WaSender receives it
2. **WaSender sends webhook** → Flask `/webhook` endpoint
3. **Flask processes message** → Extracts text and sender info
4. **Flask loads customer data** → From Supabase database
5. **Flask calls OpenAI** → Generates AI response with context
6. **Flask sends response** → Back to WhatsApp via WaSender
7. **Flask saves conversation** → To database for history

---

## 📁 Directory Structure

```
whatsapp-python-chatbot/
├── 🚀 app.py                      # Main Flask app (START HERE)
├── 📋 requirements.txt            # Python packages needed
├── 🤖 persona.json               # Bot personality config
├── 📂 src/                       # All source code
│   ├── 📂 api/                   # API endpoints (routes)
│   │   ├── api_routes.py         # Main API endpoints
│   │   ├── bot_control_routes.py # Bot on/off controls
│   │   └── lead_routes.py        # Lead management
│   ├── 📂 config/                # Configuration files
│   │   ├── config.py             # Environment variables
│   │   └── persona_manager.py    # Bot personality loader
│   ├── 📂 core/                  # Core business logic
│   │   ├── conversation_manager.py # Chat history
│   │   └── supabase_client.py    # Database operations
│   ├── 📂 handlers/              # Message processing
│   │   ├── ai_handler.py         # OpenAI integration
│   │   ├── message_processor.py  # Process incoming messages
│   │   └── whatsapp_handler.py   # Send WhatsApp messages
│   └── 📂 utils/                 # Utility functions
│       ├── bulk_messaging.py     # Send to many contacts
│       └── error_handling.py     # Handle errors gracefully
└── 📂 docs/                      # Documentation
    └── database_schema.sql       # Database structure
```

### 🎯 Why This Structure?
- **Modular:** Each folder has one job
- **Scalable:** Easy to add new features
- **Maintainable:** Easy to find and fix bugs
- **Professional:** Industry standard organization

---

## 🧩 Core Components

### 1. Main Application (`app.py`)
**What it does:** The entry point - starts the Flask server and handles basic routes

**Key parts:**
```python
# Create Flask app
app = Flask(__name__)

# Allow frontend to connect (CORS)
CORS(app, origins=["http://localhost:3000"])

# Main webhook - receives WhatsApp messages
@app.route('/webhook', methods=['POST'])
def webhook():
    # Process incoming messages
```

### 2. Configuration (`src/config/`)
**What it does:** Manages all settings and API keys

**Files:**
- `config.py` - Loads environment variables (API keys, database URLs)
- `persona_manager.py` - Loads bot personality from persona.json

### 3. API Routes (`src/api/`)
**What it does:** Defines all the endpoints the frontend can call

**Main categories:**
- **Dashboard APIs** - Get statistics and system status
- **Conversation APIs** - Manage chats and messages
- **CRM APIs** - Handle customer data
- **Bot Control APIs** - Turn bot on/off for specific chats

### 4. Core Logic (`src/core/`)
**What it does:** The main business logic

**Files:**
- `supabase_client.py` - All database operations (save/load data)
- `conversation_manager.py` - Handle chat history and context

### 5. Message Handlers (`src/handlers/`)
**What it does:** Process messages and generate responses

**Files:**
- `message_processor.py` - Main message handling logic
- `ai_handler.py` - Communicate with OpenAI API
- `whatsapp_handler.py` - Send messages via WhatsApp API

---

## 🗄️ Database Design

### Main Tables

#### 1. **contacts** - Customer Information
```sql
CREATE TABLE contacts (
    id UUID PRIMARY KEY,
    phone_number VARCHAR(20) UNIQUE,  -- WhatsApp number
    name VARCHAR(255),                -- Customer name
    email VARCHAR(255),               -- Email address
    company VARCHAR(255),             -- Company name
    lead_status VARCHAR(50),          -- new, qualified, hot, customer
    lead_score INTEGER,               -- 0-100 rating
    created_at TIMESTAMP
);
```

#### 2. **conversations** - Chat History
```sql
CREATE TABLE conversations (
    id UUID PRIMARY KEY,
    contact_id UUID,                  -- Links to contacts table
    messages JSONB,                   -- Array of chat messages
    bot_enabled BOOLEAN,              -- Is bot responding?
    last_message_at TIMESTAMP,        -- When was last message
    unread_count INTEGER              -- How many unread messages
);
```

#### 3. **bulk_campaigns** - Marketing Campaigns
```sql
CREATE TABLE bulk_campaigns (
    id UUID PRIMARY KEY,
    name VARCHAR(255),                -- Campaign name
    message_content TEXT,             -- Message to send
    total_contacts INTEGER,           -- How many contacts
    successful_sends INTEGER,         -- How many sent successfully
    status VARCHAR(50)                -- pending, running, completed
);
```

### 🔗 Relationships
- One contact can have many conversations
- One campaign can have many message results
- Conversations belong to one contact

---

## 🌐 API Endpoints

### Core Endpoints
| Method | Endpoint | What it does |
|--------|----------|--------------|
| `POST` | `/webhook` | Receives WhatsApp messages |
| `GET` | `/health` | Check if system is working |
| `POST` | `/send-message` | Send a message to someone |
| `POST` | `/start-conversation` | Start chatting with AI |

### Dashboard APIs
| Method | Endpoint | What it does |
|--------|----------|--------------|
| `GET` | `/api/dashboard-stats` | Get numbers for dashboard |
| `GET` | `/api/contacts` | List all contacts |
| `GET` | `/api/conversations` | List all chats |
| `GET` | `/api/campaigns` | List marketing campaigns |

### Bot Control APIs
| Method | Endpoint | What it does |
|--------|----------|--------------|
| `GET` | `/api/bot/status/<id>` | Is bot on or off? |
| `POST` | `/api/bot/toggle/<id>` | Turn bot on/off |
| `POST` | `/api/bot/toggle-by-phone` | Turn bot on/off by phone |

### CRM APIs
| Method | Endpoint | What it does |
|--------|----------|--------------|
| `GET` | `/api/crm/contacts` | List CRM contacts |
| `POST` | `/api/crm/contacts` | Add new contact |
| `PUT` | `/api/crm/contact/<id>` | Update contact info |
| `GET` | `/api/crm/deals` | List sales deals |

---

## 🚀 Setup Guide

### Step 1: Prerequisites
You need accounts for:
- **Supabase** (database) - supabase.com
- **OpenAI** (AI) - platform.openai.com  
- **WaSender** (WhatsApp) - wasenderapi.com

### Step 2: Clone and Install
```bash
# Download the code
git clone <repository-url>
cd whatsapp-python-chatbot

# Install Python packages
pip install -r requirements.txt
```

### Step 3: Environment Variables
Create a `.env` file with your API keys:
```env
OPENAI_API_KEY=sk-your-openai-key
WASENDER_API_TOKEN=your-wasender-token
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your-supabase-anon-key
```

### Step 4: Setup Database
1. Go to your Supabase project
2. Run the SQL from `docs/database_schema.sql`
3. This creates all the tables you need

### Step 5: Configure Bot Personality
Edit `persona.json`:
```json
{
  "name": "My Bot",
  "description": "I'm a helpful assistant for your business",
  "base_prompt": "You are a friendly customer service bot..."
}
```

### Step 6: Run the Application
```bash
# Development mode
python app.py

# Production mode  
gunicorn app:app
```

Your Flask API will be running on `http://localhost:5001`

---

## ⚙️ How It Works

### Message Processing Flow

1. **Message Arrives**
   ```
   Customer sends "Hello" → WhatsApp → WaSender → Flask /webhook
   ```

2. **Flask Processes**
   ```python
   # In message_processor.py
   def process_incoming_message(message_info):
       # Extract sender and message text
       sender = message_info['key']['remoteJid']
       text = message_info['message']['conversation']
   ```

3. **Load Customer Data**
   ```python
   # In supabase_client.py
   customer_context = supabase.get_customer_context_by_phone(sender)
   # Returns: {name: "John", company: "ABC Corp", lead_status: "hot"}
   ```

4. **Generate AI Response**
   ```python
   # In ai_handler.py
   ai_response = generate_ai_response(
       message_text=text,
       conversation_history=previous_messages,
       customer_context=customer_data
   )
   ```

5. **Send Response**
   ```python
   # In whatsapp_handler.py
   send_whatsapp_message(sender, ai_response)
   ```

6. **Save to Database**
   ```python
   # Save conversation for history
   save_conversation_history(sender, [
       {'role': 'user', 'content': text},
       {'role': 'assistant', 'content': ai_response}
   ])
   ```

### Bot Toggle System

**Why?** Sometimes humans need to take over conversations

**How it works:**
1. Each conversation has a `bot_enabled` field in database
2. When `bot_enabled = false`, bot doesn't respond
3. Human can chat directly with customer
4. Can toggle back to bot when ready

```python
# Check if bot should respond
if not is_bot_enabled_for_sender(phone_number):
    # Save message but don't respond
    return "Human is handling this conversation"
```

---

## 💻 Code Examples

### Example 1: Simple API Endpoint
```python
@app.route('/api/hello', methods=['GET'])
def hello():
    return jsonify({
        'status': 'success',
        'message': 'Hello from Flask!',
        'timestamp': datetime.now().isoformat()
    })
```

### Example 2: Get Customer Data
```python
@api_bp.route('/api/customer/<phone_number>', methods=['GET'])
def get_customer(phone_number):
    try:
        supabase = get_supabase_manager()
        customer = supabase.get_customer_context_by_phone(phone_number)
        
        if customer:
            return jsonify({
                'status': 'success',
                'data': customer
            })
        else:
            return jsonify({
                'status': 'error',
                'message': 'Customer not found'
            }), 404
            
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500
```

### Example 3: Send WhatsApp Message
```python
@app.route('/api/send-message', methods=['POST'])
def send_message():
    data = request.json
    phone = data.get('phone_number')
    message = data.get('message')
    
    if not phone or not message:
        return jsonify({
            'status': 'error',
            'message': 'Phone number and message required'
        }), 400
    
    success = send_whatsapp_message(phone, message)
    
    if success:
        return jsonify({
            'status': 'success',
            'message': 'Message sent successfully'
        })
    else:
        return jsonify({
            'status': 'error',
            'message': 'Failed to send message'
        }), 500
```

---

## 🎓 Learning Path for Students

### Beginner (Weeks 1-2)
1. **Understand the basics**
   - What is Flask?
   - How do APIs work?
   - What is a webhook?

2. **Explore the code**
   - Start with `app.py`
   - Look at simple endpoints
   - Understand the folder structure

3. **Make small changes**
   - Edit `persona.json`
   - Add a simple GET endpoint
   - Change response messages

### Intermediate (Weeks 3-4)
1. **Database operations**
   - Learn SQL basics
   - Understand the Supabase client
   - Try adding new fields to contacts

2. **API development**
   - Create new endpoints
   - Handle POST requests
   - Add input validation

3. **Integration work**
   - Understand how OpenAI API works
   - See how WhatsApp integration functions
   - Try modifying AI prompts

### Advanced (Weeks 5-6)
1. **New features**
   - Add new database tables
   - Create complex API endpoints
   - Implement new business logic

2. **Performance & scaling**
   - Add caching
   - Optimize database queries
   - Handle errors better

3. **Deployment**
   - Deploy to cloud platforms
   - Set up monitoring
   - Configure production settings

---

## 🔧 Common Issues & Solutions

### Issue 1: "Database not connected"
**Cause:** Wrong Supabase credentials
**Solution:** 
- Check `.env` file has correct SUPABASE_URL and SUPABASE_ANON_KEY
- Verify Supabase project is active

### Issue 2: "OpenAI API error"
**Cause:** Invalid API key or no credits
**Solution:**
- Check OPENAI_API_KEY in `.env`
- Verify OpenAI account has credits
- Check API usage limits

### Issue 3: "WhatsApp messages not sending"
**Cause:** WaSender API issues
**Solution:**
- Verify WASENDER_API_TOKEN
- Check WaSender account status
- Ensure phone number format is correct

### Issue 4: Bot not responding
**Cause:** Bot might be disabled
**Solution:**
- Check bot_enabled status in database
- Use bot toggle API to enable
- Check webhook is receiving messages

---

## 🎯 Next Steps

### What You've Learned
- Flask web framework basics
- RESTful API design
- Database integration with Supabase
- AI API integration with OpenAI
- WhatsApp messaging automation
- Real-world application architecture

### Where to Go Next
1. **Build your own features** - Add new endpoints
2. **Learn React/Next.js** - Build the frontend
3. **Explore other APIs** - Integrate more services
4. **Deploy to production** - Make it live
5. **Add authentication** - Secure your API

### Resources for Further Learning
- **Flask Documentation:** flask.palletsprojects.com
- **Supabase Docs:** supabase.com/docs
- **OpenAI API Guide:** platform.openai.com/docs
- **REST API Tutorial:** restfulapi.net

---

**🚀 Happy coding! This is just the beginning of your journey into building real-world applications!**

*Made with ❤️ by Rian Infotech for students learning Flask and API development* 
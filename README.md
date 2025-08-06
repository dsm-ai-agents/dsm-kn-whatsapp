# 🤖 WhatsApp AI Chatbot - Structured & Refactored

A powerful, modular WhatsApp chatbot powered by OpenAI's GPT models and WaSenderAPI. This project has been completely refactored from a monolithic 1,739-line script into a clean, organized, and maintainable structure.

## 🏗️ Project Structure

```
📁 whatsapp-python-chatbot/
├── 🚀 Entry Points
│   ├── app.py                    # Main structured application
│   └── script.py                 # Legacy redirect (shows refactoring info)
│
├── 📂 src/                       # Organized source code
│   ├── 📂 config/                # Configuration & settings
│   │   ├── __init__.py
│   │   ├── config.py             # Environment & app configuration
│   │   └── persona_manager.py    # Bot personality management
│   │
│   ├── 📂 core/                  # Core business logic
│   │   ├── __init__.py
│   │   ├── conversation_manager.py # Chat history management
│   │   └── supabase_client.py    # Database operations
│   │
│   ├── 📂 handlers/              # Message & API handlers
│   │   ├── __init__.py
│   │   ├── ai_handler.py         # OpenAI integration
│   │   ├── whatsapp_handler.py   # WhatsApp API integration
│   │   └── message_processor.py  # Message processing logic
│   │
│   ├── 📂 api/                   # REST API endpoints
│   │   ├── __init__.py
│   │   └── api_routes.py         # All API routes (dashboard, CRM, etc.)
│   │
│   └── 📂 utils/                 # Utility functions
│       ├── __init__.py
│       └── bulk_messaging.py     # Bulk messaging operations
│
├── 📂 docs/                      # Documentation
│   ├── REFACTORING_GUIDE.md      # Complete refactoring guide
│   └── database_schema.sql       # Database schema
│
├── 📂 backup/                    # Backup files
│   ├── script_original_backup.py # Original 1,739-line monolith
│   └── migrate_to_supabase.py    # Database migration script
│
├── 📂 static/                    # Web assets (CSS, JS, images)
├── 📂 templates/                 # HTML templates
├── 📂 conversations/             # Local conversation backups
│
├── 📄 Configuration Files
│   ├── .env                      # Environment variables
│   ├── persona.json              # Bot personality configuration
│   ├── requirements.txt          # Python dependencies
│   └── README.md                 # This file
```

## ✨ Key Features

- **🤖 AI-Powered Responses**: OpenAI GPT integration with customizable personas
- **💬 WhatsApp Integration**: Full WhatsApp API support via WaSenderAPI
- **📊 CRM System**: Contact management, deals, tasks, and lead scoring
- **📈 Dashboard**: Real-time statistics and conversation management
- **🔄 Bulk Messaging**: Send messages to multiple contacts with campaign tracking
- **💾 Database**: Supabase integration with local JSON fallback
- **🏗️ Modular Architecture**: Clean, maintainable, and scalable code structure

## 🚀 Quick Start

### 1. Installation

```bash
# Clone the repository
git clone <your-repo-url>
cd whatsapp-python-chatbot

# Install dependencies
pip install -r requirements.txt
```

### 2. Configuration

Create a `.env` file with your API keys:

```env
# OpenAI Configuration
OPENAI_API_KEY=your_openai_api_key_here

# WaSender API Configuration
WASENDER_API_TOKEN=your_wasender_token_here

# Supabase Configuration (optional)
SUPABASE_URL=your_supabase_url_here
SUPABASE_KEY=your_supabase_key_here
```

### 3. Bot Personality

Customize your bot in `persona.json`:

```json
{
  "name": "Rian Assistant",
  "description": "I am a helpful AI assistant from Rian Infotech...",
  "base_prompt": "You are a helpful and concise AI assistant..."
}
```

### 4. Run the Application

```bash
# Run the main structured application
python3 app.py

# Or use the legacy redirect (shows structure info)
python3 script.py
```

The application will start on `http://localhost:5001`

## 📚 Module Documentation

### 🔧 Configuration (`src/config/`)

- **`config.py`**: Centralized configuration management
- **`persona_manager.py`**: Bot personality loading and management

### 🏛️ Core (`src/core/`)

- **`conversation_manager.py`**: Chat history management with Supabase integration
- **`supabase_client.py`**: Database operations and CRM functionality

### 🎯 Handlers (`src/handlers/`)

- **`ai_handler.py`**: OpenAI API integration and response generation
- **`whatsapp_handler.py`**: WhatsApp message sending via WaSenderAPI
- **`message_processor.py`**: Incoming message processing and validation

### 🌐 API (`src/api/`)

- **`api_routes.py`**: All REST API endpoints for dashboard, CRM, and campaigns

### 🛠️ Utilities (`src/utils/`)

- **`bulk_messaging.py`**: Bulk messaging operations with campaign tracking

## 🔗 API Endpoints

### Core Endpoints
- `GET /health` - Health check
- `POST /webhook` - WhatsApp webhook handler
- `POST /send-message` - Send individual messages
- `POST /start-conversation` - Start AI conversations
- `POST /send-bulk-message` - Send bulk messages

### Dashboard & Stats
- `GET /api/dashboard-stats` - Dashboard statistics
- `GET /api/contacts` - Contact list with pagination
- `GET /api/campaigns` - Recent campaigns
- `GET /api/conversations` - Conversation list

### CRM Endpoints
- `GET /api/crm/contacts` - CRM contact management
- `GET /api/crm/deals` - Deal management
- `GET /api/crm/tasks` - Task management
- `POST /api/crm/activity` - Log activities

## 🔄 Migration from Legacy

If you're upgrading from the original monolithic version:

1. **Backup**: Your original script is saved as `backup/script_original_backup.py`
2. **Configuration**: Update imports in any custom code to use the new structure
3. **Database**: Run migration scripts if needed
4. **Testing**: Test all functionality with the new modular structure

## 🏆 Benefits of Refactoring

### Before (Monolithic)
- ❌ 1,739 lines in single file
- ❌ Hard to maintain and debug
- ❌ Difficult to add new features
- ❌ No clear separation of concerns

### After (Structured)
- ✅ 8 focused modules (~200 lines each)
- ✅ Clear separation of concerns
- ✅ Easy to maintain and extend
- ✅ Modular and testable
- ✅ Professional project structure

## 🛠️ Development

### Adding New Features

1. **Handlers**: Add new message handlers in `src/handlers/`
2. **API Endpoints**: Add new routes in `src/api/api_routes.py`
3. **Core Logic**: Add business logic in `src/core/`
4. **Configuration**: Add new config options in `src/config/config.py`

### Testing

```bash
# Test individual modules
python3 -m src.handlers.ai_handler
python3 -m src.core.conversation_manager

# Test API endpoints
curl http://localhost:5001/health
```

## 📖 Documentation

- **`docs/REFACTORING_GUIDE.md`**: Complete refactoring documentation
- **`docs/database_schema.sql`**: Database schema and setup
- **Module docstrings**: Each module has comprehensive documentation

## 🤝 Contributing

1. Follow the modular structure
2. Add proper docstrings and type hints
3. Update documentation for new features
4. Test thoroughly before submitting

## 📄 License

This project is licensed under the MIT License.

## 🆘 Support

For support and questions:
- Check the documentation in `docs/`
- Review module docstrings
- Create an issue for bugs or feature requests

---

**Built with ❤️ by Rian Infotech**

*From a 1,739-line monolith to a clean, modular, maintainable system! 🚀*

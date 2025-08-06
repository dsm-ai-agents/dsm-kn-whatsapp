# 🚀 WhatsApp AI Chatbot - API Only Backend

**Version:** 2.1 (API Only)  
**Frontend:** Separate Next.js Application  
**Backend:** Flask API Server

---

## 🎯 Overview

This is now a **pure API backend** for the WhatsApp AI Chatbot system. The frontend has been removed to allow for a separate **Next.js frontend** implementation.

### ✅ What's Included:
- 🔌 **Complete REST API** (25+ endpoints)
- 🤖 **WhatsApp AI Integration** (OpenAI + WaSender)
- 💾 **Database Integration** (Supabase)
- 📊 **CRM System** (Contacts, Deals, Tasks)
- 📈 **Campaign Management**
- 🚀 **Production Ready** (Gunicorn + Railway)

### ❌ What's Removed:
- 🎨 HTML Templates (moved to frontend_backup/)
- 📁 Static Files (CSS, JS, Images)
- 🖥️ Frontend Routes (replaced with API info endpoint)

---

## 🚀 Quick Start

### 1. Installation
```bash
pip install -r requirements.txt
```

### 2. Environment Variables
```bash
OPENAI_API_KEY=your_openai_key
WASENDER_API_TOKEN=your_wasender_token
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_key
```

### 3. Run API Server
```bash
# Development
python app.py

# Production (Railway)
gunicorn app:app --bind 0.0.0.0:$PORT
```

---

## 🔗 API Endpoints

### Core Endpoints
```
GET  /                    # API info and available endpoints
GET  /health              # Health check with component status
POST /webhook             # WhatsApp webhook handler
POST /send-message        # Send individual messages
POST /start-conversation  # Start AI conversations
POST /send-bulk-message   # Send bulk campaigns
```

### Dashboard & Stats
```
GET  /api/dashboard-stats # Dashboard statistics
GET  /api/contacts        # Contact list (paginated)
GET  /api/campaigns       # Campaign list
GET  /api/conversations   # Conversation list
```

### CRM System
```
GET  /api/crm/contacts    # CRM contacts with lead scoring
GET  /api/crm/deals       # Sales deals/opportunities
GET  /api/crm/tasks       # Follow-up tasks
POST /api/crm/deals       # Create new deals
POST /api/crm/tasks       # Create new tasks
PUT  /api/crm/contact/:id # Update contact info
```

---

## 📚 Complete Documentation

- **📖 Full API Docs**: `API_DOCUMENTATION.md` (70+ pages)
- **⚡ Quick Reference**: `API_QUICK_REFERENCE.md` (Designer friendly)
- **🚀 Deployment Guide**: `RAILWAY_DEPLOYMENT.md`

---

## 🎨 Next.js Frontend Integration

### API Service Example
```javascript
// api/whatsapp.js
const API_BASE = process.env.NEXT_PUBLIC_API_URL;

export const whatsappAPI = {
  // Send message
  sendMessage: async (phoneNumber, message) => {
    const response = await fetch(`${API_BASE}/send-message`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ phone_number: phoneNumber, message })
    });
    return response.json();
  },

  // Get conversations
  getConversations: async (limit = 20, offset = 0) => {
    const response = await fetch(
      `${API_BASE}/api/conversations?limit=${limit}&offset=${offset}`
    );
    return response.json();
  },

  // Get dashboard stats
  getDashboardStats: async () => {
    const response = await fetch(`${API_BASE}/api/dashboard-stats`);
    return response.json();
  }
};
```

### Environment Variables (.env.local)
```bash
NEXT_PUBLIC_API_URL=https://your-railway-app.railway.app
# Or for development:
NEXT_PUBLIC_API_URL=http://localhost:5001
```

---

## 🔧 Key Changes Made

### 1. Removed Frontend Routes
- ❌ `GET /` (dashboard) → ✅ `GET /` (API info)
- ❌ `GET /favicon.ico` → Removed
- ❌ Template rendering → Pure JSON responses

### 2. Moved Frontend Files
- `static/` → `frontend_backup/static/`
- `templates/` → `frontend_backup/templates/`
- Updated `.gitignore` to exclude frontend files

### 3. Updated Flask Configuration
- Removed `render_template` import
- Removed `app.static_folder` configuration
- Added API info endpoint at root

---

## 🌐 CORS Setup (for Next.js)

Add CORS support for your Next.js frontend:

```bash
pip install flask-cors
```

```python
# Add to app.py
from flask_cors import CORS

app = Flask(__name__)
CORS(app, origins=["http://localhost:3000", "https://your-nextjs-domain.com"])
```

---

## 🧪 Testing the API

### Health Check
```bash
curl https://your-app.railway.app/health
```

### Send Message
```bash
curl -X POST https://your-app.railway.app/send-message \
  -H "Content-Type: application/json" \
  -d '{"phone_number": "919876543210", "message": "Hello from API!"}'
```

### Get Dashboard Stats
```bash
curl https://your-app.railway.app/api/dashboard-stats
```

---

## 📋 Production Deployment

1. **Railway Deployment**: Already configured with Procfile
2. **Environment Variables**: Set in Railway dashboard
3. **Domain**: Use Railway-provided domain or custom domain
4. **SSL**: Automatically handled by Railway

---

## 💡 Benefits of API-Only Architecture

- ✅ **Separation of Concerns**: Backend focused on business logic
- ✅ **Scalability**: Frontend and backend can scale independently  
- ✅ **Technology Freedom**: Use any frontend framework
- ✅ **Mobile Ready**: Same API can power mobile apps
- ✅ **Better Performance**: Optimized API responses
- ✅ **Easier Testing**: API endpoints can be tested independently

---

**Ready for Next.js integration!** 🎉

Your Flask backend is now a pure API server, perfect for connecting with a modern Next.js frontend. 
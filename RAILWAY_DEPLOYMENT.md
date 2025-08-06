# 🚀 Railway Deployment Guide

## Quick Fix for "No start command found" Error

The deployment error you encountered is because Railway didn't know how to start your Flask application. I've fixed this by adding:

### ✅ Files Added/Updated:

1. **`Procfile`** - Tells Railway how to start the app
2. **`railway.json`** - Railway-specific configuration 
3. **Updated `requirements.txt`** - Added gunicorn for production
4. **Updated `app.py`** - Better production configuration

---

## 🛠️ Environment Variables Setup

In your Railway project dashboard, add these environment variables:

### Required Variables:
```
OPENAI_API_KEY=your_openai_api_key_here
WASENDER_API_TOKEN=your_wasender_token_here
```

### Optional Variables:
```
SUPABASE_URL=your_supabase_url_here
SUPABASE_KEY=your_supabase_anon_key_here
FLASK_ENV=production
BOT_NAME=Rian Assistant
```

---

## 🚀 Deployment Steps:

1. **Push these changes** to your repository
2. **Add environment variables** in Railway dashboard
3. **Redeploy** your service
4. **Test the health endpoint**: `https://your-app.railway.app/health`

---

## 🔧 What Was Fixed:

### 1. Procfile Created
```
web: gunicorn app:app --bind 0.0.0.0:$PORT --workers 4 --timeout 120
```

### 2. Railway Configuration
```json
{
  "deploy": {
    "startCommand": "gunicorn app:app --bind 0.0.0.0:$PORT --workers 4 --timeout 120",
    "healthcheckPath": "/health"
  }
}
```

### 3. Production Dependencies
Added `gunicorn` to requirements.txt for proper WSGI server.

### 4. Port Configuration
Updated app.py to use Railway's `$PORT` environment variable.

---

## 🧪 Testing After Deployment:

1. **Health Check**: `GET https://your-app.railway.app/health`
2. **Dashboard**: `GET https://your-app.railway.app/`
3. **API Test**: `GET https://your-app.railway.app/api/dashboard-stats`

---

## 🚨 Common Issues & Solutions:

### Issue: "Application failed to respond"
- **Solution**: Check environment variables are set
- **Check**: Railway logs for detailed error messages

### Issue: "502 Bad Gateway"
- **Solution**: Ensure gunicorn is starting properly
- **Check**: Make sure PORT environment variable is available

### Issue: "Internal Server Error"
- **Solution**: Check that all required API keys are configured
- **Check**: OpenAI and WaSender API credentials

---

## 📋 Environment Variables Checklist:

- [ ] `OPENAI_API_KEY` - Your OpenAI API key
- [ ] `WASENDER_API_TOKEN` - WaSender API token
- [ ] `SUPABASE_URL` - (Optional) Supabase project URL
- [ ] `SUPABASE_KEY` - (Optional) Supabase anon key

---

## 🔗 Useful Links:

- **Railway Dashboard**: https://railway.app/dashboard
- **Health Check**: https://your-app.railway.app/health
- **API Documentation**: Check API_DOCUMENTATION.md

---

**Ready to deploy!** 🎉 Push these changes and redeploy your Railway service. 
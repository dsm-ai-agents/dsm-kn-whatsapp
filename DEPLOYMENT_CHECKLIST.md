# Lead Management System - Deployment Checklist

## ✅ Backend Integration Status

### **Completed:**
- [x] Lead management database schema created in Supabase
- [x] LeadService implemented with all CRUD operations
- [x] Lead API routes created and tested
- [x] Blueprint registered in Flask app
- [x] Authentication and error handling decorators added
- [x] All tests passing
- [x] Frontend API proxy routes already exist

### **API Endpoints Available:**
```
GET  /api/leads                     - List leads with pagination/filters
POST /api/leads                     - Create new lead
GET  /api/leads/:id                 - Get lead details
PUT  /api/leads/:id                 - Update lead
GET  /api/leads/:id/interactions    - Get lead interactions
POST /api/leads/:id/interactions    - Add lead interaction
GET  /api/leads/:id/requirements    - Get lead requirements
POST /api/leads/:id/requirements    - Add lead requirement
GET  /api/leads/analytics           - Lead analytics/metrics
```

## 🚀 Deployment Steps

### **1. Environment Variables**
Ensure these are set on your server:
```bash
SUPABASE_URL=your_supabase_url
SUPABASE_ANON_KEY=your_supabase_anon_key
OPENAI_API_KEY=your_openai_key
WASENDER_API_KEY=your_wasender_key
WASENDER_INSTANCE_ID=your_instance_id
FRONTEND_URL=your_frontend_domain
```

### **2. Dependencies**
All required packages are in requirements.txt:
- Flask and extensions
- Supabase client
- OpenAI client
- Other utilities

### **3. Database**
- ✅ Supabase schema already created
- ✅ Tables: lead_details, lead_interactions, lead_requirements, lead_documents
- ✅ All relationships and constraints in place

### **4. Frontend Integration**
- ✅ Frontend already has lead management pages
- ✅ API proxy routes already configured
- ✅ Components ready to use the backend APIs

## 🔧 Server Deployment Commands

### **Option 1: Direct Deployment**
```bash
# 1. Upload your code to server
scp -r whatsapp-python-chatbot/ user@your-server:/path/to/app/

# 2. Install dependencies
pip install -r requirements.txt

# 3. Set environment variables
export SUPABASE_URL="your_url"
export SUPABASE_ANON_KEY="your_key"
# ... other env vars

# 4. Start the Flask app
python app.py
# or with gunicorn:
gunicorn -w 4 -b 0.0.0.0:5001 app:app
```

### **Option 2: Docker Deployment**
```bash
# Create Dockerfile if needed
# Build and run container
docker build -t whatsapp-crm .
docker run -p 5001:5001 --env-file .env whatsapp-crm
```

### **Option 3: PM2 (Recommended for production)**
```bash
# Install PM2
npm install -g pm2

# Create ecosystem file
pm2 start ecosystem.config.js

# Or direct start
pm2 start app.py --name whatsapp-crm --interpreter python3
```

## 🧪 Post-Deployment Testing

### **1. Health Check**
```bash
curl http://your-server:5001/health
```

### **2. Test Lead APIs**
```bash
# List leads
curl http://your-server:5001/api/leads

# Create lead (requires contact_id)
curl -X POST http://your-server:5001/api/leads \
  -H "Content-Type: application/json" \
  -d '{"contact_id":"uuid","lead_source":"website","company_name":"Test Co"}'
```

### **3. Frontend Integration**
- Update BACKEND_URL in frontend .env to point to your server
- Test lead management pages work correctly
- Verify data flows from frontend → backend → database

## 📋 Frontend Configuration

### **Update Frontend Environment**
```bash
# In frontend/.env.local
BACKEND_URL=http://your-server:5001
# or
BACKEND_URL=https://your-domain.com
```

### **Verify Frontend API Routes**
The frontend already has these proxy routes:
- `/api/leads/*` → Backend `/api/leads/*`
- All CRUD operations supported
- Error handling in place

## 🔍 Monitoring & Logs

### **Check Logs**
```bash
# Flask app logs
tail -f logs/app.log

# PM2 logs
pm2 logs whatsapp-crm

# System logs
journalctl -u your-service -f
```

### **Monitor Performance**
- Database query performance
- API response times
- Memory usage
- Error rates

## 🚨 Troubleshooting

### **Common Issues:**
1. **Database Connection**: Check Supabase credentials
2. **CORS Errors**: Verify FRONTEND_URL is set correctly
3. **Import Errors**: Ensure all dependencies installed
4. **Permission Errors**: Check file permissions and user access

### **Debug Commands:**
```bash
# Test database connection
python3 -c "from src.core.supabase_client import get_supabase_manager; print(get_supabase_manager().is_connected())"

# Test lead service
python3 -c "from src.services.lead_service import LeadService; print('LeadService loaded successfully')"

# Check routes
python3 -c "from app import app; [print(rule) for rule in app.url_map.iter_rules() if 'leads' in str(rule)]"
```

## ✅ Success Criteria

- [ ] Backend starts without errors
- [ ] Health check returns 200
- [ ] Lead APIs respond correctly
- [ ] Frontend can connect to backend
- [ ] Lead management pages work
- [ ] Data persists in Supabase
- [ ] WhatsApp integration still works
- [ ] No CORS errors in browser

## 📞 Support

If you encounter issues:
1. Check the logs first
2. Verify environment variables
3. Test database connectivity
4. Ensure all dependencies are installed
5. Check firewall/port settings

**Your lead management system is ready for deployment! 🚀** 
# 📅 WhatsApp Message Scheduling Guide

## 🎯 Overview

The WhatsApp AI Chatbot supports **automatic message scheduling** with multiple deployment options to fit different production environments.

## 🔧 Scheduling Options

### 1. **Automatic Background Scheduler (APScheduler)**
- ✅ **Best for**: Single-worker deployments, development, small-scale production
- ✅ **How it works**: Built-in background job runs every minute to process scheduled messages
- ✅ **Setup**: Automatic - no configuration needed

**Requirements:**
```bash
pip install APScheduler>=3.10.0
```

**Configuration:**
```env
# Optional: Disable if needed
GROUP_MSG_SCHEDULER_ENABLED=true
```

### 2. **Manual API Processing**
- ✅ **Best for**: Multi-worker deployments, serverless, external cron management
- ✅ **How it works**: External service calls API endpoint to process messages
- ✅ **Setup**: Configure external cron job

**API Endpoint:**
```bash
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

### 3. **External Cron Job Setup**

#### **Option A: GitHub Actions (Free)**
Create `.github/workflows/scheduled-messages.yml`:

```yaml
name: Process Scheduled Messages
on:
  schedule:
    - cron: '* * * * *'  # Every minute

jobs:
  process-messages:
    runs-on: ubuntu-latest
    steps:
      - name: Process Scheduled Messages
        run: |
          curl -X POST "${{ secrets.API_URL }}/api/group-messaging/process-scheduled"
```

#### **Option B: External Cron Service**
Use services like:
- **EasyCron**: `https://www.easycron.com/`
- **Cron-Job.org**: `https://cron-job.org/`
- **SetCronJob**: `https://www.setcronjob.com/`

**Cron Configuration:**
```bash
# Run every minute
* * * * * curl -X POST "https://your-api.railway.app/api/group-messaging/process-scheduled"
```

#### **Option C: Server-side Cron**
If you have server access:

```bash
# Edit crontab
crontab -e

# Add this line
* * * * * curl -X POST "https://your-api.railway.app/api/group-messaging/process-scheduled" >/dev/null 2>&1
```

### 4. **Railway Deployment Configuration**

#### **Single Worker (Recommended for Scheduler)**
**railway.json:**
```json
{
  "deploy": {
    "startCommand": "gunicorn app:app --bind 0.0.0.0:$PORT --workers 1 --timeout 120"
  }
}
```

#### **Multiple Workers (Use External Cron)**
**railway.json:**
```json
{
  "deploy": {
    "startCommand": "gunicorn app:app --bind 0.0.0.0:$PORT --workers 4 --timeout 120"
  }
}
```

## 🚀 Production Deployment Steps

### **Step 1: Choose Your Strategy**

**For Railway with 1 Worker:**
```bash
# In railway.json - Single worker enables background scheduler
"startCommand": "gunicorn app:app --bind 0.0.0.0:$PORT --workers 1 --timeout 120"
```

**For Railway with Multiple Workers:**
```bash
# In railway.json - Multiple workers require external cron
"startCommand": "gunicorn app:app --bind 0.0.0.0:$PORT --workers 4 --timeout 120"
```

### **Step 2: Deploy to Railway**
```bash
git add -A
git commit -m "Configure scheduler for production"
git push origin main
```

### **Step 3: Verify Deployment**
```bash
# Check health status
curl https://your-app.railway.app/api/group-messaging/health

# Expected response:
{
  "success": true,
  "service": "group_messaging", 
  "status": "healthy",
  "scheduler_status": "available", // or "not_installed"
  "manual_processing": "/api/group-messaging/process-scheduled"
}
```

### **Step 4: Test Scheduling**
```bash
# Create test scheduled message
curl -X POST "https://your-app.railway.app/api/group-messaging/schedule-message" \
  -H "Content-Type: application/json" \
  -d '{
    "message_content": "Test scheduled message",
    "target_groups": ["your-group@g.us"],
    "scheduled_at": "2024-01-01T15:05:00Z"
  }'

# Check if processed (wait 1-2 minutes)
curl https://your-app.railway.app/api/group-messaging/scheduled-messages
```

## 🔍 Troubleshooting

### **Background Scheduler Not Starting**
```bash
# Check logs for:
"⚠️ Multiple workers detected - skipping background scheduler"
```
**Solution**: Use single worker or set up external cron

### **APScheduler Import Error**
```bash
# Check logs for:
"⚠️ APScheduler not available"
```
**Solution**: Ensure `APScheduler>=3.10.0` in requirements.txt

### **Messages Not Processing**
1. **Check scheduler status:**
   ```bash
   curl https://your-app.railway.app/api/group-messaging/health
   ```

2. **Manual processing test:**
   ```bash
   curl -X POST https://your-app.railway.app/api/group-messaging/process-scheduled
   ```

3. **Check message status:**
   ```bash
   curl https://your-app.railway.app/api/group-messaging/scheduled-messages
   ```

## 📊 Monitoring & Logs

### **Production Monitoring**
- Monitor `/api/group-messaging/health` endpoint
- Set up alerts for processing failures
- Check Railway logs for scheduler messages:
  - `✅ Processed X scheduled messages`
  - `❌ Error processing scheduled messages`

### **Log Messages to Watch**
```
🚀 APScheduler background job started    # Scheduler working
⚠️ Multiple workers detected            # Need external cron  
📝 Scheduler disabled in configuration   # Explicitly disabled
❌ Failed to setup scheduler             # Setup error
```

## 🎯 Recommended Production Setup

**For Small-Medium Apps (< 1000 messages/day):**
- ✅ Single Railway worker with background scheduler
- ✅ Simple, no external dependencies

**For Large Apps (> 1000 messages/day):**
- ✅ Multiple Railway workers for performance
- ✅ External cron job for reliability
- ✅ Better resource utilization

## 📝 Environment Variables

```env
# Optional scheduler configuration
GROUP_MSG_SCHEDULER_ENABLED=true
GROUP_MSG_CHECK_INTERVAL=60        # seconds
GROUP_MSG_TIMEZONE=UTC
GROUP_MSG_MAX_SCHEDULED=1000

# Required for WhatsApp functionality
WASENDER_API_TOKEN=your_token
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_key
```

---

## 🚀 Quick Start Production

**Option 1: Single Worker (Auto Scheduler)**
```bash
# 1. Deploy with single worker
echo '{"deploy":{"startCommand":"gunicorn app:app --bind 0.0.0.0:$PORT --workers 1"}}' > railway.json

# 2. Deploy
git add . && git commit -m "Single worker deployment" && git push

# 3. Test
curl https://your-app.railway.app/api/group-messaging/health
```

**Option 2: Multi Worker + External Cron**
```bash
# 1. Deploy with multiple workers  
echo '{"deploy":{"startCommand":"gunicorn app:app --bind 0.0.0.0:$PORT --workers 4"}}' > railway.json

# 2. Deploy
git add . && git commit -m "Multi worker deployment" && git push

# 3. Set up cron at https://cron-job.org/:
# URL: https://your-app.railway.app/api/group-messaging/process-scheduled
# Interval: Every 1 minute
```

Both options work perfectly! Choose based on your scale and preferences. 🎉 
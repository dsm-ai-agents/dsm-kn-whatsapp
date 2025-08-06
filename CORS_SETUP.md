# 🌐 CORS Configuration Guide

## ✅ CORS Setup Complete!

Your Flask backend now has proper CORS (Cross-Origin Resource Sharing) configuration to work seamlessly with your Next.js frontend.

---

## 🔧 What We Added:

### 1. Flask-CORS Package
```bash
pip install flask-cors
```

### 2. CORS Configuration in app.py
```python
from flask_cors import CORS

# Configure CORS for Next.js frontend
allowed_origins = [
    "http://localhost:3000",  # Next.js development
    "http://127.0.0.1:3000",  # Alternative localhost
    "https://localhost:3000", # HTTPS dev (if using)
]

# Add production domain from environment variable
production_domain = os.environ.get('FRONTEND_URL')
if production_domain:
    allowed_origins.append(production_domain)

CORS(app, 
     origins=allowed_origins,
     methods=['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'],
     allow_headers=['Content-Type', 'Authorization'],
     supports_credentials=True)
```

---

## 🧪 CORS Testing Results:

### ✅ Preflight Request (OPTIONS)
```http
curl -X OPTIONS -H "Origin: http://localhost:3000" http://localhost:5001/send-message

HTTP/1.1 200 OK
Access-Control-Allow-Origin: http://localhost:3000
Access-Control-Allow-Credentials: true
Access-Control-Allow-Headers: Content-Type
Access-Control-Allow-Methods: DELETE, GET, OPTIONS, POST, PUT
```

### ✅ Regular Request
```http
curl -H "Origin: http://localhost:3000" http://localhost:5001/health

HTTP/1.1 200 OK
Access-Control-Allow-Origin: http://localhost:3000
Access-Control-Allow-Credentials: true
```

---

## 🚀 Environment Variables

### Development (.env.local in Next.js)
```bash
NEXT_PUBLIC_API_URL=http://localhost:5001
```

### Production (Railway Dashboard)
```bash
FRONTEND_URL=https://your-nextjs-app.vercel.app
# or
FRONTEND_URL=https://your-custom-domain.com
```

---

## 📝 Next.js Integration Examples

### 1. API Service (lib/api.js)
```javascript
const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:5001';

export const api = {
  // Send WhatsApp message
  sendMessage: async (phoneNumber, message) => {
    const response = await fetch(`${API_BASE}/send-message`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      credentials: 'include', // Important for CORS with credentials
      body: JSON.stringify({
        phone_number: phoneNumber,
        message: message
      })
    });
    
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    
    return response.json();
  },

  // Get dashboard stats
  getDashboardStats: async () => {
    const response = await fetch(`${API_BASE}/api/dashboard-stats`, {
      credentials: 'include'
    });
    return response.json();
  },

  // Get conversations
  getConversations: async (limit = 20, offset = 0) => {
    const response = await fetch(
      `${API_BASE}/api/conversations?limit=${limit}&offset=${offset}`,
      { credentials: 'include' }
    );
    return response.json();
  }
};
```

### 2. React Hook (hooks/useWhatsApp.js)
```javascript
import { useState, useEffect } from 'react';
import { api } from '../lib/api';

export const useWhatsApp = () => {
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const sendMessage = async (phoneNumber, message) => {
    try {
      setLoading(true);
      const result = await api.sendMessage(phoneNumber, message);
      return result;
    } catch (err) {
      setError(err.message);
      throw err;
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    const fetchStats = async () => {
      try {
        const data = await api.getDashboardStats();
        setStats(data.data);
      } catch (err) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    };

    fetchStats();
  }, []);

  return { stats, sendMessage, loading, error };
};
```

### 3. Component Example (components/SendMessage.jsx)
```javascript
import { useState } from 'react';
import { useWhatsApp } from '../hooks/useWhatsApp';

export default function SendMessage() {
  const [phoneNumber, setPhoneNumber] = useState('');
  const [message, setMessage] = useState('');
  const { sendMessage, loading } = useWhatsApp();

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      const result = await sendMessage(phoneNumber, message);
      alert(`Message sent successfully to ${result.recipient}`);
      setPhoneNumber('');
      setMessage('');
    } catch (error) {
      alert(`Error: ${error.message}`);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="p-4 border rounded">
      <input
        type="tel"
        placeholder="Phone Number (919876543210)"
        value={phoneNumber}
        onChange={(e) => setPhoneNumber(e.target.value)}
        className="w-full p-2 border rounded mb-2"
        required
      />
      <textarea
        placeholder="Message"
        value={message}
        onChange={(e) => setMessage(e.target.value)}
        className="w-full p-2 border rounded mb-2"
        rows={3}
        required
      />
      <button
        type="submit"
        disabled={loading}
        className="bg-blue-500 text-white px-4 py-2 rounded disabled:opacity-50"
      >
        {loading ? 'Sending...' : 'Send Message'}
      </button>
    </form>
  );
}
```

---

## 🚨 Security Notes

### 1. Production CORS Configuration
- Only allow specific domains (never use `*` in production)
- Use environment variables for frontend URLs
- Enable credentials only if needed

### 2. Next.js Environment Variables
```bash
# .env.local (development)
NEXT_PUBLIC_API_URL=http://localhost:5001

# .env.production (production)
NEXT_PUBLIC_API_URL=https://your-railway-app.railway.app
```

### 3. Railway Environment Variables
```bash
FRONTEND_URL=https://your-nextjs-app.vercel.app
```

---

## 🔍 Common Issues & Solutions

### Issue: "CORS policy" error in browser
```
Access to fetch at 'http://localhost:5001/api/...' from origin 'http://localhost:3000' 
has been blocked by CORS policy
```

**Solution:**
- ✅ Ensure Flask server is running
- ✅ Check `FRONTEND_URL` environment variable
- ✅ Verify Next.js is running on port 3000

### Issue: Preflight request fails
**Solution:**
- ✅ Make sure `flask-cors` is installed
- ✅ Check CORS configuration in app.py
- ✅ Verify `OPTIONS` method is allowed

### Issue: Production CORS errors
**Solution:**
- ✅ Set `FRONTEND_URL` in Railway dashboard
- ✅ Use HTTPS URLs for production
- ✅ Update Next.js `NEXT_PUBLIC_API_URL`

---

## 📋 Deployment Checklist

### Railway (Backend)
- [ ] `flask-cors` in requirements.txt
- [ ] CORS configuration in app.py
- [ ] `FRONTEND_URL` environment variable set
- [ ] Deploy and test endpoints

### Vercel/Netlify (Frontend)
- [ ] `NEXT_PUBLIC_API_URL` environment variable
- [ ] Test API calls from deployed frontend
- [ ] Verify CORS headers in browser dev tools

---

## 🧪 Testing Commands

```bash
# Test health endpoint with CORS
curl -i -H "Origin: http://localhost:3000" http://localhost:5001/health

# Test preflight request
curl -i -X OPTIONS \
  -H "Origin: http://localhost:3000" \
  -H "Access-Control-Request-Method: POST" \
  -H "Access-Control-Request-Headers: Content-Type" \
  http://localhost:5001/send-message

# Test POST request
curl -i -X POST \
  -H "Origin: http://localhost:3000" \
  -H "Content-Type: application/json" \
  -d '{"phone_number":"919876543210","message":"Test"}' \
  http://localhost:5001/send-message
```

---

✅ **CORS is now properly configured for your Next.js frontend!** 🎉

Your Flask backend will accept requests from:
- `http://localhost:3000` (Next.js development)
- Production domain (via `FRONTEND_URL` environment variable) 
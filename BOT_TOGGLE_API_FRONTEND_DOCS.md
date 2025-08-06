# 🤖 Bot Toggle API - Frontend Implementation Guide

## 🎯 **Overview**

The Bot Toggle API allows frontend applications to control automatic AI responses for individual WhatsApp conversations. This enables human agents to take over conversations when needed.

**Base URL**: `https://whatsapp-ai-chatbot-production-bc92.up.railway.app`

---

## 📋 **API Endpoints Summary**

| Method | Endpoint | Purpose |
|--------|----------|---------|
| `GET` | `/api/bot/status-summary` | Get overall bot status across all conversations |
| `GET` | `/api/bot/status/{conversation_id}` | Get bot status for specific conversation |
| `POST` | `/api/bot/toggle/{conversation_id}` | Toggle bot by conversation ID |
| `POST` | `/api/bot/toggle-by-phone` | Toggle bot by phone number (recommended) |
| `POST` | `/api/bot/bulk-toggle` | Toggle multiple conversations at once |

---

## 🚀 **API Reference**

### **1. Get Bot Status Summary**

**Endpoint**: `GET /api/bot/status-summary`  
**Purpose**: Get overview of bot status across all conversations  
**Authentication**: None required  

**Request**:
```javascript
fetch('https://whatsapp-ai-chatbot-production-bc92.up.railway.app/api/bot/status-summary')
```

**Response**:
```json
{
  "status": "success",
  "data": {
    "summary": {
      "total_conversations": 16,
      "bot_enabled": 15,
      "bot_disabled": 1,
      "enabled_percentage": 93.8
    },
    "disabled_conversations": [
      {
        "conversation_id": "68b5555b-95f4-4b88-b366-4a8784b50c19",
        "contact": {
          "phone_number": "917033009600_s_whatsapp_net",
          "name": "John Doe"
        }
      }
    ],
    "timestamp": "2025-06-12T12:55:24.339488+00:00"
  }
}
```

---

### **2. Get Bot Status for Specific Conversation**

**Endpoint**: `GET /api/bot/status/{conversation_id}`  
**Purpose**: Check if bot is enabled for a specific conversation  

**Request**:
```javascript
const conversationId = "68b5555b-95f4-4b88-b366-4a8784b50c19";
fetch(`https://whatsapp-ai-chatbot-production-bc92.up.railway.app/api/bot/status/${conversationId}`)
```

**Response**:
```json
{
  "status": "success",
  "data": {
    "conversation_id": "68b5555b-95f4-4b88-b366-4a8784b50c19",
    "bot_enabled": false,
    "contact": {
      "phone_number": "917033009600_s_whatsapp_net",
      "name": "John Doe"
    },
    "status_text": "Bot is paused - Human is handling"
  }
}
```

---

### **3. Toggle Bot by Conversation ID**

**Endpoint**: `POST /api/bot/toggle/{conversation_id}`  
**Purpose**: Enable/disable bot for specific conversation  

**Request**:
```javascript
const conversationId = "68b5555b-95f4-4b88-b366-4a8784b50c19";

fetch(`https://whatsapp-ai-chatbot-production-bc92.up.railway.app/api/bot/toggle/${conversationId}`, {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({
    "enabled": false,
    "reason": "Customer requested human support"
  })
})
```

**Request Body**:
```json
{
  "enabled": false,           // Optional: true/false to force state, omit to toggle
  "reason": "Human takeover"  // Optional: reason for the change
}
```

**Response**:
```json
{
  "status": "success",
  "message": "Bot disabled for conversation with John Doe",
  "data": {
    "conversation_id": "68b5555b-95f4-4b88-b366-4a8784b50c19",
    "previous_status": true,
    "new_status": false,
    "action": "disabled",
    "contact": {
      "phone_number": "917033009600_s_whatsapp_net",
      "name": "John Doe"
    },
    "reason": "Customer requested human support",
    "timestamp": "2025-06-12T10:30:00Z"
  }
}
```

---

### **4. Toggle Bot by Phone Number** ⭐ **Recommended**

**Endpoint**: `POST /api/bot/toggle-by-phone`  
**Purpose**: Enable/disable bot using phone number (easier for frontend)  

**Request**:
```javascript
fetch('https://whatsapp-ai-chatbot-production-bc92.up.railway.app/api/bot/toggle-by-phone', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({
    "phone_number": "917033009600",  // Can be with or without country code
    "enabled": false,
    "reason": "Agent taking over for technical support"
  })
})
```

**Request Body**:
```json
{
  "phone_number": "917033009600",    // Required: phone number (various formats accepted)
  "enabled": false,                  // Optional: true/false to force state, omit to toggle
  "reason": "Human agent needed"     // Optional: reason for toggle
}
```

**Phone Number Formats Accepted**:
- `917033009600`
- `+917033009600`
- `91-7033-009600`
- `917033009600_s_whatsapp_net`

**Response**:
```json
{
  "status": "success",
  "message": "Bot disabled for 917033009600_s_whatsapp_net",
  "data": {
    "conversation_id": "68b5555b-95f4-4b88-b366-4a8784b50c19",
    "previous_status": true,
    "new_status": false,
    "action": "disabled",
    "contact": {
      "phone_number": "917033009600_s_whatsapp_net",
      "name": "John Doe"
    },
    "reason": "Agent taking over for technical support",
    "timestamp": "2025-06-12T10:30:00Z"
  }
}
```

---

### **5. Bulk Toggle**

**Endpoint**: `POST /api/bot/bulk-toggle`  
**Purpose**: Enable/disable bot for multiple conversations at once  

**Request**:
```javascript
fetch('https://whatsapp-ai-chatbot-production-bc92.up.railway.app/api/bot/bulk-toggle', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({
    "conversation_ids": [
      "68b5555b-95f4-4b88-b366-4a8784b50c19",
      "f881851f-f1b4-4b27-9a0c-e2107e6f2376"
    ],
    "enabled": false,
    "reason": "Maintenance window - human agents only"
  })
})
```

**Request Body**:
```json
{
  "conversation_ids": ["id1", "id2"],  // Required: array of conversation IDs
  "enabled": false,                    // Required: new state for all conversations
  "reason": "Bulk operation"           // Optional: reason for bulk change
}
```

**Response**:
```json
{
  "status": "success",
  "message": "Bot disabled for 2 conversations",
  "data": {
    "conversation_ids": ["68b5555b-95f4-4b88-b366-4a8784b50c19", "f881851f-f1b4-4b27-9a0c-e2107e6f2376"],
    "new_status": false,
    "action": "disabled",
    "updated_count": 2,
    "reason": "Maintenance window - human agents only",
    "timestamp": "2025-06-12T10:30:00Z"
  }
}
```

---

## ⚠️ **Error Responses**

All APIs return consistent error format:

```json
{
  "status": "error",
  "message": "Descriptive error message"
}
```

**Common Error Codes**:
- `400`: Bad Request (missing required fields)
- `404`: Not Found (conversation/phone number not found)
- `500`: Internal Server Error
- `503`: Service Unavailable (database connection issues)

**Example Error**:
```json
{
  "status": "error",
  "message": "No conversation found for this phone number"
}
```

---

## 💻 **Frontend Integration Examples**

### **React Hook for Bot Toggle**

```jsx
import { useState, useCallback } from 'react';

const useBotToggle = () => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const API_BASE = 'https://whatsapp-ai-chatbot-production-bc92.up.railway.app';

  const toggleBotByPhone = useCallback(async (phoneNumber, enabled, reason = '') => {
    setLoading(true);
    setError(null);
    
    try {
      const response = await fetch(`${API_BASE}/api/bot/toggle-by-phone`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          phone_number: phoneNumber,
          enabled,
          reason
        })
      });

      const data = await response.json();
      
      if (data.status === 'error') {
        throw new Error(data.message);
      }
      
      return data;
    } catch (err) {
      setError(err.message);
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  const getBotStatusSummary = useCallback(async () => {
    setLoading(true);
    setError(null);
    
    try {
      const response = await fetch(`${API_BASE}/api/bot/status-summary`);
      const data = await response.json();
      
      if (data.status === 'error') {
        throw new Error(data.message);
      }
      
      return data;
    } catch (err) {
      setError(err.message);
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  return {
    toggleBotByPhone,
    getBotStatusSummary,
    loading,
    error
  };
};

export default useBotToggle;
```

### **Bot Toggle Component**

```jsx
import React, { useState, useEffect } from 'react';
import useBotToggle from './useBotToggle';

const BotToggleCard = ({ phoneNumber, contactName, initialStatus = true }) => {
  const [botEnabled, setBotEnabled] = useState(initialStatus);
  const { toggleBotByPhone, loading, error } = useBotToggle();

  const handleToggle = async () => {
    try {
      const newStatus = !botEnabled;
      const reason = newStatus ? 'Bot re-enabled' : 'Human agent taking over';
      
      const result = await toggleBotByPhone(phoneNumber, newStatus, reason);
      setBotEnabled(result.data.new_status);
      
      // Show success notification
      alert(`Bot ${result.data.action} for ${contactName || phoneNumber}`);
    } catch (err) {
      console.error('Toggle failed:', err);
      alert(`Failed to toggle bot: ${err.message}`);
    }
  };

  return (
    <div className="bot-toggle-card">
      <div className="contact-info">
        <h3>{contactName || 'Unknown Contact'}</h3>
        <p className="phone-number">{phoneNumber}</p>
      </div>
      
      <div className="bot-status">
        <div className={`status-indicator ${botEnabled ? 'enabled' : 'disabled'}`}>
          <span className="status-dot"></span>
          <span className="status-text">
            {botEnabled ? 'Bot Active' : 'Human Handling'}
          </span>
        </div>
        
        <button 
          onClick={handleToggle}
          disabled={loading}
          className={`toggle-button ${botEnabled ? 'enabled' : 'disabled'}`}
        >
          {loading ? 'Updating...' : (botEnabled ? '🤖 Disable Bot' : '👤 Enable Bot')}
        </button>
      </div>
      
      {error && (
        <div className="error-message">
          Error: {error}
        </div>
      )}
    </div>
  );
};

export default BotToggleCard;
```

### **Dashboard Summary Component**

```jsx
import React, { useState, useEffect } from 'react';
import useBotToggle from './useBotToggle';

const BotStatusDashboard = () => {
  const [summary, setSummary] = useState(null);
  const { getBotStatusSummary, loading, error } = useBotToggle();

  useEffect(() => {
    loadSummary();
  }, []);

  const loadSummary = async () => {
    try {
      const data = await getBotStatusSummary();
      setSummary(data.data);
    } catch (err) {
      console.error('Failed to load summary:', err);
    }
  };

  if (loading && !summary) return <div>Loading...</div>;
  if (error) return <div>Error: {error}</div>;
  if (!summary) return null;

  return (
    <div className="bot-status-dashboard">
      <h2>Bot Status Overview</h2>
      
      <div className="summary-cards">
        <div className="summary-card">
          <h3>Total Conversations</h3>
          <div className="metric">{summary.summary.total_conversations}</div>
        </div>
        
        <div className="summary-card enabled">
          <h3>Bot Enabled</h3>
          <div className="metric">{summary.summary.bot_enabled}</div>
        </div>
        
        <div className="summary-card disabled">
          <h3>Human Handling</h3>
          <div className="metric">{summary.summary.bot_disabled}</div>
        </div>
        
        <div className="summary-card percentage">
          <h3>Automation Rate</h3>
          <div className="metric">{summary.summary.enabled_percentage}%</div>
        </div>
      </div>

      {summary.disabled_conversations.length > 0 && (
        <div className="disabled-conversations">
          <h3>Conversations with Human Agents</h3>
          <div className="conversation-list">
            {summary.disabled_conversations.map((conv) => (
              <div key={conv.conversation_id} className="conversation-item">
                <span className="contact-name">
                  {conv.contact.name || 'Unknown'}
                </span>
                <span className="phone-number">
                  {conv.contact.phone_number.replace('_s_whatsapp_net', '')}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}
      
      <button onClick={loadSummary} className="refresh-button">
        Refresh Status
      </button>
    </div>
  );
};

export default BotStatusDashboard;
```

### **CSS Styles**

```css
.bot-toggle-card {
  border: 1px solid #e1e5e9;
  border-radius: 8px;
  padding: 16px;
  margin-bottom: 12px;
  background: white;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

.contact-info h3 {
  margin: 0 0 4px 0;
  color: #2c3e50;
}

.phone-number {
  color: #7f8c8d;
  font-size: 14px;
  margin: 0;
}

.bot-status {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 12px;
}

.status-indicator {
  display: flex;
  align-items: center;
  gap: 8px;
}

.status-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
}

.status-indicator.enabled .status-dot {
  background-color: #27ae60;
}

.status-indicator.disabled .status-dot {
  background-color: #e74c3c;
}

.toggle-button {
  padding: 8px 16px;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-weight: 500;
  transition: all 0.2s;
}

.toggle-button.enabled {
  background-color: #27ae60;
  color: white;
}

.toggle-button.disabled {
  background-color: #95a5a6;
  color: white;
}

.toggle-button:hover {
  opacity: 0.9;
}

.toggle-button:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.error-message {
  color: #e74c3c;
  font-size: 14px;
  margin-top: 8px;
  padding: 8px;
  background-color: #fdf2f2;
  border-radius: 4px;
}

.summary-cards {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 16px;
  margin-bottom: 24px;
}

.summary-card {
  padding: 20px;
  border-radius: 8px;
  text-align: center;
  background: white;
  border: 1px solid #e1e5e9;
}

.summary-card h3 {
  margin: 0 0 8px 0;
  color: #7f8c8d;
  font-size: 14px;
  text-transform: uppercase;
}

.summary-card .metric {
  font-size: 32px;
  font-weight: bold;
  color: #2c3e50;
}

.summary-card.enabled .metric {
  color: #27ae60;
}

.summary-card.disabled .metric {
  color: #e74c3c;
}
```

---

## 🎯 **Usage Examples**

### **1. Customer Support Dashboard**
```javascript
// Disable bot when customer escalates to human
await toggleBotByPhone('917033009600', false, 'Customer requested human agent');

// Re-enable after issue resolved
await toggleBotByPhone('917033009600', true, 'Issue resolved by agent');
```

### **2. Premium Customer Management**
```javascript
// Disable bot for VIP customers during business hours
const vipCustomers = ['917033009600', '918881616123'];
for (const phone of vipCustomers) {
  await toggleBotByPhone(phone, false, 'VIP customer - human support only');
}
```

### **3. Maintenance Mode**
```javascript
// Get all conversations and disable bot for maintenance
const summary = await getBotStatusSummary();
const allConversationIds = summary.data.disabled_conversations.map(c => c.conversation_id);

await fetch('/api/bot/bulk-toggle', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    conversation_ids: allConversationIds,
    enabled: false,
    reason: 'System maintenance - human agents only'
  })
});
```

---

## 🔧 **Best Practices**

1. **Error Handling**: Always wrap API calls in try-catch blocks
2. **Loading States**: Show loading indicators during API calls
3. **User Feedback**: Provide clear success/error messages
4. **Real-time Updates**: Consider polling or WebSocket for live status updates
5. **Permissions**: Implement role-based access for bot toggle functionality
6. **Audit Trail**: Log all toggle actions for compliance and debugging

---

## 🚀 **Quick Start Checklist**

- [ ] Copy the `useBotToggle` hook to your project
- [ ] Update the `API_BASE` URL to your deployment
- [ ] Implement the `BotToggleCard` component
- [ ] Add the dashboard summary component
- [ ] Style components with provided CSS
- [ ] Test with real phone numbers
- [ ] Add error handling and user feedback
- [ ] Deploy and monitor usage

Your Bot Toggle API is now ready for frontend integration! 🎉 
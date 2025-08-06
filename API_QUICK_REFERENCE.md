# 🚀 WhatsApp Chatbot API - Quick Reference

**For UI/UX Designers**

## 📋 Essential Endpoints for Frontend Design

### 🏠 Dashboard Data
```
GET /api/dashboard-stats
→ Total conversations, messages today, active campaigns, conversion rates
```

### 💬 Conversations
```
GET /api/conversations?limit=20&offset=0
→ List of all chat conversations with contact details

GET /api/conversation/{id}
→ Full chat history for specific conversation
```

### 👥 Contacts & CRM
```
GET /api/crm/contacts?limit=50
→ Contact list with lead scores, status, tags

GET /api/crm/deals
→ Sales opportunities and deals

GET /api/crm/tasks
→ Follow-up tasks and reminders
```

### 💬 Messaging
```
POST /send-message
Body: {"phone_number": "91XXXXXXXXX", "message": "Hello!"}
→ Send individual WhatsApp message

POST /send-bulk-message
Body: {"campaign_name": "Launch", "message": "Text", "contacts": [...]}
→ Send bulk campaign messages
```

### 📊 Campaigns
```
GET /api/campaigns
→ List of marketing campaigns with metrics

GET /api/campaign/{id}
→ Detailed campaign analytics and performance
```

---

## 🎨 Key Data Structures

### Contact Object
```json
{
  "id": "contact_123",
  "phone_number": "919876543210",
  "name": "John Doe",
  "email": "john@example.com",
  "company": "ABC Corp",
  "status": "lead|customer|inactive",
  "lead_score": 75,
  "tags": ["enterprise", "interested"],
  "last_contact": "2024-01-15T10:25:00Z"
}
```

### Conversation Object
```json
{
  "id": "conv_abc123",
  "contact": { "name": "John", "phone": "91XXXXX" },
  "last_message_at": "2024-01-15T10:25:00Z",
  "message_count": 15,
  "last_message_preview": "When can we schedule demo?",
  "status": "active|closed|pending"
}
```

### Message Object
```json
{
  "id": "msg_1",
  "role": "user|assistant",
  "content": "Message text here",
  "timestamp": "2024-01-15T10:00:00Z",
  "status": "sent|delivered|read|failed"
}
```

### Campaign Object
```json
{
  "id": "camp_123",
  "name": "Product Launch",
  "status": "active|completed|scheduled|failed",
  "total_recipients": 500,
  "messages_delivered": 472,
  "response_rate": 8.2,
  "created_at": "2024-01-15T13:00:00Z"
}
```

---

## 🎯 UI Components Needed

### 📊 Dashboard Components
- **Stats Cards**: Total chats, today's messages, conversion rate, active campaigns
- **Recent Activity Feed**: New contacts, message responses, campaign updates
- **Quick Actions**: Send message, create campaign, add contact
- **System Status Indicators**: AI, WhatsApp, Database connection status

### 💬 Chat Interface Components
- **Conversation List**: Contact name, last message, timestamp, unread indicator
- **Message Thread**: Chat bubbles (user/bot), timestamps, delivery status
- **Contact Info Panel**: Name, phone, email, company, lead score, tags
- **Message Input**: Text area, send button, emoji picker

### 👥 CRM Components
- **Contact Table**: Name, company, status, lead score, last contact, actions
- **Deal Cards**: Deal title, value, stage, probability, expected close date
- **Task List**: Title, due date, priority, assigned contact, completion status
- **Contact Profile**: Full contact details, interaction history, notes

### 📈 Campaign Components
- **Campaign Cards**: Name, status, recipients count, delivery/response rates
- **Campaign Builder**: Message composer, contact selector, scheduling
- **Analytics Charts**: Delivery rates, response trends, performance metrics
- **Campaign Timeline**: Created → Sent → Delivered → Completed status

---

## 🎨 Design Requirements

### Color Scheme
- **Primary**: #667eea (Blue)
- **WhatsApp**: #25d366 (Green) 
- **Success**: #48bb78
- **Warning**: #ed8936
- **Error**: #f56565

### Status Indicators
- **Online/Active**: Green dot
- **Offline/Inactive**: Gray dot
- **Pending**: Yellow dot
- **Failed**: Red dot

### Message Status Icons
- **Sent**: Single check ✓
- **Delivered**: Double check ✓✓
- **Read**: Blue double check ✓✓
- **Failed**: Red exclamation ⚠️

---

## 📱 Responsive Breakpoints

```css
/* Mobile: 320px - 767px */
/* Tablet: 768px - 1023px */
/* Desktop: 1024px+ */
```

### Mobile Priorities
1. Chat interface (conversations view)
2. Quick message sending
3. Contact search
4. Basic dashboard stats

### Desktop Features
1. Full dashboard with analytics
2. Split-view conversations
3. Advanced CRM features
4. Campaign management
5. Detailed reporting

---

## 🔄 Real-time Updates Needed

### WebSocket Events
- New incoming messages
- Campaign status changes
- Contact activity updates
- System status changes

### Auto-refresh Components
- Dashboard stats (every 30 seconds)
- Conversation list (when new messages arrive)
- Campaign metrics (during active campaigns)

---

## 📋 Form Requirements

### Send Message Form
```
- Phone Number (required, format: 91XXXXXXXXX)
- Message Text (required, max 1000 chars)
- Send button
```

### Bulk Campaign Form
```
- Campaign Name (required)
- Message Text (required) 
- Contact Selection (upload CSV or select from list)
- Schedule Time (optional)
- Tags (optional)
```

### Contact Form
```
- Name (required)
- Phone Number (required, format validation)
- Email (optional, email validation)
- Company (optional)
- Status (dropdown: lead/customer/inactive)
- Tags (multi-select)
- Notes (textarea)
```

### Deal Form
```
- Title (required)
- Contact (dropdown/search)
- Value (number, currency selector)
- Stage (dropdown: initial/proposal/negotiation/closed)
- Expected Close Date (date picker)
- Probability (slider 0-100%)
- Notes (textarea)
```

---

## ⚠️ Error Handling

### Common Error States
- **Network Error**: "Unable to connect. Please check your internet."
- **Invalid Phone**: "Please enter a valid phone number with country code."
- **Message Too Long**: "Message exceeds 1000 character limit."
- **API Error**: "Something went wrong. Please try again."

### Loading States
- **Dashboard**: Skeleton cards while loading stats
- **Conversations**: Loading spinner for message history
- **Sending**: Disable send button, show sending indicator
- **Campaigns**: Progress bar for bulk message sending

---

## 💡 UX Best Practices

### Navigation
- Clear breadcrumbs for deep pages
- Persistent navigation sidebar
- Search functionality in header
- Quick action floating buttons

### Feedback
- Toast notifications for actions
- Confirmation modals for destructive actions
- Progress indicators for long operations
- Success animations for completed actions

### Accessibility
- Keyboard navigation support
- Screen reader friendly labels
- High contrast mode support
- Focus indicators for all interactive elements

---

This quick reference should help you understand the data flow and design requirements. The full API documentation has complete details with request/response examples! 
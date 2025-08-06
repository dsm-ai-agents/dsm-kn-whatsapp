# 📱 WASender Contact Sync Integration Guide

## 🎯 Overview

This guide explains how to integrate WASender API contact synchronization to display proper contact names instead of phone numbers in the conversations interface.

### ✨ Features

- **Automatic Contact Sync**: Fetch contact information from WASender API
- **Real-time Enrichment**: Auto-sync contacts when viewing conversations
- **Verified Names**: Display WhatsApp verified business names
- **Profile Images**: Support for WhatsApp profile pictures
- **Business Account Detection**: Identify WhatsApp Business accounts
- **Periodic Sync**: Background synchronization every 6 hours
- **API Endpoints**: Manual sync triggers via REST API

---

## 🚀 Quick Setup

### 1. Database Migration

First, run the database migration to add WASender fields:

```sql
-- Run this in your Supabase SQL editor
\i database_migration_wasender_contacts.sql
```

### 2. Install Dependencies

```bash
pip install schedule
```

### 3. Test the Integration

```bash
python test_wasender_contact_sync.py
```

---

## 📊 How It Works

### Contact Sync Process

1. **Fetch Contacts**: Retrieve all contacts from WASender API
2. **Extract Information**: Parse contact data (name, verified name, profile image)
3. **Update Database**: Store enriched contact information
4. **Display Enhancement**: Show proper names in conversations

### Data Flow

```
WASender API → Contact Service → Database → Conversations API → Frontend
```

---

## 🔧 API Endpoints

### 1. Sync All Contacts

```http
POST /api/sync/wasender-contacts
```

**Response:**
```json
{
  "status": "success",
  "message": "Contact sync completed",
  "stats": {
    "total_fetched": 150,
    "successful_updates": 145,
    "failed_updates": 5,
    "contacts_with_names": 120,
    "contacts_without_names": 25
  }
}
```

### 2. Sync Single Contact

```http
POST /api/sync/wasender-contact/{phone_number}
```

**Example:**
```bash
curl -X POST http://localhost:5001/api/sync/wasender-contact/919876543210
```

### 3. Sync Conversation Contacts

```http
POST /api/sync/conversation-contacts
```

**Request Body (optional):**
```json
{
  "conversation_ids": ["conv_123", "conv_456"]
}
```

### 4. Get Sync Status

```http
GET /api/sync/status
```

**Response:**
```json
{
  "status": "success",
  "data": {
    "wasender_configured": true,
    "sync_available": true,
    "last_sync": "2024-01-15T10:30:00Z"
  }
}
```

---

## 🔄 Automatic Sync

### Frontend Integration

Add `auto_sync=true` parameter to conversations API:

```javascript
// Frontend code
const response = await fetch('/api/conversations/unique?auto_sync=true&limit=50');
```

This will automatically sync contacts that don't have names when loading conversations.

### Periodic Background Sync

The system automatically starts background sync every 6 hours when configured:

```python
# In your app startup
from src.services.wasender_contact_service import get_wasender_contact_service

# Start periodic sync
service = get_wasender_contact_service(auto_start_periodic=True)
```

---

## 📋 Database Schema

### New Fields in `contacts` Table

| Field | Type | Description |
|-------|------|-------------|
| `verified_name` | TEXT | WhatsApp verified business name |
| `profile_image_url` | TEXT | Profile picture URL |
| `whatsapp_status` | TEXT | WhatsApp status message |
| `is_business_account` | BOOLEAN | Business account flag |
| `last_updated_from_wasender` | TIMESTAMP | Last sync time |
| `wasender_sync_status` | TEXT | Sync status (synced/not_synced) |
| `wasender_jid` | TEXT | Original WhatsApp JID |
| `raw_wasender_data` | JSONB | Raw API response |

### Contact Display Priority

1. **Verified Name** (WhatsApp Business verified name)
2. **Name** (Regular contact name)
3. **Company** (If available in CRM)
4. **Formatted Phone Number** (Fallback)

---

## 🎨 Frontend Display

### Contact Information Structure

```json
{
  "id": "contact_123",
  "phone_number": "919876543210",
  "display_phone": "+91 98765 43210",
  "name": "John Doe",
  "verified_name": "John Doe Business",
  "profile_image_url": "https://example.com/profile.jpg",
  "is_business_account": true,
  "whatsapp_status": "Hey there! I am using WhatsApp."
}
```

### Display Logic

```javascript
function getContactDisplayName(contact) {
  return contact.verified_name || 
         contact.name || 
         `Contact from ${contact.company}` || 
         contact.display_phone;
}
```

---

## 🔍 Testing

### Run Test Suite

```bash
python test_wasender_contact_sync.py
```

### Test Results

```
🧪 WASender Contact Sync Test Suite
==================================================
Configuration            ✅ PASS
Database Connection      ✅ PASS
Database Schema          ✅ PASS
Fetch Contacts          ✅ PASS
Single Contact Sync     ✅ PASS
Conversation Contact Sync ✅ PASS
API Endpoints           ✅ PASS

Total: 7/7 tests passed
```

---

## 📈 Monitoring

### Sync Statistics

```sql
-- Get sync statistics
SELECT * FROM get_wasender_sync_stats();
```

### View Enriched Contacts

```sql
-- View contacts with enrichment status
SELECT * FROM contacts_enriched 
WHERE is_wasender_synced = true
LIMIT 10;
```

### Check Sync Status

```sql
-- Check recent syncs
SELECT phone_number, name, verified_name, last_updated_from_wasender
FROM contacts 
WHERE wasender_sync_status = 'synced'
ORDER BY last_updated_from_wasender DESC
LIMIT 20;
```

---

## 🚨 Troubleshooting

### Common Issues

#### 1. No Contacts Fetched
```bash
# Check WASender API token
echo $WASENDER_API_TOKEN

# Test API directly
curl -H "Authorization: Bearer $WASENDER_API_TOKEN" \
     https://wasenderapi.com/api/contacts
```

#### 2. Database Schema Issues
```sql
-- Check if migration ran
SELECT column_name FROM information_schema.columns 
WHERE table_name = 'contacts' AND column_name = 'verified_name';
```

#### 3. Sync Failures
```bash
# Check logs
tail -f logs/app.log | grep -i wasender
```

### Error Codes

| Code | Issue | Solution |
|------|-------|----------|
| 503 | WASender API not configured | Set `WASENDER_API_TOKEN` |
| 500 | Database connection failed | Check Supabase credentials |
| 404 | Contact not found | Contact may not exist in WASender |

---

## 🔧 Configuration

### Environment Variables

```bash
# Required
WASENDER_API_TOKEN=your_wasender_api_token

# Optional
WASENDER_SYNC_INTERVAL_HOURS=6
WASENDER_AUTO_SYNC_ENABLED=true
```

### Service Configuration

```python
# In your app configuration
from src.services.wasender_contact_service import wasender_contact_service

# Configure sync intervals
wasender_contact_service.start_periodic_sync(interval_hours=4)
```

---

## 📝 Best Practices

### 1. Sync Strategy

- **Initial Sync**: Run full sync once during setup
- **Periodic Sync**: Background sync every 6 hours
- **On-Demand Sync**: Auto-sync when viewing conversations
- **Conversation Sync**: Sync only active conversation contacts

### 2. Performance

- Use `auto_sync=true` sparingly (only for important views)
- Implement caching for frequently accessed contacts
- Monitor sync frequency to avoid API rate limits

### 3. Data Privacy

- Store only necessary contact information
- Respect user privacy settings
- Implement data retention policies

---

## 🔮 Future Enhancements

### Planned Features

- **Real-time Sync**: WebSocket-based contact updates
- **Selective Sync**: Sync only specific contact groups
- **Contact Deduplication**: Merge duplicate contacts
- **Sync Analytics**: Detailed sync performance metrics
- **Bulk Operations**: Batch contact updates

### Integration Opportunities

- **WhatsApp Business API**: Direct integration
- **CRM Systems**: Bidirectional sync
- **Contact Management**: Advanced contact organization
- **Analytics**: Contact engagement tracking

---

## 📞 Support

For issues or questions:

1. Check the test suite results
2. Review the logs for error messages
3. Verify WASender API token and permissions
4. Ensure database migration completed successfully

---

*This feature enhances the user experience by showing proper contact names instead of phone numbers, making conversations more personal and professional.* 
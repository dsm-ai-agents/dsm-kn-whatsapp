# 📱 WhatsApp Group Messaging Module

A **standalone, reusable module** for WhatsApp group messaging and scheduling that can be easily integrated into any Python application.

## 🎯 **Features**

- ✅ **Group Management** - List, create, and manage WhatsApp groups
- ✅ **Group Messaging** - Send messages to individual or multiple groups
- ✅ **Message Scheduling** - Schedule messages for future delivery
- ✅ **Recurring Messages** - Daily, weekly, monthly recurring schedules
- ✅ **Database Abstraction** - Works with Supabase, PostgreSQL, etc.
- ✅ **API Provider Support** - Currently supports Wasender API
- ✅ **Modular Design** - Easy to extract and use in other projects

## 🚀 **Quick Start**

### **1. Installation**

```bash
# Install dependencies
pip install supabase python-dateutil APScheduler

# Copy the module to your project
cp -r src/modules/group_messaging /path/to/your/project/
```

### **2. Configuration**

```python
from group_messaging import GroupMessagingConfig, DatabaseManager, GroupService

# Create configuration
config = GroupMessagingConfig.from_env()

# Or create manually
config = GroupMessagingConfig(
    whatsapp_api_token="your_wasender_token",
    database_url="your_supabase_url",
    database_key="your_supabase_key"
)

# Validate configuration
config.validate()
```

### **3. Initialize Services**

```python
# Initialize database
db_manager = DatabaseManager(config)
db_manager.connect()

# Initialize group service
group_service = GroupService(config, db_manager)
```

### **4. Basic Usage**

```python
from datetime import datetime, timedelta

# Get all groups
groups = group_service.get_all_groups()
print(f"Found {len(groups)} groups")

# Send message to a group
success = group_service.send_group_message(
    group_jid="123456789-987654321@g.us",
    message="Hello everyone! 👋"
)

# Schedule a message
from group_messaging.services.scheduler_service import SchedulerService

scheduler = SchedulerService(config, db_manager)
schedule_id = scheduler.schedule_message({
    'message_content': "Reminder: Meeting at 3 PM",
    'target_ids': ["123456789-987654321@g.us"],
    'scheduled_time': datetime.now() + timedelta(hours=1)
})
```

## 📚 **API Reference**

### **GroupService**

```python
from group_messaging import GroupService

service = GroupService(config, db_manager)

# Get all groups from WhatsApp
groups = service.get_all_groups()

# Send message to single group
success = service.send_group_message(
    group_jid="123@g.us", 
    message="Hello!"
)

# Send message to multiple groups
results = service.send_bulk_group_message(
    group_jids=["123@g.us", "456@g.us"],
    message="Bulk message!"
)

# Create new group
group_id = service.create_group(
    name="My New Group",
    participants=["1234567890", "0987654321"]
)
```

### **SchedulerService**

```python
from group_messaging import SchedulerService
from datetime import datetime, timedelta

scheduler = SchedulerService(config, db_manager)

# Schedule one-time message
schedule_id = scheduler.schedule_message({
    'message_content': "One-time message",
    'target_ids': ["123@g.us"],
    'scheduled_time': datetime.now() + timedelta(hours=2)
})

# Schedule recurring message
schedule_id = scheduler.schedule_recurring_message({
    'message_content': "Daily reminder",
    'target_ids': ["123@g.us"],
    'scheduled_time': datetime.now() + timedelta(hours=1),
    'recurring_pattern': 'daily',
    'recurring_end_date': datetime.now() + timedelta(days=30)
})

# Get scheduled messages
scheduled = scheduler.get_scheduled_messages()

# Cancel scheduled message
scheduler.cancel_scheduled_message(schedule_id)
```

## 🔧 **Integration Examples**

### **Flask Integration**

```python
from flask import Flask, Blueprint, request, jsonify
from group_messaging import (
    GroupMessagingConfig, DatabaseManager, 
    GroupService, SchedulerService,
    create_group_messaging_blueprint
)

app = Flask(__name__)

# Initialize module
config = GroupMessagingConfig.from_env()
db_manager = DatabaseManager(config)
db_manager.connect()

# Create services
group_service = GroupService(config, db_manager)
scheduler_service = SchedulerService(config, db_manager)

# Register the blueprint
group_bp = create_group_messaging_blueprint(
    group_service=group_service,
    scheduler_service=scheduler_service
)
app.register_blueprint(group_bp, url_prefix='/api/groups')

if __name__ == '__main__':
    app.run(debug=True)
```

### **Standalone Script**

```python
#!/usr/bin/env python3
"""
Standalone group messaging script
"""
import os
from datetime import datetime, timedelta
from group_messaging import (
    GroupMessagingConfig, DatabaseManager, 
    GroupService, SchedulerService
)

def main():
    # Load configuration from environment
    config = GroupMessagingConfig.from_env()
    
    try:
        config.validate()
    except ValueError as e:
        print(f"Configuration error: {e}")
        return
    
    # Initialize services
    db_manager = DatabaseManager(config)
    if not db_manager.connect():
        print("Failed to connect to database")
        return
    
    group_service = GroupService(config, db_manager)
    scheduler_service = SchedulerService(config, db_manager)
    
    # Get all groups
    print("📱 Getting WhatsApp groups...")
    groups = group_service.get_all_groups()
    print(f"Found {len(groups)} groups:")
    
    for group in groups:
        print(f"  - {group.name} ({group.group_jid})")
    
    if groups:
        # Send a test message to the first group
        first_group = groups[0]
        print(f"\n📤 Sending test message to {first_group.name}...")
        
        success = group_service.send_group_message(
            group_jid=first_group.group_jid,
            message="🤖 This is a test message from the Group Messaging Module!"
        )
        
        if success:
            print("✅ Message sent successfully!")
        else:
            print("❌ Failed to send message")
        
        # Schedule a message for 1 hour from now
        print(f"\n⏰ Scheduling a message for 1 hour from now...")
        schedule_id = scheduler_service.schedule_message({
            'message_content': "⏰ This is a scheduled message!",
            'target_ids': [first_group.group_jid],
            'scheduled_time': datetime.now() + timedelta(hours=1),
            'campaign_name': 'Test Campaign'
        })
        
        if schedule_id:
            print(f"✅ Message scheduled with ID: {schedule_id}")
        else:
            print("❌ Failed to schedule message")

if __name__ == "__main__":
    main()
```

## 🌐 **REST API Endpoints**

When integrated with Flask, the module provides these endpoints:

```
GET    /api/groups                    # Get all groups
POST   /api/groups/send               # Send message to group
POST   /api/groups/bulk-send          # Send to multiple groups
POST   /api/groups/create             # Create new group

POST   /api/groups/schedule           # Schedule message
GET    /api/groups/scheduled          # Get scheduled messages
PUT    /api/groups/scheduled/{id}     # Update scheduled message
DELETE /api/groups/scheduled/{id}     # Cancel scheduled message
```

### **Example API Calls**

```bash
# Get all groups
curl -X GET "http://localhost:5000/api/groups"

# Send message to group
curl -X POST "http://localhost:5000/api/groups/send" \
  -H "Content-Type: application/json" \
  -d '{
    "group_jid": "123456789-987654321@g.us",
    "message": "Hello from API!"
  }'

# Schedule message
curl -X POST "http://localhost:5000/api/groups/schedule" \
  -H "Content-Type: application/json" \
  -d '{
    "message_content": "Scheduled message",
    "target_ids": ["123456789-987654321@g.us"],
    "scheduled_time": "2024-01-01T15:00:00Z"
  }'
```

## 🗄️ **Database Setup**

### **Run Migration**

```sql
-- Run the migration file
\i src/modules/group_messaging/migrations/001_initial.sql
```

### **Environment Variables**

```bash
# WhatsApp API (Wasender)
WASENDER_API_TOKEN=your_wasender_token

# Database (Supabase)
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_key

# Optional: Module-specific overrides
GROUP_MSG_WHATSAPP_TOKEN=specific_token_for_groups
GROUP_MSG_DB_URL=specific_db_for_groups
```

## 📦 **Using in Other Projects**

### **1. Copy Module**

```bash
# Copy the entire module
cp -r src/modules/group_messaging /path/to/new/project/

# Or create as a package
cd src/modules/group_messaging
python setup.py sdist
pip install dist/group-messaging-1.0.0.tar.gz
```

### **2. Install Dependencies**

```bash
pip install supabase python-dateutil APScheduler requests
```

### **3. Import and Use**

```python
from group_messaging import (
    GroupMessagingConfig,
    DatabaseManager,
    GroupService,
    SchedulerService
)

# Use exactly as shown in examples above
```

## 🔧 **Configuration Options**

```python
config = GroupMessagingConfig(
    # WhatsApp API
    whatsapp_api_provider="wasender",
    whatsapp_api_token="your_token",
    whatsapp_api_url="https://wasenderapi.com/api",
    
    # Database
    database_provider="supabase",
    database_url="your_db_url",
    database_key="your_db_key",
    
    # Scheduling
    scheduler_enabled=True,
    scheduler_timezone="UTC",
    max_scheduled_messages=1000,
    
    # Rate Limiting
    rate_limit_enabled=True,
    messages_per_minute=20,
    messages_per_hour=500,
    
    # Retry Logic
    max_retries=3,
    retry_delay_seconds=5
)
```

## 🧪 **Testing**

```python
# Test the module
python -c "
from group_messaging import GroupMessagingConfig
config = GroupMessagingConfig.from_env()
print('✅ Module loaded successfully!')
print(f'Config: {config.to_dict()}')
"
```

## 📝 **License**

MIT License - Feel free to use in your projects!

---

**Created by Rian Infotech** - Modular WhatsApp Group Messaging Solution 
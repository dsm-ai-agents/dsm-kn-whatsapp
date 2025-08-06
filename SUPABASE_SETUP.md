# Supabase Setup Guide for Rian Infotech WhatsApp Bot

This guide will walk you through setting up Supabase for your WhatsApp bot migration from JSON files to a PostgreSQL database.

## 🚀 Quick Start

### 1. Create a Supabase Project

1. Go to [Supabase](https://supabase.com) and sign up/log in
2. Click "New Project"
3. Choose your organization 
4. Fill in project details:
   - **Name**: `rian-whatsapp-bot` (or your preferred name)
   - **Database Password**: Generate a strong password (save it!)
   - **Region**: Choose closest to your server location
5. Click "Create new project"

### 2. Get Your Project Credentials

Once your project is created:

1. Go to **Settings** → **API**
2. Copy the following values:
   - **Project URL** (starts with `https://`)
   - **Project API keys** → **anon/public key**

### 3. Set Up Database Schema

1. Go to **SQL Editor** in your Supabase dashboard
2. Copy the contents of `database_schema.sql` from this project
3. Paste it into a new query and click "Run"
4. This will create all necessary tables, indexes, and functions

### 4. Configure Environment Variables

Add these to your `.env` file:

```bash
# Supabase Configuration
SUPABASE_URL=your_supabase_project_url_here
SUPABASE_ANON_KEY=your_supabase_anon_key_here
```

Example:
```bash
SUPABASE_URL=https://xyzabcdef.supabase.co
SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

### 5. Install Dependencies

```bash
pip install -r requirements.txt
```

This will install the new Supabase dependencies:
- `supabase`
- `psycopg2-binary`
- `python-dateutil`

### 6. Run Migration Script

```bash
python migrate_to_supabase.py
```

This will:
- ✅ Create a backup of your JSON files
- ✅ Migrate all conversation histories to Supabase
- ✅ Migrate bulk campaign logs to Supabase
- ✅ Verify the migration was successful

### 7. Test the Integration

```bash
python script.py
```

Visit your bot's web interface and:
1. Check the health endpoint - should show `"supabase_connected": true`
2. Send a test message to verify conversations are saved to Supabase
3. Try a bulk message to test campaign tracking

## 📊 Database Schema Overview

### Core Tables

1. **contacts** - Store WhatsApp contact information
2. **conversations** - Store chat histories with timestamps
3. **bulk_campaigns** - Track bulk messaging campaigns
4. **message_results** - Individual message delivery results
5. **contact_lists** - Organize contacts into groups
6. **campaign_analytics** - Store campaign metrics

### Features

- ✅ **Automatic timestamps** with triggers
- ✅ **UUID primary keys** for scalability
- ✅ **Optimized indexes** for fast queries
- ✅ **Foreign key constraints** for data integrity
- ✅ **JSON fields** for flexible metadata storage

## 🔧 Advanced Configuration

### Row Level Security (Optional)

For production deployments, you may want to enable RLS:

```sql
-- Enable RLS on sensitive tables
ALTER TABLE contacts ENABLE ROW LEVEL SECURITY;
ALTER TABLE conversations ENABLE ROW LEVEL SECURITY;

-- Create policies (example)
CREATE POLICY "Users can only see their own data" ON contacts
  FOR ALL USING (auth.uid() = user_id);
```

### Performance Tuning

For high-volume usage:

1. **Connection Pooling** - Use PgBouncer in production
2. **Database Backups** - Enable point-in-time recovery
3. **Monitoring** - Set up Supabase monitoring and alerts

## 🔄 Migration Rollback (If Needed)

If you need to rollback to JSON files:

1. Your original files are safely backed up in `backup_YYYYMMDD_HHMMSS/`
2. Copy them back to `conversations/` and `logs/` directories
3. Comment out the Supabase imports in `script.py`
4. The bot will automatically fallback to JSON file storage

## 🎯 New Features Enabled

With Supabase integration, you now have:

### API Endpoints
- `GET /api/dashboard-stats` - Real-time statistics
- `GET /api/contacts` - Paginated contacts list
- `GET /api/campaigns` - Recent bulk campaigns
- `GET /api/campaign/{id}` - Detailed campaign analytics

### Real-Time Capabilities
- Live campaign progress tracking
- Real-time conversation analytics
- Contact activity monitoring

### Scalability
- Handle thousands of contacts
- Efficient bulk messaging campaigns
- Advanced search and filtering
- Analytics and reporting

## 🛠️ Troubleshooting

### Connection Issues

```bash
# Test Supabase connection
python -c "from supabase_client import get_supabase_manager; print('Connected:', get_supabase_manager().is_connected())"
```

### Common Errors

1. **"Supabase URL or API key not found"**
   - Check your `.env` file has the correct variables
   - Ensure `.env` is in the same directory as `script.py`

2. **"Failed to initialize Supabase client"**
   - Verify your Supabase URL and API key are correct
   - Check your internet connection

3. **"Database schema not found"**
   - Run the SQL schema from `database_schema.sql` in Supabase SQL Editor

### Reset Database (Nuclear Option)

If you need to start fresh:

```sql
-- ⚠️ This will delete all data!
DROP SCHEMA public CASCADE;
CREATE SCHEMA public;
GRANT USAGE ON SCHEMA public TO postgres, anon, authenticated, service_role;
-- Then re-run database_schema.sql
```

## 📞 Support

If you encounter issues:

1. Check the logs in your terminal
2. Verify all environment variables are set correctly
3. Ensure your Supabase project is active and healthy
4. Test the migration script in a development environment first

---

**🎉 Congratulations!** Your WhatsApp bot is now powered by Supabase with enterprise-grade data management, real-time analytics, and unlimited scalability! 
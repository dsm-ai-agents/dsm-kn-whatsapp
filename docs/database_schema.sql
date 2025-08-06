-- Rian Infotech WhatsApp Bot - Supabase Database Schema
-- =====================================================

-- Enable necessary extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- 1. CONTACTS TABLE
-- Stores individual contact information
CREATE TABLE contacts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    phone_number VARCHAR(20) UNIQUE NOT NULL,
    name VARCHAR(255),
    email VARCHAR(255),
    tags TEXT[], -- Array of tags like ['lead', 'customer', 'vip']
    metadata JSONB DEFAULT '{}', -- Flexible JSON field for additional data
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 2. CONTACT LISTS TABLE  
-- Organize contacts into groups/lists
CREATE TABLE contact_lists (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 3. CONTACT LIST MEMBERSHIPS TABLE
-- Many-to-many relationship between contacts and lists
CREATE TABLE contact_list_memberships (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    contact_id UUID REFERENCES contacts(id) ON DELETE CASCADE,
    list_id UUID REFERENCES contact_lists(id) ON DELETE CASCADE,
    added_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(contact_id, list_id)
);

-- 4. CONVERSATIONS TABLE
-- Store conversation histories
CREATE TABLE conversations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    contact_id UUID REFERENCES contacts(id) ON DELETE CASCADE,
    messages JSONB NOT NULL DEFAULT '[]', -- Array of {role, content, timestamp}
    last_message_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Enhanced conversations table with handover tracking
ALTER TABLE conversations ADD COLUMN IF NOT EXISTS handover_requested BOOLEAN DEFAULT FALSE;
ALTER TABLE conversations ADD COLUMN IF NOT EXISTS handover_timestamp TIMESTAMPTZ;
ALTER TABLE conversations ADD COLUMN IF NOT EXISTS handover_reason TEXT;

-- 5. BULK CAMPAIGNS TABLE
-- Track bulk messaging campaigns
CREATE TABLE bulk_campaigns (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255),
    message_content TEXT NOT NULL,
    total_contacts INTEGER NOT NULL,
    successful_sends INTEGER DEFAULT 0,
    failed_sends INTEGER DEFAULT 0,
    status VARCHAR(50) DEFAULT 'pending', -- pending, running, completed, failed
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 6. MESSAGE RESULTS TABLE
-- Individual message delivery results for bulk campaigns
CREATE TABLE message_results (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    campaign_id UUID REFERENCES bulk_campaigns(id) ON DELETE CASCADE,
    contact_id UUID REFERENCES contacts(id) ON DELETE CASCADE,
    success BOOLEAN NOT NULL,
    error_message TEXT,
    sent_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 7. CAMPAIGN ANALYTICS TABLE
-- Store analytics and metrics
CREATE TABLE campaign_analytics (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    campaign_id UUID REFERENCES bulk_campaigns(id) ON DELETE CASCADE,
    metric_name VARCHAR(100) NOT NULL, -- 'delivery_rate', 'response_rate', etc.
    metric_value DECIMAL(10,4) NOT NULL,
    calculated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- INDEXES for better performance
CREATE INDEX idx_contacts_phone_number ON contacts(phone_number);
CREATE INDEX idx_conversations_contact_id ON conversations(contact_id);
CREATE INDEX idx_conversations_last_message_at ON conversations(last_message_at);
CREATE INDEX idx_message_results_campaign_id ON message_results(campaign_id);
CREATE INDEX idx_message_results_contact_id ON message_results(contact_id);
CREATE INDEX idx_bulk_campaigns_status ON bulk_campaigns(status);
CREATE INDEX idx_bulk_campaigns_created_at ON bulk_campaigns(created_at);

-- Enhanced leads table with handover support
ALTER TABLE leads ADD COLUMN IF NOT EXISTS handover_requested BOOLEAN DEFAULT FALSE;
ALTER TABLE leads ADD COLUMN IF NOT EXISTS handover_trigger TEXT;
ALTER TABLE leads ADD COLUMN IF NOT EXISTS handover_timestamp TIMESTAMPTZ;
ALTER TABLE leads ADD COLUMN IF NOT EXISTS priority VARCHAR(20) DEFAULT 'medium';

-- Enhanced tasks table with task types
ALTER TABLE tasks ADD COLUMN IF NOT EXISTS task_type VARCHAR(50) DEFAULT 'general';

-- Enhanced activities table with metadata support
ALTER TABLE activities ADD COLUMN IF NOT EXISTS metadata JSONB;

-- Indexes for better performance on handover queries
CREATE INDEX IF NOT EXISTS idx_conversations_handover ON conversations(handover_requested, handover_timestamp);
CREATE INDEX IF NOT EXISTS idx_leads_handover ON leads(handover_requested, priority);
CREATE INDEX IF NOT EXISTS idx_tasks_type_status ON tasks(task_type, status, due_date);

-- FUNCTIONS for updated_at timestamps
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- TRIGGERS for automatic updated_at timestamps
CREATE TRIGGER update_contacts_updated_at BEFORE UPDATE ON contacts
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_contact_lists_updated_at BEFORE UPDATE ON contact_lists
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_conversations_updated_at BEFORE UPDATE ON conversations
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_bulk_campaigns_updated_at BEFORE UPDATE ON bulk_campaigns
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- RLS (Row Level Security) policies can be added here if needed
-- For now, we'll handle security at the application level

-- SAMPLE DATA (optional - can be removed in production)
INSERT INTO contact_lists (name, description) VALUES 
('General Leads', 'All general inquiries and leads'),
('VIP Customers', 'High-value customers requiring special attention'),
('Newsletter Subscribers', 'Contacts who opted in for regular updates');

-- VIEWS for common queries
CREATE VIEW contact_summary AS
SELECT 
    c.id,
    c.phone_number,
    c.name,
    c.email,
    array_length(c.tags, 1) as tag_count,
    c.created_at,
    COUNT(DISTINCT clm.list_id) as list_memberships,
    MAX(conv.last_message_at) as last_conversation
FROM contacts c
LEFT JOIN contact_list_memberships clm ON c.id = clm.contact_id
LEFT JOIN conversations conv ON c.id = conv.contact_id
GROUP BY c.id, c.phone_number, c.name, c.email, c.tags, c.created_at;

CREATE VIEW campaign_summary AS
SELECT 
    bc.id,
    bc.name,
    bc.message_content,
    bc.total_contacts,
    bc.successful_sends,
    bc.failed_sends,
    bc.status,
    bc.started_at,
    bc.completed_at,
    CASE 
        WHEN bc.total_contacts > 0 
        THEN ROUND((bc.successful_sends::DECIMAL / bc.total_contacts) * 100, 2)
        ELSE 0 
    END as success_rate,
    bc.created_at
FROM bulk_campaigns bc
ORDER BY bc.created_at DESC; 
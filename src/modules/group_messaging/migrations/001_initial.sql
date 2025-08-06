-- Group Messaging Module - Initial Migration
-- ============================================
-- Creates the necessary database tables for the group messaging module

-- Groups table
CREATE TABLE IF NOT EXISTS groups (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    group_jid VARCHAR(255) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    img_url TEXT,
    status VARCHAR(20) DEFAULT 'active',
    member_count INTEGER DEFAULT 0,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create index on group_jid for faster lookups
CREATE INDEX IF NOT EXISTS idx_groups_group_jid ON groups(group_jid);
CREATE INDEX IF NOT EXISTS idx_groups_status ON groups(status);
CREATE INDEX IF NOT EXISTS idx_groups_created_at ON groups(created_at);

-- Scheduled messages table
CREATE TABLE IF NOT EXISTS scheduled_messages (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    message_content TEXT NOT NULL,
    target_type VARCHAR(20) NOT NULL, -- 'group', 'bulk_groups'
    target_ids JSONB NOT NULL, -- Array of group JIDs
    scheduled_time TIMESTAMP WITH TIME ZONE NOT NULL,
    status VARCHAR(20) DEFAULT 'pending', -- 'pending', 'processing', 'sent', 'failed', 'cancelled'
    recurring_pattern VARCHAR(50), -- 'daily', 'weekly', 'monthly', null for one-time
    recurring_end_date TIMESTAMP WITH TIME ZONE,
    campaign_name VARCHAR(255),
    created_by VARCHAR(255),
    executed_at TIMESTAMP WITH TIME ZONE,
    error_message TEXT,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes for scheduled messages
CREATE INDEX IF NOT EXISTS idx_scheduled_messages_status ON scheduled_messages(status);
CREATE INDEX IF NOT EXISTS idx_scheduled_messages_scheduled_time ON scheduled_messages(scheduled_time);
CREATE INDEX IF NOT EXISTS idx_scheduled_messages_target_type ON scheduled_messages(target_type);
CREATE INDEX IF NOT EXISTS idx_scheduled_messages_created_by ON scheduled_messages(created_by);
CREATE INDEX IF NOT EXISTS idx_scheduled_messages_campaign ON scheduled_messages(campaign_name);

-- Group message logs table
CREATE TABLE IF NOT EXISTS group_message_logs (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    group_jid VARCHAR(255) NOT NULL,
    message_content TEXT NOT NULL,
    message_id VARCHAR(255), -- WhatsApp message ID from API response
    message_type VARCHAR(50) DEFAULT 'text', -- 'text', 'image', 'video', 'audio', 'document'
    media_url TEXT, -- URL for media content (if applicable)
    status VARCHAR(20) DEFAULT 'sent', -- 'sent', 'delivered', 'read', 'failed'
    sender_info JSONB DEFAULT '{}', -- Information about who sent the message
    scheduled_message_id UUID REFERENCES scheduled_messages(id), -- Link to scheduled message if applicable
    metadata JSONB DEFAULT '{}',
    sent_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes for group message logs
CREATE INDEX IF NOT EXISTS idx_group_message_logs_group_jid ON group_message_logs(group_jid);
CREATE INDEX IF NOT EXISTS idx_group_message_logs_message_id ON group_message_logs(message_id);
CREATE INDEX IF NOT EXISTS idx_group_message_logs_status ON group_message_logs(status);
CREATE INDEX IF NOT EXISTS idx_group_message_logs_sent_at ON group_message_logs(sent_at);
CREATE INDEX IF NOT EXISTS idx_group_message_logs_scheduled_id ON group_message_logs(scheduled_message_id);

-- Create trigger to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Apply the trigger to tables that have updated_at
DROP TRIGGER IF EXISTS update_groups_updated_at ON groups;
CREATE TRIGGER update_groups_updated_at 
    BEFORE UPDATE ON groups 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_scheduled_messages_updated_at ON scheduled_messages;
CREATE TRIGGER update_scheduled_messages_updated_at 
    BEFORE UPDATE ON scheduled_messages 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Insert some sample data for testing (optional - remove in production)
-- INSERT INTO groups (group_jid, name, member_count) VALUES 
-- ('123456789-987654321@g.us', 'Test Group 1', 5),
-- ('987654321-123456789@g.us', 'Test Group 2', 10);

-- Create a view for easier querying of scheduled messages with group info
CREATE OR REPLACE VIEW scheduled_messages_with_groups AS
SELECT 
    sm.*,
    CASE 
        WHEN sm.target_type = 'group' AND jsonb_array_length(sm.target_ids) = 1
        THEN (
            SELECT g.name 
            FROM groups g 
            WHERE g.group_jid = (sm.target_ids->>0)
        )
        ELSE CONCAT(jsonb_array_length(sm.target_ids), ' groups')
    END as target_display_name
FROM scheduled_messages sm;

-- Grant necessary permissions (adjust as needed for your setup)
-- GRANT SELECT, INSERT, UPDATE, DELETE ON groups TO your_app_user;
-- GRANT SELECT, INSERT, UPDATE, DELETE ON scheduled_messages TO your_app_user;
-- GRANT SELECT, INSERT, UPDATE, DELETE ON group_message_logs TO your_app_user;
-- GRANT SELECT ON scheduled_messages_with_groups TO your_app_user; 
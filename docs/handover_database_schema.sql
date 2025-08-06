-- ============================================================================
-- WhatsApp AI Chatbot - Handover Database Schema
-- ============================================================================
-- Database schema additions for bot-to-human handover functionality
-- Author: Rian Infotech
-- Version: 2.2 (Structured)

-- ============================================================================
-- 1. UPDATE CONVERSATIONS TABLE
-- ============================================================================
-- Add handover-related columns to existing conversations table

ALTER TABLE conversations 
ADD COLUMN IF NOT EXISTS mode VARCHAR(20) DEFAULT 'bot' CHECK (mode IN ('bot', 'pending_human', 'human', 'paused'));

ALTER TABLE conversations 
ADD COLUMN IF NOT EXISTS human_agent_id VARCHAR(255);

ALTER TABLE conversations 
ADD COLUMN IF NOT EXISTS last_human_response_at TIMESTAMPTZ;

-- Add index for performance
CREATE INDEX IF NOT EXISTS idx_conversations_mode ON conversations(mode);
CREATE INDEX IF NOT EXISTS idx_conversations_agent ON conversations(human_agent_id);

-- ============================================================================
-- 2. CREATE HANDOVER_REQUESTS TABLE
-- ============================================================================
-- Track handover requests and their status

CREATE TABLE IF NOT EXISTS handover_requests (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    conversation_id UUID NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
    
    -- Request details
    trigger_type VARCHAR(50) NOT NULL, -- keyword_detected, manual_takeover, escalation, etc.
    trigger_reason TEXT, -- The actual message that triggered handover
    priority VARCHAR(20) DEFAULT 'normal' CHECK (priority IN ('urgent', 'high', 'medium', 'normal')),
    
    -- Analysis data
    analysis JSONB, -- Store analysis results from handover_detector
    
    -- Status tracking
    status VARCHAR(20) DEFAULT 'pending' CHECK (status IN ('pending', 'handled', 'expired', 'cancelled')),
    queue_position INTEGER,
    
    -- Agent assignment
    assigned_agent_id VARCHAR(255),
    handled_by VARCHAR(255),
    
    -- Timestamps
    requested_at TIMESTAMPTZ DEFAULT NOW(),
    assigned_at TIMESTAMPTZ,
    handled_at TIMESTAMPTZ,
    expired_at TIMESTAMPTZ,
    
    -- Metadata
    estimated_wait_time INTEGER, -- in minutes
    department VARCHAR(50), -- technical, billing, sales, support, general
    
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Add indexes for performance
CREATE INDEX IF NOT EXISTS idx_handover_requests_status ON handover_requests(status);
CREATE INDEX IF NOT EXISTS idx_handover_requests_priority ON handover_requests(priority);
CREATE INDEX IF NOT EXISTS idx_handover_requests_conversation ON handover_requests(conversation_id);
CREATE INDEX IF NOT EXISTS idx_handover_requests_agent ON handover_requests(assigned_agent_id);
CREATE INDEX IF NOT EXISTS idx_handover_requests_requested_at ON handover_requests(requested_at);

-- ============================================================================
-- 3. CREATE HUMAN_AGENTS TABLE
-- ============================================================================
-- Track human agents and their availability

CREATE TABLE IF NOT EXISTS human_agents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    agent_id VARCHAR(255) UNIQUE NOT NULL, -- External agent identifier
    
    -- Agent details
    name VARCHAR(255) NOT NULL,
    email VARCHAR(255),
    department VARCHAR(50), -- technical, billing, sales, support, general
    role VARCHAR(50), -- agent, supervisor, manager
    
    -- Availability
    status VARCHAR(20) DEFAULT 'offline' CHECK (status IN ('online', 'busy', 'away', 'offline')),
    max_concurrent_conversations INTEGER DEFAULT 3,
    current_conversations INTEGER DEFAULT 0,
    
    -- Performance metrics
    total_conversations INTEGER DEFAULT 0,
    average_response_time INTEGER, -- in seconds
    customer_satisfaction_score DECIMAL(3,2), -- 0.00 to 5.00
    
    -- Timestamps
    last_online_at TIMESTAMPTZ,
    last_activity_at TIMESTAMPTZ,
    
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Add indexes
CREATE INDEX IF NOT EXISTS idx_human_agents_status ON human_agents(status);
CREATE INDEX IF NOT EXISTS idx_human_agents_department ON human_agents(department);
CREATE INDEX IF NOT EXISTS idx_human_agents_agent_id ON human_agents(agent_id);

-- ============================================================================
-- 4. CREATE HANDOVER_LOGS TABLE
-- ============================================================================
-- Log all handover events for analytics and debugging

CREATE TABLE IF NOT EXISTS handover_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    conversation_id UUID NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
    handover_request_id UUID REFERENCES handover_requests(id) ON DELETE SET NULL,
    
    -- Event details
    event_type VARCHAR(50) NOT NULL, -- mode_change, agent_assigned, conversation_returned, etc.
    from_mode VARCHAR(20),
    to_mode VARCHAR(20),
    
    -- Agent involvement
    agent_id VARCHAR(255),
    agent_name VARCHAR(255),
    
    -- Event data
    event_data JSONB, -- Additional event-specific data
    reason VARCHAR(255), -- Reason for the event
    
    -- Timestamps
    event_timestamp TIMESTAMPTZ DEFAULT NOW(),
    
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Add indexes
CREATE INDEX IF NOT EXISTS idx_handover_logs_conversation ON handover_logs(conversation_id);
CREATE INDEX IF NOT EXISTS idx_handover_logs_event_type ON handover_logs(event_type);
CREATE INDEX IF NOT EXISTS idx_handover_logs_timestamp ON handover_logs(event_timestamp);

-- ============================================================================
-- 5. CREATE HANDOVER_ANALYTICS TABLE
-- ============================================================================
-- Store aggregated analytics for handover performance

CREATE TABLE IF NOT EXISTS handover_analytics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    date DATE NOT NULL,
    
    -- Request metrics
    total_handover_requests INTEGER DEFAULT 0,
    successful_handovers INTEGER DEFAULT 0,
    failed_handovers INTEGER DEFAULT 0,
    expired_handovers INTEGER DEFAULT 0,
    
    -- Timing metrics
    average_wait_time INTEGER, -- in minutes
    average_resolution_time INTEGER, -- in minutes
    max_wait_time INTEGER,
    min_wait_time INTEGER,
    
    -- Priority breakdown
    urgent_requests INTEGER DEFAULT 0,
    high_priority_requests INTEGER DEFAULT 0,
    medium_priority_requests INTEGER DEFAULT 0,
    normal_requests INTEGER DEFAULT 0,
    
    -- Department breakdown
    technical_requests INTEGER DEFAULT 0,
    billing_requests INTEGER DEFAULT 0,
    sales_requests INTEGER DEFAULT 0,
    support_requests INTEGER DEFAULT 0,
    general_requests INTEGER DEFAULT 0,
    
    -- Agent metrics
    active_agents INTEGER DEFAULT 0,
    total_agent_hours DECIMAL(10,2) DEFAULT 0,
    
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    
    UNIQUE(date)
);

-- Add index
CREATE INDEX IF NOT EXISTS idx_handover_analytics_date ON handover_analytics(date);

-- ============================================================================
-- 6. CREATE TRIGGERS FOR AUTOMATIC UPDATES
-- ============================================================================

-- Update conversations.updated_at when mode changes
CREATE OR REPLACE FUNCTION update_conversation_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_conversation_timestamp
    BEFORE UPDATE ON conversations
    FOR EACH ROW
    EXECUTE FUNCTION update_conversation_timestamp();

-- Update handover_requests.updated_at
CREATE TRIGGER trigger_update_handover_request_timestamp
    BEFORE UPDATE ON handover_requests
    FOR EACH ROW
    EXECUTE FUNCTION update_conversation_timestamp();

-- Update human_agents.updated_at
CREATE TRIGGER trigger_update_human_agent_timestamp
    BEFORE UPDATE ON human_agents
    FOR EACH ROW
    EXECUTE FUNCTION update_conversation_timestamp();

-- ============================================================================
-- 7. INSERT SAMPLE HUMAN AGENTS
-- ============================================================================
-- Add some sample human agents for testing

INSERT INTO human_agents (agent_id, name, email, department, role, status) VALUES
('agent_001', 'Sarah Johnson', 'sarah@rianinfotech.com', 'support', 'agent', 'offline'),
('agent_002', 'Mike Chen', 'mike@rianinfotech.com', 'technical', 'agent', 'offline'),
('agent_003', 'Lisa Rodriguez', 'lisa@rianinfotech.com', 'sales', 'agent', 'offline'),
('supervisor_001', 'David Kumar', 'david@rianinfotech.com', 'general', 'supervisor', 'offline')
ON CONFLICT (agent_id) DO NOTHING;

-- ============================================================================
-- 8. CREATE VIEWS FOR EASY QUERYING
-- ============================================================================

-- View for active handover queue
CREATE OR REPLACE VIEW handover_queue AS
SELECT 
    hr.id,
    hr.priority,
    hr.trigger_type,
    hr.requested_at,
    hr.estimated_wait_time,
    hr.department,
    c.id as conversation_id,
    cont.name as customer_name,
    cont.phone_number,
    ROW_NUMBER() OVER (ORDER BY 
        CASE hr.priority 
            WHEN 'urgent' THEN 1 
            WHEN 'high' THEN 2 
            WHEN 'medium' THEN 3 
            ELSE 4 
        END,
        hr.requested_at
    ) as queue_position
FROM handover_requests hr
JOIN conversations c ON hr.conversation_id = c.id
JOIN contacts cont ON c.contact_id = cont.id
WHERE hr.status = 'pending'
ORDER BY queue_position;

-- View for agent workload
CREATE OR REPLACE VIEW agent_workload AS
SELECT 
    ha.agent_id,
    ha.name,
    ha.department,
    ha.status,
    ha.current_conversations,
    ha.max_concurrent_conversations,
    (ha.max_concurrent_conversations - ha.current_conversations) as available_capacity,
    COUNT(c.id) as active_conversations
FROM human_agents ha
LEFT JOIN conversations c ON c.human_agent_id = ha.agent_id AND c.mode = 'human'
GROUP BY ha.agent_id, ha.name, ha.department, ha.status, ha.current_conversations, ha.max_concurrent_conversations;

-- ============================================================================
-- 9. GRANT PERMISSIONS
-- ============================================================================
-- Grant necessary permissions (adjust based on your setup)

-- GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO your_app_user;
-- GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO your_app_user;

-- ============================================================================
-- SCHEMA COMPLETE
-- ============================================================================
-- This schema provides:
-- 1. Conversation mode tracking
-- 2. Handover request management
-- 3. Human agent management
-- 4. Event logging
-- 5. Analytics and reporting
-- 6. Queue management views
-- 7. Performance monitoring 
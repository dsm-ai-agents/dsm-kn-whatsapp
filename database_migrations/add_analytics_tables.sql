-- Phase 3A: Smart Business Intelligence & Analytics Tables
-- Migration to add comprehensive analytics and tracking capabilities

-- 1. Conversation Analytics Table
CREATE TABLE IF NOT EXISTS conversation_analytics (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    contact_id UUID REFERENCES contacts(id) ON DELETE CASCADE,
    phone_number VARCHAR(50) NOT NULL,
    session_id UUID DEFAULT uuid_generate_v4(),
    
    -- Message Analytics
    message_count INTEGER DEFAULT 0,
    user_messages INTEGER DEFAULT 0,
    bot_messages INTEGER DEFAULT 0,
    avg_response_time_seconds DECIMAL(10,2),
    
    -- Engagement Metrics
    session_duration_seconds INTEGER,
    engagement_score DECIMAL(5,2), -- 0-100 score
    interaction_quality VARCHAR(20) DEFAULT 'medium', -- low, medium, high
    
    -- Journey Tracking
    journey_start_stage VARCHAR(50),
    journey_end_stage VARCHAR(50),
    journey_progression_count INTEGER DEFAULT 0,
    
    -- Business Metrics
    lead_score DECIMAL(5,2) DEFAULT 0, -- 0-100 score
    conversion_probability DECIMAL(5,2) DEFAULT 0, -- 0-100 percentage
    business_intent_detected BOOLEAN DEFAULT FALSE,
    pricing_discussed BOOLEAN DEFAULT FALSE,
    demo_requested BOOLEAN DEFAULT FALSE,
    
    -- Timing Analytics
    session_start_time TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    session_end_time TIMESTAMP WITH TIME ZONE,
    last_activity_time TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 2. Message Analytics Table (detailed per-message tracking)
CREATE TABLE IF NOT EXISTS message_analytics (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    conversation_analytics_id UUID REFERENCES conversation_analytics(id) ON DELETE CASCADE,
    contact_id UUID REFERENCES contacts(id) ON DELETE CASCADE,
    
    -- Message Details
    message_id VARCHAR(100) NOT NULL,
    message_role VARCHAR(20) NOT NULL, -- user, assistant
    message_content TEXT,
    message_length INTEGER,
    
    -- AI Processing Analytics
    ai_handler_used VARCHAR(50), -- enhanced, rag, basic
    rag_documents_retrieved INTEGER DEFAULT 0,
    rag_query_time_ms INTEGER,
    personalization_level VARCHAR(20),
    response_strategy VARCHAR(50),
    communication_style VARCHAR(50),
    
    -- Intent & Classification
    detected_intents JSONB DEFAULT '[]'::jsonb,
    business_category VARCHAR(50), -- pricing, technical, support, sales
    urgency_level VARCHAR(20) DEFAULT 'medium',
    sentiment_score DECIMAL(3,2), -- -1 to 1
    
    -- Performance Metrics
    processing_time_ms INTEGER,
    token_count INTEGER,
    cost_estimate DECIMAL(10,4),
    
    -- Timing
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 3. Lead Scoring Analytics
CREATE TABLE IF NOT EXISTS lead_scoring_analytics (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    contact_id UUID REFERENCES contacts(id) ON DELETE CASCADE,
    phone_number VARCHAR(50) NOT NULL,
    
    -- Lead Score Components
    overall_score DECIMAL(5,2) DEFAULT 0, -- 0-100
    engagement_score DECIMAL(5,2) DEFAULT 0,
    intent_score DECIMAL(5,2) DEFAULT 0,
    fit_score DECIMAL(5,2) DEFAULT 0,
    timing_score DECIMAL(5,2) DEFAULT 0,
    
    -- Behavioral Indicators
    messages_sent INTEGER DEFAULT 0,
    questions_asked INTEGER DEFAULT 0,
    pricing_inquiries INTEGER DEFAULT 0,
    technical_questions INTEGER DEFAULT 0,
    demo_requests INTEGER DEFAULT 0,
    
    -- Engagement Patterns
    response_speed_avg DECIMAL(10,2), -- seconds
    session_frequency DECIMAL(5,2), -- sessions per day
    conversation_depth DECIMAL(5,2), -- avg messages per session
    
    -- Business Indicators
    company_size_indicator VARCHAR(50),
    industry_match_score DECIMAL(5,2),
    budget_indicators JSONB DEFAULT '[]'::jsonb,
    decision_maker_signals BOOLEAN DEFAULT FALSE,
    
    -- Conversion Tracking
    conversion_stage VARCHAR(50) DEFAULT 'awareness',
    conversion_probability DECIMAL(5,2) DEFAULT 0,
    next_best_action VARCHAR(100),
    
    -- Timing
    last_calculated TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 4. Business Intelligence Metrics
CREATE TABLE IF NOT EXISTS business_intelligence_metrics (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    metric_date DATE DEFAULT CURRENT_DATE,
    
    -- Daily Conversation Metrics
    total_conversations INTEGER DEFAULT 0,
    new_conversations INTEGER DEFAULT 0,
    returning_conversations INTEGER DEFAULT 0,
    
    -- Message Volume
    total_messages INTEGER DEFAULT 0,
    user_messages INTEGER DEFAULT 0,
    bot_messages INTEGER DEFAULT 0,
    
    -- Response Performance
    avg_response_time_seconds DECIMAL(10,2),
    successful_responses INTEGER DEFAULT 0,
    failed_responses INTEGER DEFAULT 0,
    
    -- Lead Generation
    leads_generated INTEGER DEFAULT 0,
    qualified_leads INTEGER DEFAULT 0,
    demo_requests INTEGER DEFAULT 0,
    pricing_inquiries INTEGER DEFAULT 0,
    
    -- Journey Analytics
    discovery_stage_contacts INTEGER DEFAULT 0,
    interest_stage_contacts INTEGER DEFAULT 0,
    evaluation_stage_contacts INTEGER DEFAULT 0,
    decision_stage_contacts INTEGER DEFAULT 0,
    
    -- AI Performance
    rag_queries INTEGER DEFAULT 0,
    enhanced_responses INTEGER DEFAULT 0,
    fallback_responses INTEGER DEFAULT 0,
    
    -- Business Metrics
    conversion_rate DECIMAL(5,2) DEFAULT 0,
    avg_lead_score DECIMAL(5,2) DEFAULT 0,
    customer_satisfaction_score DECIMAL(3,2) DEFAULT 0,
    
    -- Costs & ROI
    estimated_ai_costs DECIMAL(10,2) DEFAULT 0,
    estimated_savings DECIMAL(10,2) DEFAULT 0,
    roi_estimate DECIMAL(10,2) DEFAULT 0,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Ensure one record per date
    UNIQUE(metric_date)
);

-- 5. Performance Tracking Table
CREATE TABLE IF NOT EXISTS performance_tracking (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    
    -- System Performance
    endpoint VARCHAR(100) NOT NULL,
    operation_type VARCHAR(50) NOT NULL,
    execution_time_ms INTEGER NOT NULL,
    memory_usage_mb DECIMAL(10,2),
    cpu_usage_percent DECIMAL(5,2),
    
    -- AI Performance
    model_used VARCHAR(50),
    tokens_processed INTEGER,
    cost_incurred DECIMAL(10,4),
    
    -- Success/Failure Tracking
    status VARCHAR(20) NOT NULL, -- success, error, timeout
    error_message TEXT,
    error_type VARCHAR(50),
    
    -- Context
    contact_id UUID,
    session_id UUID,
    request_metadata JSONB DEFAULT '{}'::jsonb,
    
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create Indexes for Performance
CREATE INDEX IF NOT EXISTS idx_conversation_analytics_phone ON conversation_analytics(phone_number);
CREATE INDEX IF NOT EXISTS idx_conversation_analytics_session ON conversation_analytics(session_id);
CREATE INDEX IF NOT EXISTS idx_conversation_analytics_date ON conversation_analytics(session_start_time);

CREATE INDEX IF NOT EXISTS idx_message_analytics_contact ON message_analytics(contact_id);
CREATE INDEX IF NOT EXISTS idx_message_analytics_timestamp ON message_analytics(timestamp);
CREATE INDEX IF NOT EXISTS idx_message_analytics_handler ON message_analytics(ai_handler_used);

CREATE INDEX IF NOT EXISTS idx_lead_scoring_phone ON lead_scoring_analytics(phone_number);
CREATE INDEX IF NOT EXISTS idx_lead_scoring_score ON lead_scoring_analytics(overall_score);
CREATE INDEX IF NOT EXISTS idx_lead_scoring_updated ON lead_scoring_analytics(updated_at);

CREATE INDEX IF NOT EXISTS idx_bi_metrics_date ON business_intelligence_metrics(metric_date);

CREATE INDEX IF NOT EXISTS idx_performance_endpoint ON performance_tracking(endpoint);
CREATE INDEX IF NOT EXISTS idx_performance_timestamp ON performance_tracking(timestamp);
CREATE INDEX IF NOT EXISTS idx_performance_status ON performance_tracking(status);

-- Create Functions for Auto-updating timestamps
CREATE OR REPLACE FUNCTION update_analytics_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Add triggers for updated_at columns
DO $$ BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_trigger WHERE tgname = 'set_conversation_analytics_updated_at') THEN
        CREATE TRIGGER set_conversation_analytics_updated_at
        BEFORE UPDATE ON conversation_analytics
        FOR EACH ROW
        EXECUTE FUNCTION update_analytics_updated_at_column();
    END IF;
END $$;

DO $$ BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_trigger WHERE tgname = 'set_lead_scoring_analytics_updated_at') THEN
        CREATE TRIGGER set_lead_scoring_analytics_updated_at
        BEFORE UPDATE ON lead_scoring_analytics
        FOR EACH ROW
        EXECUTE FUNCTION update_analytics_updated_at_column();
    END IF;
END $$;

DO $$ BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_trigger WHERE tgname = 'set_bi_metrics_updated_at') THEN
        CREATE TRIGGER set_bi_metrics_updated_at
        BEFORE UPDATE ON business_intelligence_metrics
        FOR EACH ROW
        EXECUTE FUNCTION update_analytics_updated_at_column();
    END IF;
END $$;

-- Add Comments for Documentation
COMMENT ON TABLE conversation_analytics IS 'Tracks comprehensive analytics for each conversation session';
COMMENT ON TABLE message_analytics IS 'Detailed per-message analytics and AI performance tracking';
COMMENT ON TABLE lead_scoring_analytics IS 'Advanced lead scoring and conversion probability tracking';
COMMENT ON TABLE business_intelligence_metrics IS 'Daily aggregated business intelligence metrics';
COMMENT ON TABLE performance_tracking IS 'System and AI performance monitoring';

COMMENT ON COLUMN conversation_analytics.engagement_score IS 'Calculated engagement score from 0-100 based on interaction patterns';
COMMENT ON COLUMN lead_scoring_analytics.overall_score IS 'Composite lead score from 0-100 combining multiple factors';
COMMENT ON COLUMN business_intelligence_metrics.conversion_rate IS 'Daily conversion rate from leads to qualified prospects';
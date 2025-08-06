-- Enhanced Personalization Fields Migration
-- Safe migration that adds new fields without affecting existing data

-- Add journey tracking fields
ALTER TABLE contacts 
ADD COLUMN IF NOT EXISTS journey_stage VARCHAR(50) DEFAULT 'discovery',
ADD COLUMN IF NOT EXISTS conversation_count INTEGER DEFAULT 0,
ADD COLUMN IF NOT EXISTS first_contact_date TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
ADD COLUMN IF NOT EXISTS total_interactions INTEGER DEFAULT 0;

-- Add interest and behavior tracking (using JSONB for flexibility)
ALTER TABLE contacts 
ADD COLUMN IF NOT EXISTS topics_discussed JSONB DEFAULT '[]'::jsonb,
ADD COLUMN IF NOT EXISTS questions_asked JSONB DEFAULT '[]'::jsonb,
ADD COLUMN IF NOT EXISTS pain_points_mentioned JSONB DEFAULT '[]'::jsonb,
ADD COLUMN IF NOT EXISTS goals_expressed JSONB DEFAULT '[]'::jsonb;

-- Add behavioral patterns
ALTER TABLE contacts 
ADD COLUMN IF NOT EXISTS response_time_pattern VARCHAR(20) DEFAULT 'unknown',
ADD COLUMN IF NOT EXISTS engagement_level VARCHAR(20) DEFAULT 'medium',
ADD COLUMN IF NOT EXISTS information_preference VARCHAR(20) DEFAULT 'medium',
ADD COLUMN IF NOT EXISTS decision_making_style VARCHAR(20) DEFAULT 'unknown';

-- Add enhanced sales context
ALTER TABLE contacts 
ADD COLUMN IF NOT EXISTS budget_range VARCHAR(50),
ADD COLUMN IF NOT EXISTS timeline VARCHAR(50),
ADD COLUMN IF NOT EXISTS decision_maker BOOLEAN DEFAULT FALSE,
ADD COLUMN IF NOT EXISTS competitors_mentioned JSONB DEFAULT '[]'::jsonb;

-- Add personalization flags
ALTER TABLE contacts 
ADD COLUMN IF NOT EXISTS prefers_examples BOOLEAN DEFAULT TRUE,
ADD COLUMN IF NOT EXISTS industry_focus VARCHAR(100),
ADD COLUMN IF NOT EXISTS company_size VARCHAR(20),
ADD COLUMN IF NOT EXISTS technical_level VARCHAR(20) DEFAULT 'business_user';

-- Create conversation state table for tracking ongoing conversations
CREATE TABLE IF NOT EXISTS conversation_states (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    contact_id UUID REFERENCES contacts(id) ON DELETE CASCADE,
    phone_number VARCHAR(50) NOT NULL,
    current_topic VARCHAR(100),
    unresolved_questions JSONB DEFAULT '[]'::jsonb,
    action_items JSONB DEFAULT '[]'::jsonb,
    context_continuity JSONB DEFAULT '{}'::jsonb,
    emotional_context JSONB DEFAULT '{}'::jsonb,
    last_message_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_contacts_journey_stage ON contacts(journey_stage);
CREATE INDEX IF NOT EXISTS idx_contacts_engagement_level ON contacts(engagement_level);
CREATE INDEX IF NOT EXISTS idx_conversation_states_contact_id ON conversation_states(contact_id);
CREATE INDEX IF NOT EXISTS idx_conversation_states_phone_number ON conversation_states(phone_number);

-- Create trigger to update conversation_states updated_at
CREATE OR REPLACE FUNCTION update_conversation_states_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER IF NOT EXISTS update_conversation_states_updated_at_trigger
    BEFORE UPDATE ON conversation_states
    FOR EACH ROW
    EXECUTE FUNCTION update_conversation_states_updated_at();

-- Add comments for documentation
COMMENT ON COLUMN contacts.journey_stage IS 'User journey stage: discovery, interest, evaluation, decision';
COMMENT ON COLUMN contacts.conversation_count IS 'Total number of conversations with this contact';
COMMENT ON COLUMN contacts.engagement_level IS 'User engagement level: high, medium, low';
COMMENT ON TABLE conversation_states IS 'Tracks ongoing conversation context and state for personalization';
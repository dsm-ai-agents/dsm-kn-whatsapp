-- ============================================================================
-- Lead Qualification System Database Migration
-- ============================================================================
-- Creates table for logging AI lead qualification analysis and results
-- Run this migration after the handover system migration

-- Create lead qualification log table
CREATE TABLE IF NOT EXISTS lead_qualification_log (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    created_at timestamp with time zone DEFAULT now(),
    message_text text NOT NULL,
    is_qualified_lead boolean NOT NULL,
    confidence_score real NOT NULL,
    lead_quality varchar(20) NOT NULL, -- HIGH, MEDIUM, LOW, NOT_QUALIFIED
    lead_score integer NOT NULL,
    business_indicators text[] DEFAULT '{}',
    buying_signals text[] DEFAULT '{}',
    recommended_action varchar(50) NOT NULL, -- discovery_call, nurture, qualify_further, none
    final_decision boolean NOT NULL, -- Whether lead was actually qualified after all checks
    reason text NOT NULL,
    model_used varchar(50) NOT NULL,
    phone_number varchar(20), -- Optional: to track which customer (add if needed)
    
    -- Indexes for analytics
    CONSTRAINT valid_lead_quality CHECK (lead_quality IN ('HIGH', 'MEDIUM', 'LOW', 'NOT_QUALIFIED')),
    CONSTRAINT valid_recommended_action CHECK (recommended_action IN ('discovery_call', 'nurture', 'qualify_further', 'none'))
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_lead_qualification_log_created_at ON lead_qualification_log(created_at);
CREATE INDEX IF NOT EXISTS idx_lead_qualification_log_is_qualified ON lead_qualification_log(is_qualified_lead);
CREATE INDEX IF NOT EXISTS idx_lead_qualification_log_lead_quality ON lead_qualification_log(lead_quality);
CREATE INDEX IF NOT EXISTS idx_lead_qualification_log_final_decision ON lead_qualification_log(final_decision);

-- Add new columns to existing tables for lead qualification tracking
ALTER TABLE contacts ADD COLUMN IF NOT EXISTS discovery_call_requested boolean DEFAULT false;
ALTER TABLE contacts ADD COLUMN IF NOT EXISTS last_qualification_date timestamp with time zone;

ALTER TABLE lead_details ADD COLUMN IF NOT EXISTS qualification_trigger text;
ALTER TABLE lead_details ADD COLUMN IF NOT EXISTS qualification_timestamp timestamp with time zone;
ALTER TABLE lead_details ADD COLUMN IF NOT EXISTS business_indicators text[] DEFAULT '{}';
ALTER TABLE lead_details ADD COLUMN IF NOT EXISTS buying_signals text[] DEFAULT '{}';
ALTER TABLE lead_details ADD COLUMN IF NOT EXISTS lead_quality varchar(20);
ALTER TABLE lead_details ADD COLUMN IF NOT EXISTS ai_confidence real;
ALTER TABLE lead_details ADD COLUMN IF NOT EXISTS discovery_call_requested boolean DEFAULT false;

-- Add constraint for lead quality
ALTER TABLE lead_details ADD CONSTRAINT IF NOT EXISTS valid_lead_quality_details 
    CHECK (lead_quality IS NULL OR lead_quality IN ('HIGH', 'MEDIUM', 'LOW', 'NOT_QUALIFIED'));

-- Create view for lead qualification analytics
CREATE OR REPLACE VIEW lead_qualification_analytics AS
SELECT 
    DATE(created_at) as qualification_date,
    lead_quality,
    COUNT(*) as total_analyzed,
    SUM(CASE WHEN is_qualified_lead THEN 1 ELSE 0 END) as ai_qualified_count,
    SUM(CASE WHEN final_decision THEN 1 ELSE 0 END) as final_qualified_count,
    AVG(confidence_score) as avg_confidence,
    AVG(lead_score) as avg_lead_score,
    SUM(CASE WHEN recommended_action = 'discovery_call' THEN 1 ELSE 0 END) as discovery_call_recommendations
FROM lead_qualification_log
GROUP BY DATE(created_at), lead_quality
ORDER BY qualification_date DESC, lead_quality;

-- Create view for qualified leads summary
CREATE OR REPLACE VIEW qualified_leads_summary AS
SELECT 
    c.phone_number,
    c.name,
    c.lead_score,
    c.lead_status,
    c.discovery_call_requested,
    ld.qualification_trigger,
    ld.qualification_timestamp,
    ld.lead_quality,
    ld.ai_confidence,
    ld.business_indicators,
    ld.buying_signals,
    -- Get latest activity
    (SELECT description FROM activities WHERE contact_id = c.id AND activity_type = 'calendly_invitation' ORDER BY created_at DESC LIMIT 1) as latest_calendly_activity,
    (SELECT created_at FROM activities WHERE contact_id = c.id AND activity_type = 'calendly_invitation' ORDER BY created_at DESC LIMIT 1) as calendly_sent_at
FROM contacts c
LEFT JOIN lead_details ld ON c.id = ld.contact_id
WHERE c.discovery_call_requested = true OR ld.discovery_call_requested = true
ORDER BY ld.qualification_timestamp DESC NULLS LAST;

-- Insert sample configuration data (optional)
COMMENT ON TABLE lead_qualification_log IS 'Logs all AI lead qualification analysis attempts with metadata for monitoring and improvement';
COMMENT ON TABLE qualified_leads_summary IS 'View of all qualified leads with discovery call information';

-- Grant necessary permissions (adjust as needed for your setup)
-- GRANT SELECT, INSERT ON lead_qualification_log TO your_app_role;
-- GRANT SELECT ON lead_qualification_analytics TO your_analytics_role;
-- GRANT SELECT ON qualified_leads_summary TO your_app_role;

COMMIT; 
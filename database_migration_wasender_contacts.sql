-- Database Migration: Add WASender Contact Fields
-- This migration adds fields to support WASender contact synchronization

-- Add WASender-specific fields to contacts table
ALTER TABLE contacts 
ADD COLUMN IF NOT EXISTS verified_name TEXT,
ADD COLUMN IF NOT EXISTS profile_image_url TEXT,
ADD COLUMN IF NOT EXISTS whatsapp_status TEXT,
ADD COLUMN IF NOT EXISTS is_business_account BOOLEAN DEFAULT FALSE,
ADD COLUMN IF NOT EXISTS last_updated_from_wasender TIMESTAMP WITH TIME ZONE,
ADD COLUMN IF NOT EXISTS wasender_sync_status TEXT DEFAULT 'not_synced',
ADD COLUMN IF NOT EXISTS wasender_jid TEXT,
ADD COLUMN IF NOT EXISTS raw_wasender_data JSONB;

-- Create index for faster WASender sync queries
CREATE INDEX IF NOT EXISTS idx_contacts_wasender_sync_status ON contacts(wasender_sync_status);
CREATE INDEX IF NOT EXISTS idx_contacts_wasender_jid ON contacts(wasender_jid);
CREATE INDEX IF NOT EXISTS idx_contacts_last_updated_wasender ON contacts(last_updated_from_wasender);

-- Create a function to track WASender sync statistics
CREATE OR REPLACE FUNCTION get_wasender_sync_stats()
RETURNS TABLE(
    total_contacts BIGINT,
    synced_contacts BIGINT,
    contacts_with_names BIGINT,
    contacts_with_verified_names BIGINT,
    business_accounts BIGINT,
    last_sync_time TIMESTAMP WITH TIME ZONE
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        COUNT(*) as total_contacts,
        COUNT(*) FILTER (WHERE wasender_sync_status = 'synced') as synced_contacts,
        COUNT(*) FILTER (WHERE name IS NOT NULL AND name != phone_number) as contacts_with_names,
        COUNT(*) FILTER (WHERE verified_name IS NOT NULL) as contacts_with_verified_names,
        COUNT(*) FILTER (WHERE is_business_account = TRUE) as business_accounts,
        MAX(last_updated_from_wasender) as last_sync_time
    FROM contacts;
END;
$$ LANGUAGE plpgsql;

-- Create a view for enriched contact information
CREATE OR REPLACE VIEW contacts_enriched AS
SELECT 
    c.*,
    CASE 
        WHEN c.verified_name IS NOT NULL THEN c.verified_name
        WHEN c.name IS NOT NULL AND c.name != c.phone_number THEN c.name
        ELSE NULL
    END as display_name,
    CASE 
        WHEN c.wasender_sync_status = 'synced' THEN TRUE
        ELSE FALSE
    END as is_wasender_synced,
    CASE 
        WHEN c.profile_image_url IS NOT NULL THEN TRUE
        ELSE FALSE
    END as has_profile_image
FROM contacts c;

-- Add comment to document the migration
COMMENT ON TABLE contacts IS 'Contacts table with WASender API integration fields added';
COMMENT ON COLUMN contacts.verified_name IS 'Verified business name from WhatsApp';
COMMENT ON COLUMN contacts.profile_image_url IS 'Profile picture URL from WhatsApp';
COMMENT ON COLUMN contacts.whatsapp_status IS 'WhatsApp status message';
COMMENT ON COLUMN contacts.is_business_account IS 'Whether this is a WhatsApp Business account';
COMMENT ON COLUMN contacts.wasender_sync_status IS 'Status of WASender synchronization';
COMMENT ON COLUMN contacts.wasender_jid IS 'Original WhatsApp JID from WASender';
COMMENT ON COLUMN contacts.raw_wasender_data IS 'Raw contact data from WASender API';

-- Migration completed successfully
SELECT 'WASender contact fields migration completed successfully' as status; 
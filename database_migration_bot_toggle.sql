-- WhatsApp AI Chatbot - Bot Toggle Feature Migration
-- ===================================================
-- Adds bot_enabled field to conversations table for controlling
-- automatic bot responses per conversation.
--
-- Author: Rian Infotech
-- Date: 2025-06-12

-- Add bot_enabled column to conversations table
ALTER TABLE conversations 
ADD COLUMN IF NOT EXISTS bot_enabled BOOLEAN DEFAULT true;

-- Add comment for documentation
COMMENT ON COLUMN conversations.bot_enabled IS 'Controls whether the bot should automatically respond to messages in this conversation. When false, human agents handle the conversation.';

-- Create index for performance
CREATE INDEX IF NOT EXISTS idx_conversations_bot_enabled 
ON conversations(bot_enabled);

-- Update any existing conversations to have bot enabled by default
UPDATE conversations 
SET bot_enabled = true 
WHERE bot_enabled IS NULL;

-- Optional: Create audit table for bot toggle actions
CREATE TABLE IF NOT EXISTS bot_toggle_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    conversation_id UUID REFERENCES conversations(id) ON DELETE CASCADE,
    previous_status BOOLEAN,
    new_status BOOLEAN,
    reason TEXT,
    toggled_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Add index for audit logs
CREATE INDEX IF NOT EXISTS idx_bot_toggle_logs_conversation 
ON bot_toggle_logs(conversation_id);

CREATE INDEX IF NOT EXISTS idx_bot_toggle_logs_date 
ON bot_toggle_logs(toggled_at);

-- Add comment for audit table
COMMENT ON TABLE bot_toggle_logs IS 'Audit trail for bot enable/disable toggle actions';

-- Verify the changes
SELECT 
    table_name,
    column_name,
    data_type,
    is_nullable,
    column_default
FROM information_schema.columns 
WHERE table_name = 'conversations' 
  AND column_name = 'bot_enabled';

-- Show sample data to verify
SELECT 
    id,
    bot_enabled,
    created_at,
    updated_at
FROM conversations 
LIMIT 5; 
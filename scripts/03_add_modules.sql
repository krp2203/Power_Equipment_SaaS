-- Add Modules support for Add-On architecture
ALTER TABLE organization ADD COLUMN IF NOT EXISTS modules JSONB DEFAULT '{}';
ALTER TABLE organization ADD COLUMN IF NOT EXISTS theme_config JSONB DEFAULT '{}';

-- Add Dealer specific social and labor fields if missing
ALTER TABLE dealer ADD COLUMN IF NOT EXISTS labor_rate NUMERIC(10, 2);

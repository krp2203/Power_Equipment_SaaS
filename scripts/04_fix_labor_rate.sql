-- Fix labor_rate typo/type mismatch
-- It was created as VARCHAR but should be NUMERIC(10,2)

-- First, we need to handle any empty strings or non-numeric values if they exist.
-- This simple cast assumes data is clean or NULL. 
-- If 'labor_rate' contains '' (empty string), NULLIF will treat it as NULL.

ALTER TABLE dealer 
ALTER COLUMN labor_rate TYPE NUMERIC(10, 2) 
USING NULLIF(labor_rate, '')::numeric;

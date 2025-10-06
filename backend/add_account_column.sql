-- Add missing account_number_masked column to accounts table
-- This fixes the issue where account creation fails due to missing column

ALTER TABLE accounts ADD COLUMN IF NOT EXISTS account_number_masked VARCHAR(50);

-- Also ensure institution_name exists (it should already be there based on the model)
-- ALTER TABLE accounts ADD COLUMN IF NOT EXISTS institution_name VARCHAR(255);

-- Add comment for documentation
COMMENT ON COLUMN accounts.account_number_masked IS 'Masked account number for display purposes (e.g., ****1234)';
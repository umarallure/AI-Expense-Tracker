-- Complete accounts table schema migration
-- Add all missing columns to match the Account model

-- Basic account information (should already exist)
ALTER TABLE accounts ADD COLUMN IF NOT EXISTS account_name VARCHAR(255) NOT NULL;
ALTER TABLE accounts ADD COLUMN IF NOT EXISTS account_type VARCHAR NOT NULL;
ALTER TABLE accounts ADD COLUMN IF NOT EXISTS currency VARCHAR(3) NOT NULL DEFAULT 'USD';

-- Optional descriptive fields
ALTER TABLE accounts ADD COLUMN IF NOT EXISTS description TEXT;
ALTER TABLE accounts ADD COLUMN IF NOT EXISTS institution_name VARCHAR(255);
ALTER TABLE accounts ADD COLUMN IF NOT EXISTS account_number_masked VARCHAR(50);
ALTER TABLE accounts ADD COLUMN IF NOT EXISTS routing_number VARCHAR(50);

-- Financial fields
ALTER TABLE accounts ADD COLUMN IF NOT EXISTS current_balance NUMERIC(15, 2) NOT NULL DEFAULT 0.00;
ALTER TABLE accounts ADD COLUMN IF NOT EXISTS available_balance NUMERIC(15, 2);
ALTER TABLE accounts ADD COLUMN IF NOT EXISTS credit_limit NUMERIC(15, 2);
ALTER TABLE accounts ADD COLUMN IF NOT EXISTS interest_rate NUMERIC(7, 4);
ALTER TABLE accounts ADD COLUMN IF NOT EXISTS minimum_payment NUMERIC(15, 2);
ALTER TABLE accounts ADD COLUMN IF NOT EXISTS due_date INTEGER;

-- Account settings
ALTER TABLE accounts ADD COLUMN IF NOT EXISTS is_primary BOOLEAN NOT NULL DEFAULT FALSE;
ALTER TABLE accounts ADD COLUMN IF NOT EXISTS color VARCHAR(7);
ALTER TABLE accounts ADD COLUMN IF NOT EXISTS icon VARCHAR(50);
ALTER TABLE accounts ADD COLUMN IF NOT EXISTS settings JSONB NOT NULL DEFAULT '{}';

-- Status and timestamps
ALTER TABLE accounts ADD COLUMN IF NOT EXISTS is_active BOOLEAN NOT NULL DEFAULT TRUE;
ALTER TABLE accounts ADD COLUMN IF NOT EXISTS created_at TIMESTAMPTZ NOT NULL DEFAULT NOW();
ALTER TABLE accounts ADD COLUMN IF NOT EXISTS updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW();

-- Add comments for documentation
COMMENT ON COLUMN accounts.account_number_masked IS 'Masked account number for display purposes (e.g., ****1234)';
COMMENT ON COLUMN accounts.institution_name IS 'Name of the financial institution';
COMMENT ON COLUMN accounts.routing_number IS 'Bank routing number';
COMMENT ON COLUMN accounts.current_balance IS 'Current account balance';
COMMENT ON COLUMN accounts.available_balance IS 'Available balance (may differ from current for credit cards)';
COMMENT ON COLUMN accounts.credit_limit IS 'Credit limit for credit card accounts';
COMMENT ON COLUMN accounts.interest_rate IS 'Annual interest rate as decimal (e.g., 0.15 for 15%)';
COMMENT ON COLUMN accounts.minimum_payment IS 'Minimum payment amount for credit cards';
COMMENT ON COLUMN accounts.due_date IS 'Day of month when payment is due (1-31)';
COMMENT ON COLUMN accounts.is_primary IS 'Whether this is the primary account for the business';
COMMENT ON COLUMN accounts.color IS 'Hex color code for UI display';
COMMENT ON COLUMN accounts.icon IS 'Icon identifier for UI display';
COMMENT ON COLUMN accounts.settings IS 'Additional account-specific settings as JSON';
COMMENT ON COLUMN accounts.is_active IS 'Whether the account is active';

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_accounts_business_active ON accounts(business_id, is_active);
CREATE INDEX IF NOT EXISTS idx_accounts_type ON accounts(account_type);
CREATE INDEX IF NOT EXISTS idx_accounts_currency ON accounts(currency);
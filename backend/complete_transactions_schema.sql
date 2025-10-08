-- Complete transactions table schema migration
-- Create the transactions table to match the Transaction model

CREATE TABLE IF NOT EXISTS transactions (
    id VARCHAR PRIMARY KEY DEFAULT gen_random_uuid()::text,
    business_id VARCHAR NOT NULL REFERENCES businesses(id),
    account_id VARCHAR NOT NULL REFERENCES accounts(id),
    category_id VARCHAR REFERENCES categories(id),
    user_id VARCHAR NOT NULL,
    amount NUMERIC(15, 2) NOT NULL,
    currency VARCHAR(3) NOT NULL DEFAULT 'USD',
    description VARCHAR NOT NULL,
    date TIMESTAMPTZ NOT NULL,
    receipt_url VARCHAR,
    status VARCHAR NOT NULL DEFAULT 'draft' CHECK (status IN ('draft', 'pending', 'approved', 'rejected')),
    notes TEXT,
    vendor VARCHAR,
    taxes_fees NUMERIC(15, 2),
    payment_method VARCHAR,
    recipient_id VARCHAR,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_transactions_business_id ON transactions(business_id);
CREATE INDEX IF NOT EXISTS idx_transactions_account_id ON transactions(account_id);
CREATE INDEX IF NOT EXISTS idx_transactions_category_id ON transactions(category_id);
CREATE INDEX IF NOT EXISTS idx_transactions_user_id ON transactions(user_id);
CREATE INDEX IF NOT EXISTS idx_transactions_date ON transactions(date);
CREATE INDEX IF NOT EXISTS idx_transactions_status ON transactions(status);
CREATE INDEX IF NOT EXISTS idx_transactions_business_date ON transactions(business_id, date);

-- Add comments for documentation
COMMENT ON TABLE transactions IS 'Financial transactions/expenses for businesses';
COMMENT ON COLUMN transactions.business_id IS 'Reference to the business this transaction belongs to';
COMMENT ON COLUMN transactions.account_id IS 'Reference to the account this transaction affects';
COMMENT ON COLUMN transactions.category_id IS 'Reference to the category this transaction belongs to';
COMMENT ON COLUMN transactions.user_id IS 'Reference to the user who created this transaction';
COMMENT ON COLUMN transactions.amount IS 'Transaction amount';
COMMENT ON COLUMN transactions.currency IS 'Currency code (ISO 4217)';
COMMENT ON COLUMN transactions.description IS 'Transaction description';
COMMENT ON COLUMN transactions.date IS 'Date when the transaction occurred';
COMMENT ON COLUMN transactions.receipt_url IS 'URL to receipt image/document';
COMMENT ON COLUMN transactions.status IS 'Transaction status: draft, pending, approved, rejected';
COMMENT ON COLUMN transactions.notes IS 'Additional notes about the transaction';
COMMENT ON COLUMN transactions.vendor IS 'Vendor or merchant name for the transaction';
COMMENT ON COLUMN transactions.taxes_fees IS 'Taxes and fees associated with the transaction';
COMMENT ON COLUMN transactions.payment_method IS 'Payment method used (cash, credit card, bank transfer, etc.)';
COMMENT ON COLUMN transactions.recipient_id IS 'ID of the recipient for the transaction';
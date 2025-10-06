-- Fix the account_type check constraint to allow all valid account types

-- First, drop the existing restrictive constraint
ALTER TABLE accounts DROP CONSTRAINT IF EXISTS accounts_account_type_check;

-- Add a new constraint that allows all valid account types
ALTER TABLE accounts ADD CONSTRAINT accounts_account_type_check
    CHECK (account_type IN ('checking', 'savings', 'credit_card', 'investment', 'loan', 'cash', 'other'));

-- Add comment
COMMENT ON CONSTRAINT accounts_account_type_check ON accounts IS 'Valid account types for financial accounts';
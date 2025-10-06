"""
Script to check and fix the accounts table schema.
"""
import os
from app.core.config import settings
from supabase import create_client

def main():
    # Create admin client to bypass RLS
    client = create_client(settings.SUPABASE_URL, settings.SUPABASE_SERVICE_KEY)

    try:
        # Try to select from accounts table
        response = client.table('accounts').select('*').limit(1).execute()
        print("✅ Accounts table exists")

        # Check if we have any data
        if response.data:
            print(f"Sample row: {response.data[0]}")
            # Check what columns are present
            columns = list(response.data[0].keys())
            print(f"Columns found: {columns}")

            # Check for missing columns
            required_columns = ['account_number_masked', 'institution_name']
            missing_columns = [col for col in required_columns if col not in columns]

            if missing_columns:
                print(f"❌ Missing columns: {missing_columns}")
                print("Need to add these columns to the database schema")
            else:
                print("✅ All required columns present")
        else:
            print("ℹ️  Accounts table is empty")

    except Exception as e:
        print(f"❌ Error accessing accounts table: {e}")
        if "Could not find the table" in str(e):
            print("Accounts table doesn't exist - need to create it")

if __name__ == "__main__":
    main()
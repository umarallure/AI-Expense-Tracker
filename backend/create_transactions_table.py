"""
Script to create the transactions table in Supabase.
"""
import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.core.config import settings
from supabase import create_client

def main():
    # Create admin client to bypass RLS
    client = create_client(settings.SUPABASE_URL, settings.SUPABASE_SERVICE_KEY)

    # Read the SQL file
    sql_file = 'complete_transactions_schema.sql'
    with open(sql_file, 'r') as f:
        sql = f.read()

    print("Executing transactions table creation SQL...")
    print("SQL to execute:")
    print(sql)

    try:
        # Execute the SQL using rpc
        response = client.rpc('exec_sql', {'sql': sql}).execute()
        print("✅ Successfully created transactions table")
        print(f"Response: {response.data}")
    except Exception as e:
        print(f"❌ Failed to create table: {e}")

        # Try alternative approach - check if table exists
        print("Checking if transactions table already exists...")
        try:
            response = client.table('transactions').select('*').limit(1).execute()
            print("✅ Transactions table already exists")
            print(f"Sample data: {response.data}")
        except Exception as e2:
            print(f"❌ Transactions table does not exist: {e2}")
            print("Manual database migration required in Supabase dashboard")

if __name__ == "__main__":
    main()
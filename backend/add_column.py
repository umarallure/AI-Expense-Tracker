"""
Script to add the missing account_number_masked column to the accounts table.
"""
import os
from app.core.config import settings
from supabase import create_client

def main():
    # Create admin client to bypass RLS
    client = create_client(settings.SUPABASE_URL, settings.SUPABASE_SERVICE_KEY)

    # SQL to add the missing column
    sql = """
    ALTER TABLE accounts ADD COLUMN IF NOT EXISTS account_number_masked VARCHAR(50);
    """

    try:
        # Try to execute raw SQL
        response = client.rpc('exec_sql', {'sql': sql}).execute()
        print("✅ Successfully added account_number_masked column")
        print(f"Response: {response.data}")
    except Exception as e:
        print(f"❌ Failed to add column: {e}")

        # Try alternative approach - use the table API to check if we can infer the schema
        print("Trying alternative approach...")

        # Try to insert a test record with the column to see if it works
        test_data = {
            'business_id': '00000000-0000-0000-0000-000000000000',  # dummy UUID
            'account_name': 'test',
            'account_type': 'checking',
            'currency': 'USD',
            'current_balance': 0.0,
            'account_number_masked': 'test',
            'institution_name': 'test'
        }

        try:
            response = client.table('accounts').insert(test_data).execute()
            print("✅ Column exists or was added successfully")
            # Clean up the test record
            if response.data:
                client.table('accounts').delete().eq('id', response.data[0]['id']).execute()
                print("✅ Test record cleaned up")
        except Exception as e2:
            print(f"❌ Column still missing: {e2}")
            print("Manual database migration required in Supabase dashboard")

if __name__ == "__main__":
    main()
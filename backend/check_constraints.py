"""
Script to check database constraints on the accounts table.
"""
import os
from app.core.config import settings
from supabase import create_client

def main():
    # Create admin client to bypass RLS
    client = create_client(settings.SUPABASE_URL, settings.SUPABASE_SERVICE_KEY)

    try:
        # Try to execute raw SQL to check constraints
        # This might not work, but let's try
        sql = """
        SELECT
            tc.table_name,
            tc.constraint_name,
            tc.constraint_type,
            cc.check_clause
        FROM information_schema.table_constraints tc
        LEFT JOIN information_schema.check_constraints cc
            ON tc.constraint_name = cc.constraint_name
        WHERE tc.table_name = 'accounts'
        AND tc.table_schema = 'public';
        """

        print("Checking database constraints...")
        print("Note: This might fail due to Supabase restrictions")

        # Try a simple insert to see what happens
        test_data = {
            'business_id': '00000000-0000-0000-0000-000000000000',
            'account_name': 'test',
            'account_type': 'checking',
            'currency': 'USD',
            'current_balance': 0.0,
            'account_number_masked': 'test',
            'institution_name': 'test',
            'is_active': True,
            'settings': {}
        }

        try:
            response = client.table('accounts').insert(test_data).execute()
            print("✅ Insert with 'checking' succeeded")
            # Clean up
            if response.data:
                client.table('accounts').delete().eq('id', response.data[0]['id']).execute()
        except Exception as e:
            print(f"❌ Insert with 'checking' failed: {e}")

            # Try with different account types
            for acc_type in ['savings', 'credit_card', 'investment', 'loan', 'cash', 'other']:
                try:
                    test_data['account_type'] = acc_type
                    response = client.table('accounts').insert(test_data).execute()
                    print(f"✅ Insert with '{acc_type}' succeeded")
                    # Clean up
                    if response.data:
                        client.table('accounts').delete().eq('id', response.data[0]['id']).execute()
                    break
                except Exception as e2:
                    print(f"❌ Insert with '{acc_type}' failed: {e2}")

    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    main()
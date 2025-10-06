"""
Script to find what account types are allowed by the database constraint.
"""
import os
from app.core.config import settings
from supabase import create_client

def main():
    # Create admin client to bypass RLS
    client = create_client(settings.SUPABASE_URL, settings.SUPABASE_SERVICE_KEY)

    # Get a real business ID first
    try:
        businesses = client.table('businesses').select('id').limit(1).execute()
        if businesses.data:
            business_id = businesses.data[0]['id']
            print(f"Using business ID: {business_id}")
        else:
            print("❌ No businesses found")
            return
    except Exception as e:
        print(f"❌ Error getting business: {e}")
        return

    # Common account types to try
    account_types = [
        'checking', 'savings', 'credit_card', 'investment', 'loan', 'cash', 'other',
        'bank', 'credit', 'debit', 'asset', 'liability'
    ]

    print("Testing different account types...")

    for acc_type in account_types:
        try:
            test_data = {
                'business_id': business_id,
                'account_name': f'Test {acc_type} Account',
                'account_type': acc_type,
                'currency': 'USD',
                'current_balance': 0.0,
                'account_number_masked': '****1234',
                'institution_name': 'Test Bank',
                'is_active': True,
                'settings': {}
            }

            response = client.table('accounts').insert(test_data).execute()
            print(f"✅ '{acc_type}' is allowed")

            # Clean up
            if response.data:
                client.table('accounts').delete().eq('id', response.data[0]['id']).execute()
            break

        except Exception as e:
            error_msg = str(e)
            if "account_type_check" in error_msg:
                print(f"❌ '{acc_type}' rejected by constraint")
            elif "foreign key" in error_msg:
                print(f"⚠️  '{acc_type}' passed constraint but failed on foreign key (business not found)")
            else:
                print(f"❓ '{acc_type}' failed with unexpected error: {error_msg}")

if __name__ == "__main__":
    main()
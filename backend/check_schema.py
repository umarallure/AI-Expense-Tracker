"""
Script to check the current accounts table schema in Supabase.
"""
import os
from app.core.config import settings
from supabase import create_client

def main():
    # Create admin client to bypass RLS
    client = create_client(settings.SUPABASE_URL, settings.SUPABASE_SERVICE_KEY)

    # Query the accounts table schema
    response = client.table('information_schema.columns').select('column_name, data_type, is_nullable').eq('table_name', 'accounts').eq('table_schema', 'public').execute()

    print('Current accounts table columns:')
    for col in response.data:
        print(f'  {col["column_name"]}: {col["data_type"]} (nullable: {col["is_nullable"]})')

if __name__ == "__main__":
    main()
#!/usr/bin/env python3
"""
Check categories in database
"""
import sys
import os
from supabase import create_client

# Add the app directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

def check_categories():
    """Check what categories exist in the database"""
    # Initialize Supabase client with service key to check
    supabase_service = create_client(settings.SUPABASE_URL, settings.SUPABASE_SERVICE_KEY)
    business_id = '5021efe2-7c63-4bcd-bd2b-3e243e8a4935'

    # Check what categories exist
    response = supabase_service.table('categories').select('id, category_name, business_id').eq('business_id', business_id).execute()

    print('Categories for business (service key):')
    print(f'Total categories: {len(response.data)}')
    for cat in response.data:
        print(f'  ID: {cat["id"]}')
        print(f'    category_name: {cat.get("category_name")}')
        print(f'    business_id: {cat.get("business_id")}')
        print()

    # Also check all categories in the system
    print('All categories in system (service key):')
    all_response = supabase_service.table('categories').select('id, category_name, business_id, category_type').limit(50).execute()
    print(f'Total categories in system: {len(all_response.data)}')
    for cat in all_response.data[:20]:  # Show first 20
        print(f'  ID: {cat["id"]}, category_name: {cat.get("category_name")}, business_id: {cat.get("business_id")}, type: {cat.get("category_type")}')
    if len(all_response.data) > 20:
        print(f'  ... and {len(all_response.data) - 20} more')
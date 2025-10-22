#!/usr/bin/env python3
"""
Check for travel categories
"""
import sys
import os
from supabase import create_client

# Add the app directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from app.core.config import settings

def check_travel_categories():
    """Check for travel-related categories"""
    supabase_service = create_client(settings.SUPABASE_URL, settings.SUPABASE_SERVICE_KEY)

    print('All categories with Travel in name:')
    all_response = supabase_service.table('categories').select('id, category_name, business_id, category_type').ilike('category_name', '%travel%').execute()
    print(f'Categories with Travel: {len(all_response.data)}')
    for cat in all_response.data:
        print(f'  {cat}')

    print()
    print('All expense categories:')
    expense_response = supabase_service.table('categories').select('id, category_name').eq('category_type', 'expense').execute()
    print(f'Expense categories: {len(expense_response.data)}')
    for cat in expense_response.data:
        print(f'  {cat["category_name"]}')

if __name__ == "__main__":
    check_travel_categories()
#!/usr/bin/env python3
"""
Seed default categories for testing
"""
import sys
import os
from supabase import create_client

# Add the app directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from app.core.config import settings

def seed_categories():
    """Create default categories for testing"""
    # Initialize Supabase client with service key to bypass RLS
    supabase = create_client(settings.SUPABASE_URL, settings.SUPABASE_SERVICE_KEY)
    business_id = '5021efe2-7c63-4bcd-bd2b-3e243e8a4935'

    # Default categories
    default_categories = [
        {"category_name": "Travel & Entertainment", "description": "Hotels, flights, meals, entertainment", "category_type": "expense"},
        {"category_name": "Office Supplies", "description": "Stationery, equipment, software", "category_type": "expense"},
        {"category_name": "Meals & Entertainment", "description": "Business meals, client entertainment", "category_type": "expense"},
        {"category_name": "Professional Services", "description": "Consulting, legal, accounting", "category_type": "expense"},
        {"category_name": "Marketing & Advertising", "description": "Advertising, promotions, events", "category_type": "expense"},
        {"category_name": "Utilities", "description": "Electricity, water, internet, phone", "category_type": "expense"},
        {"category_name": "Rent & Lease", "description": "Office rent, equipment leases", "category_type": "expense"},
        {"category_name": "Insurance", "description": "Business insurance premiums", "category_type": "expense"},
        {"category_name": "Transportation", "description": "Vehicle expenses, public transport", "category_type": "expense"},
        {"category_name": "Training & Development", "description": "Employee training, conferences", "category_type": "expense"}
    ]

    print(f"Seeding {len(default_categories)} default categories for business {business_id}...")

    for category in default_categories:
        try:
            data = {
                "business_id": business_id,
                "category_name": category["category_name"],
                "description": category["description"],
                "category_type": "expense"
            }
            response = supabase.table('categories').insert(data).execute()
            print(f"✅ Created category: {category['category_name']}")
        except Exception as e:
            print(f"❌ Failed to create category {category['category_name']}: {e}")

if __name__ == "__main__":
    seed_categories()
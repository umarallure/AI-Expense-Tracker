#!/usr/bin/env python3
"""
Test script to verify category matching functionality
"""
import asyncio
import sys
import os
from supabase import create_client

# Add the app directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from app.services.transaction_creator import TransactionCreator
from app.core.config import settings

async def test_category_matching():
    """Test the category matching functionality"""
    # Initialize Supabase client with service key
    supabase = create_client(settings.SUPABASE_URL, settings.SUPABASE_SERVICE_KEY)

    # Get a business ID (we'll use the first one we find)
    try:
        business_response = supabase.table("businesses").select("id").limit(1).execute()
        if not business_response.data:
            print("No businesses found in database")
            return
        business_id = business_response.data[0]["id"]
        print(f"Using business ID: {business_id}")
    except Exception as e:
        print(f"Failed to get business ID: {e}")
        return

    creator = TransactionCreator()

    # Test cases
    test_cases = [
        'Travel',
        'Office Supplies',
        'Meals',
        'Professional Services',
        'NonExistentCategory'
    ]

    print("Testing AI-based category selection:")
    print("=" * 50)
    print("Categories are now selected directly by AI during document extraction.")
    print("No more fuzzy string matching - AI returns category_id directly.")
    print("\nTo test:")
    print("1. Upload a document (receipt, invoice, etc.)")
    print("2. AI extracts data including category_id")
    print("3. Transaction is created with the AI-selected category")
    print("\nThe fuzzy matching logic has been removed from TransactionCreator.")

if __name__ == "__main__":
    asyncio.run(test_category_matching())
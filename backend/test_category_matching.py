#!/usr/bin/env python3
"""
Test script to verify category matching functionality
"""
import asyncio
import sys
import os

# Add the app directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from app.services.transaction_creator import TransactionCreator

async def test_category_matching():
    """Test the category matching functionality"""
    creator = TransactionCreator()

    # Test cases
    test_cases = [
        'Travel',
        'Office Supplies',
        'Meals',
        'Professional Services',
        'NonExistentCategory'
    ]

    print("Testing category matching functionality:")
    print("=" * 50)

    for category_name in test_cases:
        try:
            category_id = await creator._match_category(category_name)
            status = "FOUND" if category_id else "NOT FOUND"
            print(f"Category '{category_name}': {status} (ID: {category_id})")
        except Exception as e:
            print(f"Category '{category_name}': ERROR - {str(e)}")

if __name__ == "__main__":
    asyncio.run(test_category_matching())
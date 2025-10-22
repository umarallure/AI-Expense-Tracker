#!/usr/bin/env python3
"""
Test script to verify prompt building with category IDs
"""
import sys
import os
from supabase import create_client

# Add the app directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from app.services.ai.data_extractor import DataExtractor
from app.core.config import settings

def test_prompt_building():
    """Test that prompts include category IDs"""
    # Initialize Supabase client
    supabase = create_client(settings.SUPABASE_URL, settings.SUPABASE_SERVICE_KEY)

    # Get a business ID
    business_response = supabase.table("businesses").select("id").limit(1).execute()
    if not business_response.data:
        print("No businesses found in database")
        return
    business_id = business_response.data[0]["id"]
    print(f"Using business ID: {business_id}")

    # Initialize DataExtractor
    extractor = DataExtractor()

    # Fetch categories
    categories = extractor._fetch_business_categories(business_id, supabase)
    print(f"Fetched {len(categories)} categories")

    # Build prompt
    test_text = "Sample hotel receipt text"
    prompt = extractor._build_extraction_prompt(test_text, "receipt", categories)

    print("\n=== PROMPT PREVIEW ===")
    # Show just the category section
    lines = prompt.split('\n')
    in_category_section = False
    for line in lines:
        if 'Available Categories' in line:
            in_category_section = True
        if in_category_section:
            print(line)
            if line.strip() == '' and in_category_section:
                break

    print("\n=== CHECKING FOR CATEGORY IDs ===")
    has_category_ids = 'ID:' in prompt and 'Name:' in prompt
    print(f"Prompt contains category IDs: {has_category_ids}")
    print(f"Prompt contains 'category_id': {'category_id' in prompt}")

if __name__ == "__main__":
    test_prompt_building()
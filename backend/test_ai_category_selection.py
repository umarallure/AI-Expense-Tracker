#!/usr/bin/env python3
"""
Test script to verify AI category selection
"""
import asyncio
import sys
import os
from supabase import create_client

# Add the app directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from app.services.ai.data_extractor import DataExtractor
from app.core.config import settings

async def test_ai_category_selection():
    """Test AI category selection"""
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

    # Test document text (hotel receipt)
    test_text = """
    MOTEL 6
    123 Main Street
    Chula Vista, CA 91910

    Guest: John Doe
    Check-in: 09/12/2025
    Check-out: 09/13/2025
    Room: 101

    Room Rate: $71.00
    Taxes & Fees: $9.44
    Total: $80.44

    Payment: Visa ****1234
    Receipt #: 73240609831625
    """

    print("Testing AI category selection...")
    print("Document text:")
    print(test_text)
    print("\nExtracting data...")

    # Extract data
    extracted_data = extractor.extract(
        text=test_text,
        document_type="receipt",
        business_id=business_id,
        supabase_client=supabase
    )

    print("\nExtracted data:")
    print(f"Vendor: {extracted_data.get('vendor')}")
    print(f"Amount: {extracted_data.get('amount')}")
    print(f"Date: {extracted_data.get('date')}")
    print(f"Category ID: {extracted_data.get('category_id')}")
    print(f"Confidence: {extracted_data.get('field_confidence', {}).get('category_id')}")

    # Verify the category_id exists in database
    if extracted_data.get('category_id'):
        category_check = supabase.table('categories').select('category_name').eq('id', extracted_data['category_id']).execute()
        if category_check.data:
            print(f"✅ Category ID is valid: {category_check.data[0]['category_name']}")
        else:
            print("❌ Category ID not found in database")
    else:
        print("⚠️ No category_id returned by AI")

if __name__ == "__main__":
    asyncio.run(test_ai_category_selection())
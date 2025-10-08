"""Test to verify document response includes processing fields"""
import requests
import os
from dotenv import load_dotenv

load_dotenv()

# Configuration
API_URL = "http://localhost:8000/api/v1"
DOCUMENT_ID = "57159141-580e-4bfa-89c2-78ad2dc13bb9"
BUSINESS_ID = "5021efe2-7c63-4bcd-bd2b-3e243e8a4935"

# Get token from environment or use a test token
TOKEN = os.getenv("TEST_TOKEN", "your-token-here")

headers = {
    "Authorization": f"Bearer {TOKEN}",
    "Content-Type": "application/json"
}

print("=" * 80)
print("Testing Document Response Fields")
print("=" * 80)

# Test 1: Get documents list
print("\n1. Testing GET /documents/?business_id=...")
try:
    response = requests.get(
        f"{API_URL}/documents/",
        params={"business_id": BUSINESS_ID},
        headers=headers
    )
    
    if response.status_code == 200:
        data = response.json()
        documents = data.get("documents", [])
        
        # Find our test document
        test_doc = None
        for doc in documents:
            if doc.get("id") == DOCUMENT_ID:
                test_doc = doc
                break
        
        if test_doc:
            print(f"✓ Found document: {test_doc.get('document_name')}")
            print(f"  - extraction_status: {test_doc.get('extraction_status')}")
            print(f"  - confidence_score: {test_doc.get('confidence_score')}")
            print(f"  - processing_error: {test_doc.get('processing_error')}")
            print(f"  - processed_at: {test_doc.get('processed_at')}")
            
            if test_doc.get('extraction_status'):
                print("\n✓ SUCCESS: extraction_status field is present!")
            else:
                print("\n✗ FAIL: extraction_status field is missing")
        else:
            print(f"✗ Document {DOCUMENT_ID} not found in list")
    else:
        print(f"✗ Request failed: {response.status_code}")
        print(f"  Response: {response.text}")
        
except Exception as e:
    print(f"✗ Error: {str(e)}")

# Test 2: Get processing status
print("\n2. Testing GET /document-processing/{id}/status")
try:
    response = requests.get(
        f"{API_URL}/document-processing/{DOCUMENT_ID}/status",
        headers=headers
    )
    
    if response.status_code == 200:
        status_data = response.json()
        print(f"✓ Processing status retrieved:")
        print(f"  - extraction_status: {status_data.get('extraction_status')}")
        print(f"  - raw_text_length: {status_data.get('raw_text_length')}")
        print(f"  - word_count: {status_data.get('word_count')}")
        print(f"  - confidence_score: {status_data.get('confidence_score')}")
        
        if status_data.get('raw_text_preview'):
            preview = status_data['raw_text_preview'][:100]
            print(f"  - text_preview: {preview}...")
    else:
        print(f"✗ Request failed: {response.status_code}")
        print(f"  Response: {response.text}")
        
except Exception as e:
    print(f"✗ Error: {str(e)}")

print("\n" + "=" * 80)

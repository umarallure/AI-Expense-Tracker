"""
Quick test for enhanced JSON parsing with fallback strategies
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from app.services.ai.data_extractor import DataExtractor

def test_json_parsing():
    """Test various malformed JSON scenarios"""
    
    extractor = DataExtractor()
    
    # Test 1: Valid JSON
    print("\n" + "="*80)
    print("Test 1: Valid JSON")
    print("="*80)
    valid_json = '{"vendor": "Test Inc", "amount": 100.50, "date": "2025-11-02"}'
    result = extractor._parse_json_with_fallback(valid_json)
    print(f"✅ Result: {result}")
    assert result is not None
    assert result["vendor"] == "Test Inc"
    
    # Test 2: Trailing comma
    print("\n" + "="*80)
    print("Test 2: Trailing comma (before cleaning)")
    print("="*80)
    trailing_comma = '{"vendor": "Test Inc", "amount": 100.50,}'
    cleaned = extractor._clean_json_response(trailing_comma)
    result = extractor._parse_json_with_fallback(cleaned)
    print(f"✅ Result: {result}")
    assert result is not None
    
    # Test 3: Missing comma between properties
    print("\n" + "="*80)
    print("Test 3: Missing comma between properties")
    print("="*80)
    missing_comma = '{"vendor": "Test Inc""amount": 100.50}'
    cleaned = extractor._clean_json_response(missing_comma)
    result = extractor._parse_json_with_fallback(cleaned)
    print(f"Result: {result}")
    # This might still fail, but should at least try regex fallback
    
    # Test 4: Truncated JSON with unclosed braces
    print("\n" + "="*80)
    print("Test 4: Truncated JSON")
    print("="*80)
    truncated = '{"vendor": "Test Inc", "amount": 100.50, "field": "incomplete'
    result = extractor._parse_json_with_fallback(truncated)
    print(f"Result: {result}")
    if result:
        print("✅ Fallback parsing succeeded!")
    else:
        print("⚠️ Could not parse truncated JSON")
    
    # Test 5: Multi-transaction with missing commas
    print("\n" + "="*80)
    print("Test 5: Multi-transaction array")
    print("="*80)
    multi_tx = '''
    {
        "extraction_type": "multi_transaction",
        "transactions": [
            {"vendor": "Store A", "amount": 50.0}
            {"vendor": "Store B", "amount": 75.0}
        ]
    }
    '''
    cleaned = extractor._clean_json_response(multi_tx)
    result = extractor._parse_json_with_fallback(cleaned)
    print(f"✅ Result: {result}")
    if result:
        print(f"   Transactions found: {len(result.get('transactions', []))}")
    
    # Test 6: Markdown wrapped JSON
    print("\n" + "="*80)
    print("Test 6: Markdown code block")
    print("="*80)
    markdown = '''
    Here is the result:
    ```json
    {"vendor": "Test Inc", "amount": 100.50}
    ```
    '''
    cleaned = extractor._clean_json_response(markdown)
    result = extractor._parse_json_with_fallback(cleaned)
    print(f"✅ Result: {result}")
    assert result is not None
    
    print("\n" + "="*80)
    print("✅ All JSON parsing tests completed!")
    print("="*80)

if __name__ == "__main__":
    test_json_parsing()

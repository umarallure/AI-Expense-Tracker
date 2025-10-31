"""
Simple test runner for TransactionCreator missing fields validation
"""
import sys
import os

# Add the app directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from app.services.transaction_creator import TransactionCreator


def run_tests():
    """Run all test cases"""
    creator = TransactionCreator(confidence_threshold=0.85)
    passed = 0
    failed = 0

    def assert_equal(actual, expected, test_name):
        nonlocal passed, failed
        if actual == expected:
            print(f"✅ {test_name}")
            passed += 1
        else:
            print(f"❌ {test_name} - Expected: {expected}, Got: {actual}")
            failed += 1

    def assert_in(item, container, test_name):
        nonlocal passed, failed
        if item in container:
            print(f"✅ {test_name}")
            passed += 1
        else:
            print(f"❌ {test_name} - '{item}' not found in {container}")
            failed += 1

    def assert_not_in(item, container, test_name):
        nonlocal passed, failed
        if item not in container:
            print(f"✅ {test_name}")
            passed += 1
        else:
            print(f"❌ {test_name} - '{item}' unexpectedly found in {container}")
            failed += 1

    print("Running TransactionCreator Missing Fields Tests...\n")

    # Test 1: Missing category field
    extracted_data = {
        "vendor": "Amazon",
        "amount": 100.50,
        "date": "2025-10-30",
        "description": "Office supplies",
        "payment_method": "Credit Card",
    }
    status = creator._determine_status(0.96, extracted_data)
    assert_equal(status, "pending", "High confidence with missing category should be pending")
    missing_fields = creator._check_missing_required_fields(extracted_data)
    assert_in("category", missing_fields, "Missing category should be detected")

    # Test 2: Missing payment method field
    extracted_data = {
        "vendor": "Walmart",
        "amount": 75.25,
        "date": "2025-10-30",
        "description": "Groceries",
        "category_id": "some-category-id",
    }
    status = creator._determine_status(0.97, extracted_data)
    assert_equal(status, "pending", "High confidence with missing payment method should be pending")
    missing_fields = creator._check_missing_required_fields(extracted_data)
    assert_in("payment_method", missing_fields, "Missing payment method should be detected")

    # Test 3: Missing vendor field (non-transfer)
    extracted_data = {
        "amount": 200.00,
        "date": "2025-10-30",
        "description": "Consulting services",
        "category_id": "some-category-id",
        "payment_method": "Bank Transfer",
    }
    status = creator._determine_status(0.95, extracted_data)
    assert_equal(status, "pending", "High confidence with missing vendor should be pending")
    missing_fields = creator._check_missing_required_fields(extracted_data)
    assert_in("vendor", missing_fields, "Missing vendor should be detected")

    # Test 4: Transfer/deposit doesn't require vendor
    extracted_data = {
        "amount": 500.00,
        "date": "2025-10-30",
        "description": "Bank transfer to savings",
        "category_id": "some-category-id",
        "payment_method": "Bank Transfer",
    }
    missing_fields = creator._check_missing_required_fields(extracted_data)
    assert_not_in("vendor", missing_fields, "Transfer transactions should not require vendor")

    # Test 5: Invalid amount
    extracted_data = {
        "vendor": "Office Depot",
        "date": "2025-10-30",
        "description": "Printer ink",
        "category_id": "some-category-id",
        "payment_method": "Credit Card",
        "amount": 0
    }
    status = creator._determine_status(0.96, extracted_data)
    assert_equal(status, "pending", "Transaction with invalid amount should be pending")
    missing_fields = creator._check_missing_required_fields(extracted_data)
    assert_in("amount", missing_fields, "Invalid amount should be detected")

    # Test 6: All fields present, high confidence
    extracted_data = {
        "vendor": "Best Buy",
        "amount": 299.99,
        "date": "2025-10-30",
        "description": "Laptop purchase",
        "category_id": "some-category-id",
        "payment_method": "Credit Card"
    }
    status = creator._determine_status(0.96, extracted_data)
    assert_equal(status, "approved", "High confidence with all fields should be approved")
    missing_fields = creator._check_missing_required_fields(extracted_data)
    assert_equal(len(missing_fields), 0, "No missing fields should be detected")

    # Test 7: All fields present, medium confidence
    status = creator._determine_status(0.90, extracted_data)
    assert_equal(status, "pending", "Medium confidence should be pending")

    # Test 8: Low confidence
    status = creator._determine_status(0.80, extracted_data)
    assert_equal(status, "draft", "Low confidence should be draft")

    # Test 9: Notes generation with missing fields
    extracted_data_missing = {
        "vendor": "Starbucks",
        "amount": 12.75,
        "date": "2025-10-30",
        "description": "Coffee purchase",
    }
    notes = creator._generate_notes(extracted_data_missing, 0.95)
    assert_in("MISSING REQUIRED FIELDS", notes, "Notes should mention missing fields")
    assert_in("CATEGORY", notes, "Notes should specify which field is missing")

    # Test 10: Notes generation without missing fields
    notes = creator._generate_notes(extracted_data, 0.95)
    assert_not_in("MISSING REQUIRED FIELDS", notes, "Notes should not mention missing fields when all present")

    print(f"\nTest Results: {passed} passed, {failed} failed")
    return failed == 0


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
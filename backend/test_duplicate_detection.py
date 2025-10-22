#!/usr/bin/env python3
"""
Test script for duplicate transaction detection
This script tests the duplicate detection logic with the mock data we just inserted.
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'backend'))

# Import the duplicate detection logic (we'll need to adapt it for Python)
def generate_transaction_fingerprint(transaction):
    """Generate a transaction fingerprint for exact duplicate detection"""
    date = transaction['date'].split('T')[0]  # Get date part only
    amount = f"{transaction['amount']:.2f}"
    vendor = (transaction.get('vendor') or '').lower().strip()
    description = transaction['description'].lower().strip()

    fingerprint = f"{date}|{amount}|{vendor}|{description}"
    return hash(fingerprint)  # Simple hash for testing

def find_exact_duplicates(transactions):
    """Find exact duplicates in a list of transactions"""
    fingerprint_map = {}

    for transaction in transactions:
        fingerprint = generate_transaction_fingerprint(transaction)
        if fingerprint not in fingerprint_map:
            fingerprint_map[fingerprint] = []
        fingerprint_map[fingerprint].append(transaction)

    # Return only groups with duplicates
    duplicate_groups = {}
    for fingerprint, group in fingerprint_map.items():
        if len(group) > 1:
            duplicate_groups[fingerprint] = group

    return duplicate_groups

def test_duplicate_detection():
    """Test the duplicate detection with mock data"""
    # Mock transactions based on what we inserted
    mock_transactions = [
        # Exact duplicates
        {'id': '1', 'date': '2025-10-20T10:00:00Z', 'amount': 150.00, 'vendor': 'Marriott Hotels', 'description': 'Hotel stay for 1 night'},
        {'id': '2', 'date': '2025-10-20T10:00:00Z', 'amount': 150.00, 'vendor': 'Marriott Hotels', 'description': 'Hotel stay for 1 night'},

        # Similar but not exact
        {'id': '3', 'date': '2025-10-20T10:00:00Z', 'amount': 150.00, 'vendor': 'Marriott Hotels', 'description': 'Hotel accommodation for one night'},
        {'id': '4', 'date': '2025-10-22T10:00:00Z', 'amount': 150.00, 'vendor': 'Marriott Hotels', 'description': 'Hotel stay for 1 night'},
        {'id': '5', 'date': '2025-10-20T10:00:00Z', 'amount': 150.00, 'vendor': 'Marriot Hotels', 'description': 'Hotel stay for 1 night'},
        {'id': '6', 'date': '2025-10-20T10:00:00Z', 'amount': 149.25, 'vendor': 'Marriott Hotels', 'description': 'Hotel stay for 1 night'},

        # Different transactions
        {'id': '7', 'date': '2025-10-20T10:00:00Z', 'amount': 200.00, 'vendor': 'Marriott Hotels', 'description': 'Hotel stay for 2 nights'},
        {'id': '8', 'date': '2025-10-20T10:00:00Z', 'amount': 150.00, 'vendor': 'Hilton Hotels', 'description': 'Hotel stay for 1 night'},
        {'id': '9', 'date': '2025-10-25T10:00:00Z', 'amount': 150.00, 'vendor': 'Marriott Hotels', 'description': 'Hotel stay for 1 night'},
    ]

    print("🧪 Testing Duplicate Detection Logic")
    print("=" * 50)

    # Find exact duplicates
    duplicate_groups = find_exact_duplicates(mock_transactions)

    print(f"📊 Found {len(duplicate_groups)} duplicate group(s)")
    print()

    for i, (fingerprint, group) in enumerate(duplicate_groups.items(), 1):
        print(f"🔍 Duplicate Group {i}: {len(group)} transactions")
        for transaction in group:
            print(f"   ID: {transaction['id']}, Date: {transaction['date'][:10]}, Amount: ${transaction['amount']}, Vendor: {transaction['vendor']}, Description: {transaction['description']}")
        print()

    # Expected results
    expected_duplicates = 1  # Only the exact duplicates should be in one group
    actual_duplicates = len(duplicate_groups)

    if actual_duplicates == expected_duplicates:
        print("✅ PASS: Found expected number of duplicate groups")
    else:
        print(f"❌ FAIL: Expected {expected_duplicates} duplicate groups, found {actual_duplicates}")

    # Check that the exact duplicates are detected
    exact_duplicate_found = any(
        len(group) == 2 and
        all(t['description'] == 'Hotel stay for 1 night' and
            t['vendor'] == 'Marriott Hotels' and
            t['amount'] == 150.00 and
            t['date'].startswith('2025-10-20')
            for t in group)
        for group in duplicate_groups.values()
    )

    if exact_duplicate_found:
        print("✅ PASS: Exact duplicates correctly identified")
    else:
        print("❌ FAIL: Exact duplicates not found")

    print()
    print("🎯 Test Summary:")
    print("- Exact duplicates should be detected by hash-based matching")
    print("- Fuzzy matching (85%+ similarity) is handled by the frontend")
    print("- Different amounts, vendors, dates should not be flagged as exact duplicates")
    print()
    print("🚀 Ready to test the frontend duplicate detection feature!")

if __name__ == "__main__":
    test_duplicate_detection()
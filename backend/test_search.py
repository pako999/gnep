#!/usr/bin/env python3
"""
Quick test script for search functionality
"""
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# Set DATABASE_URL from environment or use default
if not os.getenv('DATABASE_URL'):
    print("⚠️  DATABASE_URL not set, using default...")
    # You'll need to set this
    sys.exit(1)

from property_detective.matcher import find_probable_parcels

# Test data
test_cases = [
    {
        'name': 'Test 1: Area 500m²',
        'data': {
            'settlement': 'Ljubljana',
            'parcel_area_m2': 500
        }
    },
    {
        'name': 'Test 2: Area 542m² (specific)',
        'data': {
            'settlement': 'Test',
            'parcel_area_m2': 542.0
        }
    },
    {
        'name': 'Test 3: Area 1000m²',
        'data': {
            'settlement': 'Maribor',
            'parcel_area_m2': 1000
        }
    }
]

print("🔍 Testing GNEP Search Functionality")
print("=" * 60)

for test in test_cases:
    print(f"\n{test['name']}")
    print("-" * 60)
    
    try:
        result = find_probable_parcels(test['data'])
        
        print(f"✅ Success: {result['success']}")
        print(f"📊 Count: {result['count']}")
        print(f"💬 Message: {result['message']}")
        
        if result['count'] > 0:
            print(f"\n🎯 Top 3 matches:")
            for i, match in enumerate(result['matches'][:3], 1):
                print(f"  {i}. Parcel: {match['parcela_stevilka']}")
                print(f"     KO: {match['ko_sifra']}")
                print(f"     Area: {match['povrsina']}m²")
                print(f"     Confidence: {match['confidence_score']}%")
    except Exception as e:
        print(f"❌ Error: {e}")

print("\n" + "=" * 60)
print("✨ Test complete!")

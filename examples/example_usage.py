"""
Example usage of PropertyDetective module
Demonstrates how to find probable parcels for a real estate listing
"""

import json
from property_detective import find_probable_parcels
from property_detective.geojson_utils import save_geojson

# Example listing data (from scraper)
listing_data = {
    "settlement": "Ljubljana - Center",
    "parcel_area_m2": 542.0,
    "construction_year": 1974,
    "net_floor_area_m2": 185.4,
    "property_type": "Hiša",
    "street_name": "Slovenska cesta"
}

def main():
    print("🔍 GNEP PropertyDetective - Example Usage\n")
    print("Finding probable parcels for:")
    print(json.dumps(listing_data, indent=2))
    print("\n" + "="*60 + "\n")
    
    # Call PropertyDetective
    result = find_probable_parcels(listing_data)
    
    if result['success']:
        print(f"✅ {result['message']}\n")
        print(f"Found {result['count']} matches:\n")
        
        for idx, match in enumerate(result['matches'], 1):
            parcela = match['parcela']
            confidence = match['confidence']
            score = match['score']
            
            print(f"Match #{idx}: {confidence:.1f}% confidence (Score: {score})")
            print(f"  Parcela: {parcela['parcela_stevilka']}")
            print(f"  Location: {parcela['ko_ime']}")
            print(f"  Area: {parcela['povrsina']}m²")
            
            if 'stavba' in match and match['stavba']:
                stavba = match['stavba']
                print(f"  Building:")
                if stavba.get('leto_izgradnje'):
                    print(f"    Year: {stavba['leto_izgradnje']}")
                if stavba.get('neto_tloris'):
                    print(f"    Floor area: {stavba['neto_tloris']}m²")
                if stavba.get('naslov'):
                    print(f"    Address: {stavba['naslov']}")
            
            # Show score breakdown
            print(f"  Score breakdown:")
            for criterion, points in match['score_breakdown'].items():
                print(f"    {criterion}: +{points} points")
            print()
        
        # Save GeoJSON for visualization
        if result['geojson']:
            output_file = 'examples/result.geojson'
            save_geojson(result['geojson'], output_file)
            print(f"💾 GeoJSON saved to: {output_file}")
            print("   You can visualize this on a map!")
    else:
        print(f"❌ Error: {result['message']}")


if __name__ == "__main__":
    main()

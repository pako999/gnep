
import os
import sys
import zipfile

def analyze_zip(zip_path):
    print(f"📦 Checking: {os.path.basename(zip_path)}")
    try:
        if not zipfile.is_zipfile(zip_path):
            print("   ❌ Not a valid zip file.")
            return

        with zipfile.ZipFile(zip_path, 'r') as zf:
            files = zf.namelist()
            
            # Check for Shapefiles (.shp)
            shps = [f for f in files if f.endswith('.shp')]
            if shps:
                print(f"   ✅ FOUND SHAPEFILES ({len(shps)}):")
                for s in shps:
                    print(f"      - {s}")
                print("   🎉 This zip contains GEOMETRY! You are good.")
                return True
            
            # Check for CSVs
            csvs = [f for f in files if f.endswith('.csv')]
            if csvs:
                print(f"   ℹ️  Contains CSVs ({len(csvs)}):")
                for c in csvs[:3]:
                    print(f"      - {c}")
                print("   ⚠️  No Shapefiles found. likely just Attributes (Text).")
                return False
                
            print("   ⚠️  Zip contains neither SHP nor CSV.")
            
    except Exception as e:
        print(f"   ❌ Error reading: {e}")

def main():
    start_dir = "gurs_data"
    found_zip = False
    
    # Walk to find the specific parcele zip
    for root, dirs, files in os.walk(start_dir):
        for f in files:
            if "parcele" in f and f.endswith(".zip"):
                found_zip = True
                full_path = os.path.join(root, f)
                analyze_zip(full_path)
    
    if not found_zip:
        print("❌ No 'parcele' zip files found in gurs_data.")

if __name__ == "__main__":
    main()

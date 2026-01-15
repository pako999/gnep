
import os
import sys
import zipfile
import geopandas as gpd

def check_headers(data_dir):
    # Find the zip
    zip_path = None
    for root, dirs, files in os.walk(data_dir):
        for f in files:
            if "KN_SLO_PARCELE_SLO_parcele_" in f and f.endswith(".zip"):
                zip_path = os.path.join(root, f)
                break
    
    if not zip_path:
        print("❌ Zip not found")
        return

    print(f"📦 Zip: {zip_path}")
    
    # Read first row
    try:
        with zipfile.ZipFile(zip_path, 'r') as zf:
             shps = [n for n in zf.namelist() if n.endswith("PARCELE_poligon.shp")]
             shp_name = shps[0]
             
        full_path = f"zip://{zip_path}!{shp_name}"
        gdf = gpd.read_file(full_path, rows=1)
        print(f"📊 COLUMNS: {list(gdf.columns)}")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    check_headers(sys.argv[1])

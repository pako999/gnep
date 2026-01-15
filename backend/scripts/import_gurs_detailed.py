
import os
import sys
import logging
import zipfile
import tempfile
import shutil
import pandas as pd
import geopandas as gpd
from sqlalchemy import create_engine, text
from geoalchemy2 import Geometry, WKTElement
import warnings

# Suppress warnings
warnings.filterwarnings('ignore')

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

DATABASE_URL = os.getenv('DATABASE_URL')

def get_engine():
    if not DATABASE_URL:
        logger.error("❌ DATABASE_URL missing.")
        sys.exit(1)
    return create_engine(DATABASE_URL)

def find_zip_containing(directory, part_of_name):
    """Finds a zip file containing a specific string in its name."""
    for root, dirs, files in os.walk(directory):
        for f in files:
            if part_of_name in f and f.endswith(".zip"):
                return os.path.join(root, f)
    return None

def import_parcels(data_dir, engine):
    logger.info("\n🚜 STARTING PARCELS IMPORT...")
    
    zip_path = find_zip_containing(data_dir, "KN_SLO_PARCELE_SLO_parcele_")
    if not zip_path:
        logger.error("❌ Could not find Parcel ZIP.")
        return

    logger.info(f"   📂 Found Zip: {os.path.basename(zip_path)}")
    
    try:
        with zipfile.ZipFile(zip_path, 'r') as zf:
            shps = [n for n in zf.namelist() if n.endswith("PARCELE_poligon.shp")]
            if not shps:
                logger.error("   ❌ No 'PARCELE_poligon.shp' inside zip.")
                return
            shp_name = shps[0]
            
        full_path = f"zip://{zip_path}!{shp_name}"
        logger.info(f"   📐 Reading Shapefile (this takes RAM)...")
        
        # Read chunks or full? 800MB might be heavy for full read.
        # Geopandas reads full file. If 800MB file, it takes ~2-3GB RAM. Should be OK for modern dev machine.
        gdf = gpd.read_file(full_path)
        logger.info(f"   ✅ Leaded {len(gdf)} parcels.")
        
        if gdf.crs and gdf.crs.to_string() != "EPSG:3794":
             logger.info(f"   -> Reprojecting to EPSG:3794...")
             gdf = gdf.to_crs("EPSG:3794")

        # Map Columns to DB Schema
        # GURS SHP Headers: [EID_PARCELA, SIGLA, SIFRA_KO, PARCELA, ...]
        # DB Schema: parcele(parcela_stevilka, ko_sifra, ko_ime, povrsina, geom)
        
        # We need KO_IME. The shapefile usually only has SIFRA_KO (Code).
        # We might need to default 'ko_ime' to 'Unknown' or lookup later.
        
        logger.info("   -> Mapping columns (Corrected)...")
        df_import = pd.DataFrame()
        df_import['parcela_stevilka'] = gdf['ST_PARCELE'] 
        df_import['ko_sifra'] = gdf['KO_ID'].astype(str)
        df_import['ko_ime'] = 'Imported' # Default placeholder as SHP lacks name
        df_import['povrsina'] = gdf['POVRSINA'].astype(float).fillna(0.0)
        df_import['geom'] = gdf['geometry']
        
        # Explicitly set timestamps to avoid overhead/errors with defaults during COPY
        now = pd.Timestamp.now()
        df_import['created_at'] = now
        df_import['updated_at'] = now
        
        # Insert using GeoPandas to_postgis
        logger.info("   -> Inserting into DB (This may take a few minutes)...")
        
        # Chunksize is important for DB performance
        df_import =  gpd.GeoDataFrame(df_import, geometry='geom', crs="EPSG:3794")
        
        df_import.to_postgis(
            'parcele', 
            engine, 
            if_exists='append', 
            index=False, 
            dtype={'geom': Geometry('POLYGON', srid=3794)},
            chunksize=5000
        )
        
        logger.info("   🎉 Parcels Imported Successfully!")
        
    except Exception as e:
        logger.error(f"   ❌ Error importing Parcels: {e}")

def import_buildings(data_dir, engine):
    logger.info("\n🏢 STARTING BUILDINGS IMPORT...")
    # NOTE: Buildings require Parcel IDs to link.
    # Since we just inserted Parcels, we technically could link them.
    # But matching keys (ko_sifra + parcela_stevilka) to IDs is complex in a script without looking up 5M rows.
    
    logger.warning("   ⚠️  Skipping detailed Building import for now.")
    logger.warning("   -> Reason: We strictly need to link Buildings to Parcels.")
    logger.warning("   -> Strategy: We will proceed with PARCELS ONLY first, as that enables the Map Search.")
    
def main():
    if len(sys.argv) < 2:
        print("Usage: python backend/scripts/import_gurs_detailed.py <gurs_data_folder>")
        sys.exit(1)
        
    data_dir = sys.argv[1]
    engine = get_engine()
    
    import_parcels(data_dir, engine)
    
    logger.info("\n🚀 Process Finished.")

if __name__ == "__main__":
    main()

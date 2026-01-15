import os
import sys
import logging
import geopandas as gpd
from sqlalchemy import create_engine
import pandas as pd

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

DATABASE_URL = os.getenv('DATABASE_URL')

def get_engine():
    if not DATABASE_URL:
        logger.error("❌ DATABASE_URL missing.")
        sys.exit(1)
    return create_engine(DATABASE_URL)

def import_from_zip(zip_path, shapefile_name, table_name, engine):
    """Import shapefile directly from ZIP"""
    logger.info(f"\n📦 Importing from ZIP: {os.path.basename(zip_path)}")
    logger.info(f"   Target shapefile: {shapefile_name}")
    
    try:
        # Read directly from ZIP using zip:// protocol
        zip_url = f"zip://{zip_path}!{shapefile_name}"
        logger.info(f"   Reading from: {zip_url}")
        
        gdf = gpd.read_file(zip_url)
        logger.info(f"   ✅ Loaded {len(gdf)} records")
        logger.info(f"   Columns: {list(gdf.columns)[:10]}")
        
        # Reproject if needed
        if gdf.crs and gdf.crs.to_string() != "EPSG:3794":
            logger.info(f"   -> Reprojecting to EPSG:3794...")
            gdf = gdf.to_crs("EPSG:3794")
        
        # Set geometry column and rename
        gdf = gdf.set_geometry('geometry')
        gdf = gdf.rename_geometry('geom')
        
        # Add timestamps
        now = pd.Timestamp.now()
        gdf['created_at'] = now
        gdf['updated_at'] = now
        
        # Insert into database
        logger.info(f"   -> Inserting into {table_name}...")
        gdf.to_postgis(
            table_name,
            engine,
            if_exists='append',
            index=False,
            dtype={'geom': 'Geometry'},
            chunksize=5000
        )
        
        logger.info(f"   🎉 Successfully imported {len(gdf)} records to {table_name}")
        return len(gdf)
        
    except Exception as e:
        logger.error(f"   ❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return 0

def main():
    engine = get_engine()
    
    logger.info("🚀 BATCH IMPORT FROM ZIP FILES")
    logger.info("=" * 60)
    
    total_imported = 0
    
    # 1. Building Attributes (critical for search)
    count = import_from_zip(
        'gurs_data/KN_SLO_STAVBE_SLO_20260111/KN_SLO_STAVBE_SLO_stavbe_20260111.zip',
        'KN_SLO_STAVBE_SLO_STAVBE_tocka.shp',
        'stavbe_attributes',
        engine
    )
    total_imported += count
    
    # 2. Building-Parcel Links (critical for linking)
    count = import_from_zip(
        'gurs_data/KN_SLO_STAVBE_SLO_20260111/KN_SLO_STAVBE_SLO_stavbe_parcele_20260111.zip',
        'KN_SLO_STAVBE_SLO_STAVBE_PARCELE_poligon.shp',
        'stavbe_parcele',
        engine
    )
    total_imported += count
    
    logger.info("\n" + "=" * 60)
    logger.info(f"✨ BATCH IMPORT COMPLETE!")
    logger.info(f"   Total records imported: {total_imported:,}")

if __name__ == "__main__":
    main()

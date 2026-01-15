import os
import sys
import logging
import geopandas as gpd
from sqlalchemy import create_engine, text
import pandas as pd

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

DATABASE_URL = os.getenv('DATABASE_URL')

def get_engine():
    if not DATABASE_URL:
        logger.error("❌ DATABASE_URL missing.")
        sys.exit(1)
    return create_engine(DATABASE_URL)

def import_buildings(shapefile_path, engine):
    """Import building footprints from shapefile"""
    logger.info("\n🏢 STARTING BUILDINGS IMPORT...")
    logger.info(f"   📂 Reading: {os.path.basename(shapefile_path)}")
    
    try:
        # Read shapefile
        gdf = gpd.read_file(shapefile_path)
        logger.info(f"   ✅ Loaded {len(gdf)} buildings")
        
        # Check CRS
        if gdf.crs and gdf.crs.to_string() != "EPSG:3794":
            logger.info(f"   -> Reprojecting from {gdf.crs} to EPSG:3794...")
            gdf = gdf.to_crs("EPSG:3794")
        
        # Show columns
        logger.info(f"   ℹ️  Columns: {list(gdf.columns)}")
        
        # Sample data
        logger.info("\n   Sample building:")
        for col in gdf.columns[:5]:
            logger.info(f"      {col}: {gdf[col].iloc[0]}")
        
        # Map to database schema
        # stavbe table needs: stavba_id, parcela_id, leto_izgradnje, neto_tloris, geom
        logger.info("\n   -> Preparing for database import...")
        
        df_import = pd.DataFrame()
        
        # Try to map common column names
        if 'STAVBA_ID' in gdf.columns:
            df_import['stavba_id'] = gdf['STAVBA_ID']
        elif 'ID' in gdf.columns:
            df_import['stavba_id'] = gdf['ID']
        else:
            df_import['stavba_id'] = range(1, len(gdf) + 1)
        
        df_import['geom'] = gdf['geometry']
        
        # Add timestamps
        now = pd.Timestamp.now()
        df_import['created_at'] = now
        df_import['updated_at'] = now
        
        # Convert to GeoDataFrame
        gdf_import = gpd.GeoDataFrame(df_import, geometry='geom', crs="EPSG:3794")
        
        # Insert into database
        logger.info("   -> Inserting into database (this will take several minutes)...")
        
        gdf_import.to_postgis(
            'stavbe',
            engine,
            if_exists='append',
            index=False,
            dtype={'geom': 'Geometry'},
            chunksize=5000
        )
        
        logger.info(f"\n🎉 Successfully imported {len(gdf)} buildings!")
        
    except Exception as e:
        logger.error(f"   ❌ Error: {e}")
        import traceback
        traceback.print_exc()

def main():
    if len(sys.argv) < 2:
        print("Usage: python import_buildings.py <shapefile_path>")
        sys.exit(1)
    
    shapefile = sys.argv[1]
    engine = get_engine()
    
    import_buildings(shapefile, engine)
    
    logger.info("\n✨ Buildings import complete!")

if __name__ == "__main__":
    main()

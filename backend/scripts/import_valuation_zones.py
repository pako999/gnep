import os
import sys
import logging
import geopandas as gpd
from sqlalchemy import create_engine, text
import glob

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

DATABASE_URL = os.getenv('DATABASE_URL')

def get_engine():
    if not DATABASE_URL:
        logger.error("❌ DATABASE_URL missing.")
        sys.exit(1)
    return create_engine(DATABASE_URL)

def import_valuation_zones(data_dir, engine):
    """Import GURS valuation zone shapefiles"""
    logger.info("\n🏘️ STARTING VALUATION ZONES IMPORT...")
    
    # Find all zone shapefiles
    zone_files = glob.glob(os.path.join(data_dir, "emv_vredn_cone_17_VSE_2025", "*.shp"))
    
    if not zone_files:
        logger.error("❌ No valuation zone shapefiles found")
        return
    
    logger.info(f"   📂 Found {len(zone_files)} zone files")
    
    total_zones = 0
    
    for shp_file in zone_files:
        # Extract zone code from filename (e.g., emv_vredn_cone_DRZ.shp -> DRZ)
        zone_code = os.path.basename(shp_file).split('_')[-1].replace('.shp', '')
        
        logger.info(f"   -> Processing zone: {zone_code}")
        
        try:
            # Read shapefile
            gdf = gpd.read_file(shp_file)
            
            # Ensure correct CRS
            if gdf.crs and gdf.crs.to_string() != "EPSG:3794":
                gdf = gdf.to_crs("EPSG:3794")
            
            logger.info(f"      Loaded {len(gdf)} zones")
            
            # Prepare for database
            df_import = gdf.copy()
            df_import['zone_code'] = zone_code
            
            # Map zone codes to categories
            zone_categories = {
                'DRZ': 'Državne ceste',
                'GAR': 'Garaže',
                'GOZ': 'Gozd',
                'HIS': 'Hiše',
                'IND': 'Industrijske',
                'INP': 'Industrijske parcele',
                'KDS': 'Kmetijske',
                'KME': 'Kmetijske',
                'PNB': 'Poslovne stavbe',
                'PNE': 'Poslovne enote',
                'PNP': 'Poslovne parcele',
                'PPL': 'Parcele',
                'PPP': 'Parcele',
                'SDP': 'Stanovanja',
                'STA': 'Stanovanja',
                'STZ': 'Stanovanjske zgradbe',
                'TUR': 'Turistične'
            }
            
            df_import['zone_category'] = zone_categories.get(zone_code, 'Other')
            df_import['geom'] = df_import['geometry']
            
            # Select only needed columns
            cols_to_keep = ['zone_code', 'zone_category', 'geom']
            df_import = df_import[cols_to_keep]
            
            # Convert to GeoDataFrame
            gdf_import = gpd.GeoDataFrame(df_import, geometry='geom', crs="EPSG:3794")
            
            # Insert into database
            gdf_import.to_postgis(
                'valuation_zones',
                engine,
                if_exists='append',
                index=False,
                dtype={'geom': 'Geometry'}
            )
            
            total_zones += len(gdf)
            logger.info(f"      ✅ Imported {len(gdf)} zones")
            
        except Exception as e:
            logger.error(f"      ❌ Error importing {zone_code}: {e}")
    
    logger.info(f"\n🎉 Total zones imported: {total_zones}")

def create_schema(engine):
    """Create valuation tables if they don't exist"""
    logger.info("📋 Creating valuation schema...")
    
    with engine.connect() as conn:
        # Read and execute schema file
        schema_file = os.path.join(os.path.dirname(__file__), '..', 'database', 'valuation_schema.sql')
        if os.path.exists(schema_file):
            with open(schema_file, 'r') as f:
                schema_sql = f.read()
                conn.execute(text(schema_sql))
                conn.commit()
            logger.info("   ✅ Schema created")
        else:
            logger.warning("   ⚠️  Schema file not found, tables may not exist")

def main():
    if len(sys.argv) < 2:
        print("Usage: python import_valuation_zones.py <gurs_data_folder>")
        sys.exit(1)
    
    data_dir = sys.argv[1]
    engine = get_engine()
    
    # Create schema first
    create_schema(engine)
    
    # Import zones
    import_valuation_zones(data_dir, engine)
    
    logger.info("\n✨ Valuation zones import complete!")

if __name__ == "__main__":
    main()

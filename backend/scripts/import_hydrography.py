
import os
import sys
import logging
import zipfile
import tempfile
import glob
import geopandas as gpd
from sqlalchemy import create_engine, text
from geoalchemy2 import Geometry, WKTElement

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

DATABASE_URL = os.getenv('DATABASE_URL')

def get_engine():
    if not DATABASE_URL:
        logger.error("❌ DATABASE_URL missing.")
        sys.exit(1)
    return create_engine(DATABASE_URL)

def create_table(engine):
    """Create water_bodies table"""
    with engine.connect() as conn:
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS water_bodies (
                id SERIAL PRIMARY KEY,
                type VARCHAR(50),
                name VARCHAR(255),
                geom GEOMETRY(MultiPolygon, 3794),
                original_file VARCHAR(255)
            );
            CREATE INDEX IF NOT EXISTS idx_water_bodies_geom ON water_bodies USING GIST(geom);
        """))
        conn.commit()

def import_zip(zip_path, engine):
    """Import a single ZIP file containing Shapefiles"""
    filename = os.path.basename(zip_path)
    logger.info(f"📦 Processing archive: {filename}")
    
    with tempfile.TemporaryDirectory() as tmpdirname:
        # Unzip
        try:
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(tmpdirname)
        except Exception as e:
            logger.error(f"   ❌ Failed to unzip {filename}: {e}")
            return

        # Find .shp files
        shp_files = glob.glob(os.path.join(tmpdirname, '**', '*.shp'), recursive=True)
        
        if not shp_files:
            logger.warning(f"   ⚠️ No .shp files found in {filename}")
            return

        for shp_file in shp_files:
            shp_name = os.path.basename(shp_file)
            logger.info(f"   📄 Reading Shapefile: {shp_name}")
            
            try:
                gdf = gpd.read_file(shp_file)
                
                if gdf.empty:
                    logger.warning("      ⚠️ Unknown CRS or empty file. Skipping.")
                    continue

                # FX: Explicitly set geometry column if it's named 'geom' or something else
                # GURS often uses 'geom' or 'geometry'
                if 'geom' in gdf.columns:
                     gdf = gdf.set_geometry('geom')
                elif 'geometry' not in gdf.columns:
                    # Fallback: try to find any geometry column
                    geom_cols = gdf.select_dtypes(include=['geometry']).columns
                    if len(geom_cols) > 0:
                        gdf = gdf.set_geometry(geom_cols[0])
                    else:
                        logger.error(f"      ❌ No geometry column found in {shp_name}")
                        continue

                # Ensure CRS is correct (GURS is usually EPSG:3794 or 3912)
                if gdf.crs is None:
                    # Assume 3794 if not set, or let user define
                    gdf.set_crs(epsg=3794, inplace=True) 
                
                # We need to standardize columns
                # GURS usually has 'IME' for name. 
                # We will map whatever we can to our schema.
                
                target_gdf = gpd.GeoDataFrame()
                target_gdf['geom'] = gdf.geometry
                target_gdf['original_file'] = filename
                
                # Infer type from filename
                if 'TEKOCE' in filename:
                    target_gdf['type'] = 'RUNNING_WATER'
                elif 'STOJECE' in filename:
                    target_gdf['type'] = 'STANDING_WATER'
                elif 'MOKROTNE' in filename:
                    target_gdf['type'] = 'WETLAND'
                elif 'MORJE' in filename:
                    target_gdf['type'] = 'SEA'
                else:
                    target_gdf['type'] = 'OTHER'

                # Try to find Name field
                name_cols = [c for c in gdf.columns if 'IME' in c.upper() or 'NAME' in c.upper()]
                if name_cols:
                    target_gdf['name'] = gdf[name_cols[0]]
                else:
                    target_gdf['name'] = None

                # Write to DB
                logger.info(f"      💾 Writing {len(target_gdf)} features to DB...")
                target_gdf.to_postgis('water_bodies', engine, if_exists='append', index=False, dtype={'geom': Geometry('MultiPolygon', srid=3794)})
                logger.info("      ✅ Done.")

            except Exception as e:
                logger.error(f"      ❌ Error importing {shp_name}: {e}")

def main():
    if len(sys.argv) < 2:
        print("Usage: python import_hydrography.py <data_folder>")
        sys.exit(1)

    data_dir = sys.argv[1]
    engine = get_engine()
    
    # Initialize DB
    create_table(engine)
    
    # Find all ZIPs
    # Prioritize Polygons (_P_)
    search_pattern = os.path.join(data_dir, "**", "*_P_*.zip")
    zip_files = glob.glob(search_pattern, recursive=True)
    
    logger.info(f"Found {len(zip_files)} ZIP files to import.")
    
    for zip_file in zip_files:
        import_zip(zip_file, engine)
        
    logger.info("🌊 Hydrography Import Complete!")

if __name__ == "__main__":
    main()

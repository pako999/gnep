
import os
import sys
import logging
import geopandas as gpd
from sqlalchemy import create_engine
from geoalchemy2 import Geometry, WKTElement

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Database connection
DATABASE_URL = os.getenv('DATABASE_URL')

def import_data(file_path, table_name):
    """
    Import geospatial file to PostGIS database
    """
    if not DATABASE_URL:
        logger.error("DATABASE_URL environment variable is not set.")
        return

    if not os.path.exists(file_path):
        logger.error(f"File not found: {file_path}")
        return

    logger.info(f"Reading file: {file_path}...")
    try:
        # Read file using geopandas (supports shp, gpkg, geojson, etc.)
        gdf = gpd.read_file(file_path)
        logger.info(f"Loaded {len(gdf)} rows matching CRS: {gdf.crs}")

        # Ensure CRS is EPSG:3794 (Slovenian Grid)
        if gdf.crs and gdf.crs.to_string() != "EPSG:3794":
            logger.info("Reprojecting to EPSG:3794...")
            gdf = gdf.to_crs("EPSG:3794")

        # Rename columns to match our schema if necessary
        # This mapping depends on the exact GURS file format
        # Example mapping (you might need to adjust this based on the file)
        column_mapping = {
            'PARCELA_ID': 'parcela_stevilka', # Adjust these based on actual columns
            'KO_SIFRA': 'ko_sifra',
            'KO_IME': 'ko_ime',
            'POV_PARC': 'povrsina'
        }
        # gdf = gdf.rename(columns=column_mapping)

        # Create engine
        engine = create_engine(DATABASE_URL)

        # Write to PostGIS
        logger.info(f"Writing to table {table_name}...")
        gdf.to_postgis(
            table_name,
            engine,
            if_exists='append', # or 'replace'
            index=False,
            dtype={'geom': Geometry('POLYGON', srid=3794)}
        )
        logger.info("Import successful!")

    except Exception as e:
        logger.error(f"Error importing data: {e}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python import_gurs.py <path_to_file>")
        sys.exit(1)
    
    file_path = sys.argv[1]
    # Default to 'parcele' table, but could be 'stavbe'
    import_data(file_path, 'parcele')

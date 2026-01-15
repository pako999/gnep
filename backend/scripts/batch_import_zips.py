import os
import sys
import logging
import geopandas as gpd
from sqlalchemy import create_engine
import pandas as pd

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Add backend to path to import connection.py
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
try:
    from database.connection import get_engine
except ImportError:
    # Fallback if run from root
    from backend.database.connection import get_engine

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
        
        # Rename columns to match schema (handle common GURS variants)
        column_map = {
            'PAR_ST': 'parcela_stevilka',
            'PARCELA_ST': 'parcela_stevilka',
            'KO_SIFRA': 'ko_sifra', 
            'KO_IME': 'ko_ime',
            'POVRSINA': 'povrsina',
            'POV_PARC': 'povrsina',
            'STAVBA_ST': 'stavba_stevilka',
            'ST_ETAZ': 'stevilo_etaz',
            'LETO_IZG': 'leto_izgradnje',
            'NETO_TLOR': 'neto_tloris',
            'DELEZ': 'delez',
            'VRSTA': 'vrsta',
            'IME': 'ime',
            'PRIIMEK': 'priimek',
            'NAZIV': 'ime' # For companies
        }
        gdf.rename(columns=column_map, inplace=True)
        
        # Ensure we only have lowercase columns (Postgres convention)
        gdf.columns = [c.lower() for c in gdf.columns]
        
        logger.info(f"   -> Mapped columns: {list(gdf.columns)[:10]}")

        # Set geometry column and rename
        if 'geometry' in gdf.columns:
            gdf = gdf.set_geometry('geometry')
        gdf = gdf.rename_geometry('geom')
        
        # Add metadata
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

def import_from_shapefile(shapefile_path, table_name, engine, zone_type=None):
    """Import unzipped shapefile directly"""
    logger.info(f"\n📂 Importing Shapefile: {os.path.basename(shapefile_path)}")
    
    try:
        gdf = gpd.read_file(shapefile_path)
        logger.info(f"   ✅ Loaded {len(gdf)} records")
        
        if len(gdf) == 0:
            logger.warning("   ⚠️  Shapefile is empty, skipping.")
            return 0
            
        # Reproject if needed
        if gdf.crs and gdf.crs.to_string() != "EPSG:3794":
            logger.info(f"   -> Reprojecting to EPSG:3794...")
            gdf = gdf.to_crs("EPSG:3794")
        
        # Set geometry column and rename
        gdf = gdf.set_geometry('geometry')
        gdf = gdf.rename_geometry('geom')
        
        # Add metadata
        now = pd.Timestamp.now()
        gdf['created_at'] = now
        gdf['updated_at'] = now
        if zone_type:
            gdf['zone_type'] = zone_type
        
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
        
        logger.info(f"   🎉 Imported {len(gdf)} records to {table_name}")
        return len(gdf)
        
    except Exception as e:
        logger.error(f"   ❌ Error: {e}")
        return 0

def main():
    engine = get_engine()
    
    logger.info("🚀 BATCH IMPORT FROM ZIP FILES")
    logger.info("=" * 60)
    
    total_imported = 0
    
    # 1. Parcels (Base Layer)
    count = import_from_zip(
        'gurs_data/KN_SLO_STAVBE_SLO_20260111/KN_SLO_PARCELE_SLO_20260111/KN_SLO_PARCELE_SLO_parcele_20260111.zip',
        'KN_SLO_PARCELE_SLO_PARCELE_poligon.shp',
        'parcele',
        engine
    )
    total_imported += count

    # 2. Buildable Parcels (Gradbene Parcele)
    count = import_from_zip(
        'gurs_data/KN_SLO_STAVBE_SLO_20260111/KN_SLO_PARCELE_SLO_20260111/KN_SLO_PARCELE_SLO_gradbene_parcele_20260111.zip',
        'KN_SLO_PARCELE_SLO_GRADBENE_PARCELE.shp',
        'gradbene_parcele',
        engine
    )
    total_imported += count

    # 3. Valuation Zones (EMV)
    emv_dir = 'gurs_data/KN_SLO_STAVBE_SLO_20260111/emv_vredn_cone_17_VSE_2025'
    if os.path.exists(emv_dir):
        # Import key zones: Residential (STA), House (HIS), Industrial (IND), Tourism (TUR), Mixed (KME)
        zones = ['STA', 'HIS', 'IND', 'TUR', 'KME']
        for zone in zones:
            shp_path = os.path.join(emv_dir, f'emv_vredn_cone_{zone}.shp')
            if os.path.exists(shp_path):
                count = import_from_shapefile(shp_path, 'valuation_zones', engine, zone_type=zone)
                total_imported += count
    else:
        logger.warning(f"⚠️ Valuation zones directory not found: {emv_dir}")

    # 4. Building Attributes (critical for search)
    count = import_from_zip(
        'gurs_data/KN_SLO_STAVBE_SLO_20260111/KN_SLO_STAVBE_SLO_stavbe_20260111.zip',
        'KN_SLO_STAVBE_SLO_STAVBE_tocka.shp',
        'stavbe_attributes',
        engine
    )
    total_imported += count
    
    # 5. Building-Parcel Links (critical for linking)
    count = import_from_zip(
        'gurs_data/KN_SLO_STAVBE_SLO_20260111/KN_SLO_STAVBE_SLO_stavbe_parcele_20260111.zip',
        'KN_SLO_STAVBE_SLO_STAVBE_PARCELE_poligon.shp',
        'stavbe_parcele',
        engine
    )
    total_imported += count
    
    # 6. Hydrography - Flowing Water (Lines)
    count = import_from_zip(
        'gurs_data/DTM_SLO_HIDROGRAFIJA_20260110/DTM_SLO_HIDROGRAFIJA_HY_TEKOCE_VODE_L_20260110.zip',
        'DTM_SLO_HIDROGRAFIJA_HY_TEKOCEVODE_L_line.shp',
        'water_flowing_lines',
        engine
    )
    total_imported += count

    # 7. Hydrography - Flowing Water (Polygons)
    count = import_from_zip(
        'gurs_data/DTM_SLO_HIDROGRAFIJA_20260110/DTM_SLO_HIDROGRAFIJA_HY_TEKOCE_VODE_P_20260110.zip',
        'DTM_SLO_HIDROGRAFIJA_HY_TEKOCEVODE_P_poligon.shp',
        'water_flowing_polygons',
        engine
    )
    total_imported += count

    # 8. Hydrography - Standing Water
    count = import_from_zip(
        'gurs_data/DTM_SLO_HIDROGRAFIJA_20260110/DTM_SLO_HIDROGRAFIJA_HY_STOJECE_VODE_P_20260110.zip',
        'DTM_SLO_HIDROGRAFIJA_HY_STOJECEVODE_P_poligon.shp',
        'water_standing',
        engine
    )
    total_imported += count
    
    logger.info("\n" + "=" * 60)
    logger.info(f"✨ BATCH IMPORT COMPLETE!")
    logger.info(f"   Total records imported: {total_imported:,}")

if __name__ == "__main__":
    main()

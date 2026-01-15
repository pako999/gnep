import os
import sys
import logging
import rasterio
from rasterio.warp import calculate_default_transform, reproject, Resampling
from sqlalchemy import create_engine, text
import numpy as np

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

DATABASE_URL = os.getenv('DATABASE_URL')

def get_engine():
    if not DATABASE_URL:
        logger.error("❌ DATABASE_URL missing.")
        sys.exit(1)
    return create_engine(DATABASE_URL)

def create_terrain_tables(engine):
    """Create tables for terrain analysis results"""
    logger.info("📋 Creating terrain tables...")
    
    schema = """
    -- Terrain cache for quick lookups
    CREATE TABLE IF NOT EXISTS terrain_cache (
        id SERIAL PRIMARY KEY,
        parcela_id INTEGER REFERENCES parcele(id),
        min_elevation DECIMAL(8, 2),
        max_elevation DECIMAL(8, 2),
        avg_elevation DECIMAL(8, 2),
        avg_slope DECIMAL(5, 2),
        aspect VARCHAR(10),
        flood_risk VARCHAR(20),
        solar_hours DECIMAL(5, 2),
        buildable_area_m2 DECIMAL(10, 2),
        cached_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(parcela_id)
    );
    
    CREATE INDEX IF NOT EXISTS idx_terrain_cache_parcela ON terrain_cache(parcela_id);
    CREATE INDEX IF NOT EXISTS idx_terrain_cache_flood ON terrain_cache(flood_risk);
    
    -- Analysis results storage
    CREATE TABLE IF NOT EXISTS terrain_analyses (
        id SERIAL PRIMARY KEY,
        parcela_id INTEGER REFERENCES parcele(id),
        analysis_type VARCHAR(50) NOT NULL,
        result_data JSONB,
        visualization_url TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        user_id INTEGER
    );
    
    CREATE INDEX IF NOT EXISTS idx_terrain_analyses_parcela ON terrain_analyses(parcela_id);
    CREATE INDEX IF NOT EXISTS idx_terrain_analyses_type ON terrain_analyses(analysis_type);
    CREATE INDEX IF NOT EXISTS idx_terrain_analyses_date ON terrain_analyses(created_at);
    
    COMMENT ON TABLE terrain_cache IS 'Cached terrain metrics for fast retrieval';
    COMMENT ON TABLE terrain_analyses IS 'Historical terrain analysis results for users';
    """
    
    with engine.connect() as conn:
        conn.execute(text(schema))
        conn.commit()
    
    logger.info("   ✅ Terrain tables created")

def process_dtm_tile(dtm_file):
    """Process a single DTM tile and extract statistics"""
    logger.info(f"   -> Processing: {os.path.basename(dtm_file)}")
    
    try:
        with rasterio.open(dtm_file) as src:
            # Read elevation data
            elevation = src.read(1)
            
            # Calculate basic statistics
            stats = {
                'min': float(np.nanmin(elevation)),
                'max': float(np.nanmax(elevation)),
                'mean': float(np.nanmean(elevation)),
                'std': float(np.nanstd(elevation))
            }
            
            logger.info(f"      Elevation: {stats['min']:.1f}m - {stats['max']:.1f}m (avg: {stats['mean']:.1f}m)")
            
            return stats
            
    except Exception as e:
        logger.error(f"      ❌ Error: {e}")
        return None

def import_dtm_data(data_dir, engine):
    """Import DTM (Digital Terrain Model) data"""
    logger.info("\n🗻 STARTING DTM IMPORT...")
    
    # Look for DTM files (various possible formats)
    dtm_patterns = ['*DTM*.tif', '*dmv*.tif', '*DEM*.tif', '*elevation*.tif']
    dtm_files = []
    
    for pattern in dtm_patterns:
        import glob
        found = glob.glob(os.path.join(data_dir, '**', pattern), recursive=True)
        dtm_files.extend(found)
    
    if not dtm_files:
        logger.warning("   ⚠️  No DTM files found")
        logger.info("   Looking for common DTM file patterns:")
        logger.info("     - *DTM*.tif")
        logger.info("     - *dmv*.tif (Digitalni model višin)")
        logger.info("     - *DEM*.tif")
        return
    
    logger.info(f"   📂 Found {len(dtm_files)} DTM files")
    
    # Process first few tiles to verify
    for dtm_file in dtm_files[:3]:
        process_dtm_tile(dtm_file)
    
    logger.info(f"\n   ℹ️  DTM files are ready for processing")
    logger.info(f"   Next step: Implement terrain analysis algorithms")

def main():
    if len(sys.argv) < 2:
        print("Usage: python import_dtm.py <gurs_data_folder>")
        sys.exit(1)
    
    data_dir = sys.argv[1]
    engine = get_engine()
    
    # Create tables
    create_terrain_tables(engine)
    
    # Import DTM
    import_dtm_data(data_dir, engine)
    
    logger.info("\n✨ DTM import preparation complete!")
    logger.info("   Ready to implement terrain analysis features")

if __name__ == "__main__":
    main()

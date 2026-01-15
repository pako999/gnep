
from sqlalchemy import create_engine, text
import os
import sys

DATABASE_URL = os.getenv('DATABASE_URL')
if DATABASE_URL and DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

if not DATABASE_URL:
    print("DATABASE_URL missing")
    sys.exit(1)

engine = create_engine(DATABASE_URL)

query = text("""
    WITH mvtgeom AS (
        SELECT 
            id, 
            parcela_stevilka, 
            ko_ime,
            ST_AsMVTGeom(
                ST_Transform(ST_SetSRID(geom, 3794), 3857), 
                ST_TileEnvelope(14, 8933, 5849)
            ) AS geom
        FROM parcele
        WHERE ST_Intersects(
            ST_Transform(ST_SetSRID(geom, 3794), 3857), 
            ST_TileEnvelope(14, 8933, 5849)
        )
    )
    SELECT ST_AsMVT(mvtgeom.*) FROM mvtgeom;
""")

try:
    with engine.connect() as conn:
        print("Executing diagnostic MVT query...")
        result = conn.execute(query).fetchone()
        if result:
            print(f"Success! Tile size: {len(result[0])} bytes")
        else:
            print("No data returned but query succeeded.")
except Exception as e:
    print(f"❌ SQL Error: {e}")
    import traceback
    traceback.print_exc()

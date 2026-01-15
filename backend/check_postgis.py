
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

def run_diagnostic():
    try:
        with engine.connect() as conn:
            print("--- Extension Diagnostic ---")
            result = conn.execute(text("SELECT extname FROM pg_extension;")).fetchall()
            extensions = [r[0] for r in result]
            print(f"Installed Extensions: {extensions}")
            
            if 'postgis' not in extensions:
                print("⚠️ PostGIS is MISSING! Attempting to enable...")
                try:
                    conn.execute(text("CREATE EXTENSION IF NOT EXISTS postgis;"))
                    conn.commit()
                    print("✅ CREATE EXTENSION postgis succeeded!")
                except Exception as e:
                    print(f"❌ Failed to create extension: {e}")
            else:
                print("✅ PostGIS extension is installed.")
                
            # Verify version
            try:
                version = conn.execute(text("SELECT PostGIS_Full_Version();")).fetchone()
                print(f"PostGIS Version: {version[0]}")
            except Exception as e:
                print(f"❌ Error getting version: {e}")

            print("\n--- Search Path ---")
            path = conn.execute(text("SHOW search_path;")).fetchone()
            print(f"Search Path: {path[0]}")

    except Exception as e:
        print(f"❌ Global Diagnostic Error: {e}")

if __name__ == "__main__":
    run_diagnostic()

import os
import sys
from sqlalchemy import text

# Add backend to path to import connection.py
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from database.connection import get_engine

def run_schema_init():
    print("🚀 Initializing Database Schema...")
    schema_path = os.path.join(os.path.dirname(__file__), '../database/schema.sql')
    
    if not os.path.exists(schema_path):
        print(f"❌ Schema file not found: {schema_path}")
        return

    with open(schema_path, 'r') as f:
        schema_sql = f.read()

    engine = get_engine()
    
    try:
        with engine.connect() as conn:
            # Execute the entire schema as one block if possible, or split if needed.
            # SQLAlchemy text() usually handles multiple statements for postgres.
            conn.execute(text(schema_sql))
            conn.commit()
            print("✅ Schema initialized successfully!")
    except Exception as e:
        print(f"❌ Error initializing schema: {e}")

if __name__ == "__main__":
    run_schema_init()

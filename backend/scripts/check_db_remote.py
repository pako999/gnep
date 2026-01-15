import os
import sys
from sqlalchemy import create_engine, text

# Add backend to path to import connection.py
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from database.connection import get_engine

def check():
    print("Testing connection...")
    try:
        engine = get_engine()
        with engine.connect() as conn:
            # Check version
            res = conn.execute(text("SELECT version();")).fetchone()
            print(f"✅ Connected! Version: {res[0]}")
            
            # Check if table 'parcele' exists
            res = conn.execute(text("SELECT to_regclass('public.parcele');")).fetchone()
            if res[0]:
                print("✅ Table 'parcele' exists!")
            else:
                print("❌ Table 'parcele' DOES NOT exist.")
    except Exception as e:
        print(f"❌ Check Failed: {e}")

if __name__ == "__main__":
    check()

"""
Database Connection Utilities for PropertyDetective
Handles PostgreSQL/PostGIS connections using SQLAlchemy
"""

import os
from contextlib import contextmanager
from typing import Generator

from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import QueuePool
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class DatabaseConfig:
    """Database configuration from environment variables"""
    
    def __init__(self):
        # Check for DATABASE_URL first (Railway, Render, Heroku style)
        database_url = os.getenv('DATABASE_URL')
        
        if database_url:
            # Normalize postgres:// to postgresql:// for SQLAlchemy 1.4+ compatibility
            if database_url.startswith("postgres://"):
                database_url = database_url.replace("postgres://", "postgresql://", 1)
            # Use the full connection string directly
            self._connection_string = database_url
            self.echo = os.getenv('DB_ECHO', 'false').lower() == 'true'
        else:
            # Fall back to individual environment variables
            self.host = os.getenv('DB_HOST', 'localhost')
            self.port = os.getenv('DB_PORT', '5432')
            self.database = os.getenv('DB_NAME', 'gurs_gnep')
            self.user = os.getenv('DB_USER', 'postgres')
            self.password = os.getenv('DB_PASSWORD', '')
            self.echo = os.getenv('DB_ECHO', 'false').lower() == 'true'
            self._connection_string = None
    
    @property
    def connection_string(self) -> str:
        """Generate PostgreSQL connection string"""
        if self._connection_string:
            return self._connection_string
        return (
            f"postgresql://{self.user}:{self.password}@"
            f"{self.host}:{self.port}/{self.database}"
        )


# Global engine and session factory
_engine: Engine = None
_SessionFactory: sessionmaker = None


def initialize_database(config: DatabaseConfig = None) -> Engine:
    """
    Initialize database engine and session factory
    
    Args:
        config: DatabaseConfig instance (uses default if None)
    
    Returns:
        SQLAlchemy Engine instance
    """
    global _engine, _SessionFactory
    
    if config is None:
        config = DatabaseConfig()
    
    # Create engine with connection pooling
    _engine = create_engine(
        config.connection_string,
        echo=config.echo,
        poolclass=QueuePool,
        pool_size=10,
        max_overflow=20,
        pool_pre_ping=True,  # Verify connections before using
    )
    
    # PostGIS extension - Railway PostgreSQL already has it installed
    # Commenting out auto-creation to avoid permission issues
    # @event.listens_for(_engine, "connect")
    # def load_postgis(dbapi_conn, connection_record):
    #     """Ensure PostGIS is loaded"""
    #     cursor = dbapi_conn.cursor()
    #     cursor.execute("CREATE EXTENSION IF NOT EXISTS postgis;")
    #     cursor.close()
    #     dbapi_conn.commit()
    
    # Create session factory
    _SessionFactory = sessionmaker(bind=_engine)
    
    return _engine


def get_engine() -> Engine:
    """
    Get database engine (initializes if needed)
    
    Returns:
        SQLAlchemy Engine instance
    """
    global _engine
    if _engine is None:
        initialize_database()
    return _engine


def get_session() -> Session:
    """
    Get a new database session
    
    Returns:
        SQLAlchemy Session instance
    
    Note:
        Remember to close the session when done or use session_scope context manager
    """
    global _SessionFactory
    if _SessionFactory is None:
        initialize_database()
    return _SessionFactory()


@contextmanager
def session_scope() -> Generator[Session, None, None]:
    """
    Provide a transactional scope for database operations
    
    Usage:
        with session_scope() as session:
            results = session.query(Parcela).all()
    
    Yields:
        SQLAlchemy Session instance
    """
    session = get_session()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def test_connection() -> bool:
    """
    Test database connection
    
    Returns:
        True if connection successful, False otherwise
    """
    try:
        engine = get_engine()
        with engine.connect() as conn:
            result = conn.execute("SELECT version();")
            row = result.fetchone()
            print(f"✓ Database connection successful: {row[0]}")
            return True
    except Exception as e:
        print(f"✗ Database connection failed: {e}")
        return False


def check_database_setup(engine: Engine):
    """
    Verify database has PostGIS and SRID 3794 (Slovenian Grid)
    """
    try:
        with engine.connect() as conn:
            # 1. Check PostGIS
            conn.execute("CREATE EXTENSION IF NOT EXISTS postgis;")
            
            # 2. Check/Insert SRID 3794
            # Using raw SQL to avoid dependency on geoalchemy2 in this check
            check_srid = conn.execute("SELECT srid FROM spatial_ref_sys WHERE srid = 3794;").fetchone()
            
            if not check_srid:
                print("⚠ SRID 3794 missing. Inserting...")
                conn.execute("""
                    INSERT INTO spatial_ref_sys (srid, auth_name, auth_srid, srtext, proj4text)
                    VALUES (3794, 'EPSG', 3794, 
                    'PROJCS["D96 / TM",GEOGCS["D96",DATUM["Drzavni_koordinatni_sistem_1996",SPHEROID["GRS 1980",6378137,298.257222101,AUTHORITY["EPSG","7019"]],AUTHORITY["EPSG","6763"]],PRIMEM["Greenwich",0,AUTHORITY["EPSG","8901"]],UNIT["degree",0.0174532925199433,AUTHORITY["EPSG","9122"]],AUTHORITY["EPSG","4796"]],PROJECTION["Transverse_Mercator"],PARAMETER["latitude_of_origin",0],PARAMETER["central_meridian",15],PARAMETER["scale_factor",0.9999],PARAMETER["false_easting",500000],PARAMETER["false_northing",-5000000],UNIT["metre",1,AUTHORITY["EPSG","9001"]],AXIS["Northing",NORTH],AXIS["Easting",EAST],AUTHORITY["EPSG","3794"]]', 
                    '+proj=tmerc +lat_0=0 +lon_0=15 +k=0.9999 +x_0=500000 +y_0=-5000000 +ellps=GRS80 +towgs84=0,0,0,0,0,0,0 +units=m +no_defs');
                """)
                print("✓ SRID 3794 inserted.")
            else:
                print("✓ SRID 3794 exists.")
                
            conn.commit()
            return True
            
    except Exception as e:
        print(f"✗ Database setup check failed: {e}")
        return False


if __name__ == "__main__":
    # Test connection when run directly
    test_connection()

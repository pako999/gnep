
"""
Database Seeding Script for GNEP
Populates the database with sample Slovenian cadastral data for demonstration.
"""
import logging
import sys
import os

# Add parent directory to path to allow imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.connection import session_scope
from property_detective.models import Parcela, Stavba
from sqlalchemy import text

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def seed_database():
    """Seed the database with sample data"""
    logger.info("Starting database seeding...")
    
    with session_scope() as session:
        # Check if data already exists
        count = session.query(Parcela).count()
        if count > 0:
            logger.info(f"Database already contains {count} parcels. Skipping seed.")
            return

        # ==========================================
        # 1. Ljubljana Center (House)
        # ==========================================
        lj_parcel = Parcela(
            parcela_stevilka="123/4",
            ko_sifra="1723",
            ko_ime="Ljubljana Center",
            povrsina=542.0,
            # Point in Ljubljana Center (approximate)
            geom="POLYGON((460500 102500, 460520 102500, 460520 102525, 460500 102525, 460500 102500))"
        )
        session.add(lj_parcel)
        session.flush() # Get ID

        lj_building = Stavba(
            parcela_id=lj_parcel.id,
            stavba_stevilka="1122",
            leto_izgradnje=1974,
            neto_tloris=185.4,
            stevilo_etaz=2,
            tip="Stanovanjska stavba",
            naslov_ulica="Slovenska cesta",
            naslov_hisna_st="10",
            naslov_naselje="Ljubljana",
            naslov_posta="Ljubljana",
            naslov_postna_st="1000"
        )
        session.add(lj_building)

        # ==========================================
        # 2. Maribor Center (Apartment Building)
        # ==========================================
        mb_parcel = Parcela(
            parcela_stevilka="88/2",
            ko_sifra="657",
            ko_ime="Maribor Grad",
            povrsina=1250.5,
            geom="POLYGON((550500 155500, 550550 155500, 550550 155550, 550500 155550, 550500 155500))"
        )
        session.add(mb_parcel)
        session.flush()

        mb_building = Stavba(
            parcela_id=mb_parcel.id,
            stavba_stevilka="3344",
            leto_izgradnje=1980, # Approximate for "without exact year" matching
            neto_tloris=4000.0, # Multi-apartment building
            stevilo_etaz=5,
            tip="Večstanovanjska stavba",
            naslov_ulica="Gosposka ulica",
            naslov_hisna_st="5",
            naslov_naselje="Maribor",
            naslov_posta="Maribor",
            naslov_postna_st="2000"
        )
        session.add(mb_building)

        # ==========================================
        # 3. Bled (Land Plot)
        # ==========================================
        bled_parcel = Parcela(
            parcela_stevilka="999/1",
            ko_sifra="2156",
            ko_ime="Bled",
            povrsina=3200.0,
            geom="POLYGON((430500 135500, 430600 135500, 430600 135600, 430500 135600, 430500 135500))"
        )
        session.add(bled_parcel)
        # No building for land plot

        # ==========================================
        # 4. Kranj (Modern House)
        # ==========================================
        kranj_parcel = Parcela(
            parcela_stevilka="44/7",
            ko_sifra="2100",
            ko_ime="Kranj",
            povrsina=876.3,
            geom="POLYGON((450500 125500, 450530 125500, 450530 125530, 450500 125530, 450500 125500))"
        )
        session.add(kranj_parcel)
        session.flush()

        kranj_building = Stavba(
            parcela_id=kranj_parcel.id,
            stavba_stevilka="5566",
            leto_izgradnje=2018,
            neto_tloris=234.7,
            stevilo_etaz=2,
            tip="Stanovanjska stavba",
            naslov_ulica="Cesta Staneta Žagarja",
            naslov_hisna_st="22",
            naslov_naselje="Kranj",
            naslov_posta="Kranj",
            naslov_postna_st="4000"
        )
        session.add(kranj_building)
        
        logger.info("Database seeding completed successfully!")

if __name__ == "__main__":
    try:
        seed_database()
    except Exception as e:
        logger.error(f"Error seeding database: {e}")
        # Print full stack trace for debugging
        import traceback
        traceback.print_exc()

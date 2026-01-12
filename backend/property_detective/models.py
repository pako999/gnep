"""
SQLAlchemy ORM Models for GURS Cadastral Data
Maps to PostGIS database tables
"""

from datetime import datetime
from typing import Optional, List

from sqlalchemy import Column, Integer, String, Numeric, DateTime, ForeignKey
from sqlalchemy.orm import DeclarativeBase, relationship, Mapped, mapped_column
from geoalchemy2 import Geometry
from geoalchemy2.shape import to_shape
from shapely.geometry import shape


class Base(DeclarativeBase):
    """Base class for all ORM models"""
    pass


class Parcela(Base):
    """
    Land Parcel (Parcela) Model
    Represents cadastral parcels from GURS database
    """
    __tablename__ = 'parcele'
    
    # Primary key
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    
    # Parcel identification
    parcela_stevilka: Mapped[str] = mapped_column(String(50), nullable=False)
    ko_sifra: Mapped[str] = mapped_column(String(10), nullable=False)
    ko_ime: Mapped[str] = mapped_column(String(100), nullable=False)
    
    # Parcel properties
    povrsina: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    
    # Spatial data (Slovenian coordinate system D96/TM - EPSG:3794)
    geom = Column(Geometry('POLYGON', srid=3794))
    
    # Metadata
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    stavbe: Mapped[List["Stavba"]] = relationship("Stavba", back_populates="parcela", cascade="all, delete-orphan")
    lastniki: Mapped[List["Lastnik"]] = relationship("Lastnik", back_populates="parcela", cascade="all, delete-orphan")
    
    def __repr__(self) -> str:
        return f"<Parcela(id={self.id}, stevilka={self.parcela_stevilka}, ko={self.ko_ime}, povrsina={self.povrsina}m²)>"
    
    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization"""
        return {
            'id': self.id,
            'parcela_stevilka': self.parcela_stevilka,
            'ko_sifra': self.ko_sifra,
            'ko_ime': self.ko_ime,
            'povrsina': float(self.povrsina),
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }
    
    def get_geometry_wgs84(self):
        """Get geometry converted to WGS84 (EPSG:4326) for web mapping"""
        if self.geom:
            # Convert from D96/TM to WGS84
            from geoalchemy2.functions import ST_Transform
            return ST_Transform(self.geom, 4326)
        return None


class Stavba(Base):
    """
    Building (Stavba) Model
    Represents buildings registered in GURS cadastre
    """
    __tablename__ = 'stavbe'
    
    # Primary key
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    
    # Foreign key to parcel
    parcela_id: Mapped[int] = mapped_column(Integer, ForeignKey('parcele.id', ondelete='CASCADE'), nullable=False)
    
    # Building identification
    stavba_stevilka: Mapped[Optional[str]] = mapped_column(String(50))
    
    # Building properties (key fields for matching)
    leto_izgradnje: Mapped[Optional[int]] = mapped_column(Integer)
    neto_tloris: Mapped[Optional[float]] = mapped_column(Numeric(10, 2))
    stevilo_etaz: Mapped[Optional[int]] = mapped_column(Integer)
    tip: Mapped[Optional[str]] = mapped_column(String(50))
    
    # Address information
    naslov_ulica: Mapped[Optional[str]] = mapped_column(String(200))
    naslov_hisna_st: Mapped[Optional[str]] = mapped_column(String(20))
    naslov_naselje: Mapped[Optional[str]] = mapped_column(String(100))
    naslov_posta: Mapped[Optional[str]] = mapped_column(String(50))
    naslov_postna_st: Mapped[Optional[str]] = mapped_column(String(10))
    
    # Metadata
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    parcela: Mapped["Parcela"] = relationship("Parcela", back_populates="stavbe")
    
    def __repr__(self) -> str:
        return f"<Stavba(id={self.id}, leto={self.leto_izgradnje}, tloris={self.neto_tloris}m²)>"
    
    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization"""
        return {
            'id': self.id,
            'parcela_id': self.parcela_id,
            'stavba_stevilka': self.stavba_stevilka,
            'leto_izgradnje': self.leto_izgradnje,
            'neto_tloris': float(self.neto_tloris) if self.neto_tloris else None,
            'stevilo_etaz': self.stevilo_etaz,
            'tip': self.tip,
            'naslov': self.get_full_address(),
        }
    
    def get_full_address(self) -> Optional[str]:
        """Get formatted full address"""
        parts = []
        if self.naslov_ulica:
            parts.append(self.naslov_ulica)
        if self.naslov_hisna_st:
            parts.append(self.naslov_hisna_st)
        if self.naslov_naselje:
            parts.append(self.naslov_naselje)
        return ', '.join(parts) if parts else None


class Lastnik(Base):
    """
    Owner (Lastnik) Model
    Represents ownership information for parcels
    """
    __tablename__ = 'lastniki'
    
    # Primary key
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    
    # Foreign key to parcel
    parcela_id: Mapped[int] = mapped_column(Integer, ForeignKey('parcele.id', ondelete='CASCADE'), nullable=False)
    
    # Owner information
    ime: Mapped[Optional[str]] = mapped_column(String(200))
    vrsta: Mapped[Optional[str]] = mapped_column(String(50))  # fizična/pravna oseba
    
    # Ownership details
    delez: Mapped[Optional[str]] = mapped_column(String(50))  # e.g., "1/1", "1/2"
    pravica: Mapped[Optional[str]] = mapped_column(String(100))  # lastništvo, služnost, etc.
    
    # Metadata
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    parcela: Mapped["Parcela"] = relationship("Parcela", back_populates="lastniki")
    
    def __repr__(self) -> str:
        return f"<Lastnik(id={self.id}, ime={self.ime}, delez={self.delez})>"
    
    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization"""
        return {
            'id': self.id,
            'parcela_id': self.parcela_id,
            'ime': self.ime,
            'vrsta': self.vrsta,
            'delez': self.delez,
            'pravica': self.pravica,
        }


# Export all models
__all__ = ['Base', 'Parcela', 'Stavba', 'Lastnik']

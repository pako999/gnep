"""
Configuration for PropertyDetective Module
Adjustable parameters for fuzzy matching and scoring
"""

import os
from dataclasses import dataclass
from typing import Dict
from dotenv import load_dotenv

load_dotenv()


@dataclass
class MatchingConfig:
    """Configuration for fuzzy matching tolerances"""
    
    # Area tolerance (percentage)
    parcel_area_tolerance: float = 0.01  # ±1%
    building_area_tolerance: float = 0.01  # ±1%
    
    # Year tolerance (absolute)
    construction_year_tolerance: int = 1  # ±1 year
    
    # Maximum results to return
    max_results: int = 3
    
    # Minimum confidence score to include in results (0-100)
    min_confidence: float = 50.0
    
    # Settlement name fuzzy matching threshold (0-100)
    settlement_fuzzy_threshold: int = 80
    
    def get_parcel_area_range(self, area: float) -> tuple:
        """Calculate min/max range for parcel area"""
        tolerance_value = area * self.parcel_area_tolerance
        return (area - tolerance_value, area + tolerance_value)
    
    def get_building_area_range(self, area: float) -> tuple:
        """Calculate min/max range for building floor area"""
        tolerance_value = area * self.building_area_tolerance
        return (area - tolerance_value, area + tolerance_value)
    
    def get_year_range(self, year: int) -> tuple:
        """Calculate min/max range for construction year"""
        return (year - self.construction_year_tolerance, 
                year + self.construction_year_tolerance)


@dataclass
class ScoringConfig:
    """Configuration for match scoring weights"""
    
    # Base weights for exact matches
    parcel_area_weight: int = 50
    construction_year_weight: int = 30
    building_area_weight: int = 40
    
    # Bonus weights
    street_match_bonus: int = 15
    building_type_bonus: int = 10
    settlement_match_bonus: int = 5
    
    # Penalty multipliers for non-exact matches
    area_near_match_multiplier: float = 0.8  # 80% of points for ±0.5%
    area_fuzzy_match_multiplier: float = 0.6  # 60% of points for ±1%
    year_near_match_multiplier: float = 0.67  # 67% of points for ±1 year
    
    @property
    def max_possible_score(self) -> int:
        """Calculate maximum possible score"""
        return (self.parcel_area_weight + 
                self.construction_year_weight + 
                self.building_area_weight +
                self.street_match_bonus +
                self.building_type_bonus +
                self.settlement_match_bonus)
    
    def calculate_confidence(self, score: int) -> float:
        """Convert score to confidence percentage"""
        return (score / self.max_possible_score) * 100


@dataclass
class GeoJSONConfig:
    """Configuration for GeoJSON output"""
    
    # Coordinate system
    output_srid: int = 4326  # WGS84 for web mapping
    source_srid: int = 3794  # Slovenian D96/TM
    
    # Styling hints for frontend
    colors: Dict[str, str] = None
    
    def __post_init__(self):
        if self.colors is None:
            self.colors = {
                'high_confidence': '#22c55e',  # Green for >90%
                'medium_confidence': '#eab308',  # Yellow for 70-90%
                'low_confidence': '#ef4444',  # Red for <70%
            }
    
    def get_color_for_confidence(self, confidence: float) -> str:
        """Get color based on confidence score"""
        if confidence >= 90:
            return self.colors['high_confidence']
        elif confidence >= 70:
            return self.colors['medium_confidence']
        else:
            return self.colors['low_confidence']


class PropertyDetectiveConfig:
    """Main configuration class combining all configs"""
    
    def __init__(self):
        self.matching = MatchingConfig()
        self.scoring = ScoringConfig()
        self.geojson = GeoJSONConfig()
        
        # Load custom values from environment if provided
        self._load_from_env()
    
    def _load_from_env(self):
        """Load configuration from environment variables"""
        # Matching config
        if parcel_tol := os.getenv('PARCEL_AREA_TOLERANCE'):
            self.matching.parcel_area_tolerance = float(parcel_tol)
        if building_tol := os.getenv('BUILDING_AREA_TOLERANCE'):
            self.matching.building_area_tolerance = float(building_tol)
        if year_tol := os.getenv('YEAR_TOLERANCE'):
            self.matching.construction_year_tolerance = int(year_tol)
        if max_results := os.getenv('MAX_RESULTS'):
            self.matching.max_results = int(max_results)
        if min_conf := os.getenv('MIN_CONFIDENCE'):
            self.matching.min_confidence = float(min_conf)


# Global default config instance
default_config = PropertyDetectiveConfig()


# Export
__all__ = [
    'MatchingConfig',
    'ScoringConfig', 
    'GeoJSONConfig',
    'PropertyDetectiveConfig',
    'default_config'
]

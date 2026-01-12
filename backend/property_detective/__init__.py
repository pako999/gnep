"""
PropertyDetective - AI-Powered Real Estate Matching for GURS Data

Automatically matches real estate listings with GURS cadastral data using
fuzzy matching and intelligent scoring algorithms.
"""

from .matcher import find_probable_parcels, PropertyMatcher
from .models import Parcela, Stavba
from .scoring import calculate_match_score, rank_candidates
from .geojson_utils import parcels_to_geojson

__version__ = "1.0.0"
__all__ = [
    "find_probable_parcels",
    "PropertyMatcher",
    "Parcela",
    "Stavba",
    "calculate_match_score",
    "rank_candidates",
    "parcels_to_geojson",
]

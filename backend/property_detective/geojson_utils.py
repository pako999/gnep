"""
GeoJSON Utilities for PropertyDetective
Converts parcel geometries to GeoJSON for web mapping
"""

import json
from typing import List, Optional
from shapely.geometry import mapping
from geoalchemy2.shape import to_shape

from .models import Parcela
from .scoring import MatchScore
from .config import GeoJSONConfig, default_config


def parcels_to_geojson(
    match_scores: List[MatchScore],
    config: GeoJSONConfig = None
) -> dict:
    """
    Convert match scores to GeoJSON FeatureCollection
    
    Args:
        match_scores: List of MatchScore objects with parcels
        config: GeoJSONConfig instance (uses default if None)
    
    Returns:
        GeoJSON FeatureCollection dict
    
    Example output:
        {
            "type": "FeatureCollection",
            "features": [
                {
                    "type": "Feature",
                    "geometry": {...},
                    "properties": {
                        "parcela_id": 123,
                        "rank": 1,
                        "confidence": 95.5,
                        "score": 120,
                        "parcela_stevilka": "123/4",
                        "ko_ime": "Ljubljana - Center",
                        ...
                    }
                }
            ]
        }
    """
    if config is None:
        config = default_config.geojson
    
    features = []
    for rank, match_score in enumerate(match_scores, start=1):
        feature = create_feature(match_score, rank, config)
        if feature:
            features.append(feature)
    
    return {
        "type": "FeatureCollection",
        "features": features
    }


def create_feature(
    match_score: MatchScore,
    rank: int,
    config: GeoJSONConfig = None
) -> Optional[dict]:
    """
    Create a single GeoJSON feature from a match score
    
    Args:
        match_score: MatchScore object
        rank: Ranking position (1, 2, 3, etc.)
        config: GeoJSONConfig instance
    
    Returns:
        GeoJSON Feature dict or None if no geometry
    """
    if config is None:
        config = default_config.geojson
    
    parcela = match_score.parcela
    
    # Convert PostGIS geometry to Shapely, then to GeoJSON
    if parcela.geom is None:
        return None
    
    # Convert geometry to shape
    shape_geom = to_shape(parcela.geom)
    
    # Convert to WGS84 if needed (assuming source is EPSG:3794)
    # Note: This would require pyproj for coordinate transformation
    # For now, we'll use the geometry as-is and note the CRS
    geojson_geom = mapping(shape_geom)
    
    # Build properties
    properties = {
        # Identification
        'parcela_id': parcela.id,
        'parcela_stevilka': parcela.parcela_stevilka,
        'ko_sifra': parcela.ko_sifra,
        'ko_ime': parcela.ko_ime,
        
        # Match information
        'rank': rank,
        'confidence': round(match_score.confidence, 2),
        'score': match_score.total_score,
        'score_breakdown': match_score.breakdown,
        
        # Parcel details
        'povrsina': float(parcela.povrsina),
        
        # Styling hints for frontend
        'color': config.get_color_for_confidence(match_score.confidence),
        'opacity': 0.7 if match_score.confidence >= 80 else 0.5,
    }
    
    # Add building information if available
    if match_score.stavba:
        stavba = match_score.stavba
        properties.update({
            'stavba_id': stavba.id,
            'leto_izgradnje': stavba.leto_izgradnje,
            'neto_tloris': float(stavba.neto_tloris) if stavba.neto_tloris else None,
            'naslov': stavba.get_full_address(),
            'tip': stavba.tip,
        })
    
    return {
        "type": "Feature",
        "geometry": geojson_geom,
        "properties": properties
    }


def save_geojson(geojson_data: dict, filepath: str):
    """
    Save GeoJSON data to file
    
    Args:
        geojson_data: GeoJSON dict
        filepath: Output file path
    """
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(geojson_data, f, ensure_ascii=False, indent=2)


# Export
__all__ = ['parcels_to_geojson', 'create_feature', 'save_geojson']

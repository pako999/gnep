"""
Scoring Algorithm for PropertyDetective
Calculates match confidence scores for parcel candidates
"""

from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass

from .models import Parcela, Stavba
from .config import ScoringConfig, default_config


@dataclass
class MatchScore:
    """Container for match score details"""
    total_score: int
    confidence: float
    breakdown: Dict[str, int]
    parcela: Parcela
    stavba: Optional[Stavba] = None
    
    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization"""
        return {
            'total_score': self.total_score,
            'confidence': round(self.confidence, 2),
            'breakdown': self.breakdown,
            'parcela_id': self.parcela.id,
            'stavba_id': self.stavba.id if self.stavba else None,
        }


def calculate_match_score(
    listing_data: dict,
    parcela: Parcela,
    stavba: Optional[Stavba] = None,
    config: ScoringConfig = None
) -> MatchScore:
    """
    Calculate match score for a parcel candidate
    
    Args:
        listing_data: Dictionary with listing information from scraper
        parcela: Parcela ORM instance
        stavba: Optional Stavba ORM instance (for houses/apartments)
        config: ScoringConfig instance (uses default if None)
    
    Returns:
        MatchScore with total score, confidence, and breakdown
    
    Example listing_data:
        {
            'settlement': 'Ljubljana - Center',
            'parcel_area_m2': 542,
            'construction_year': 1974,
            'net_floor_area_m2': 185.4,
            'property_type': 'Hiša',
            'street_name': 'Slovenska cesta'  # optional
        }
    """
    if config is None:
        config = default_config.scoring
    
    score_breakdown = {}
    total = 0
    
    # 1. Parcel Area Matching (+50 points max)
    if 'parcel_area_m2' in listing_data and listing_data['parcel_area_m2']:
        listing_area = float(listing_data['parcel_area_m2'])
        parcela_area = float(parcela.povrsina)
        area_diff_pct = abs(listing_area - parcela_area) / listing_area * 100
        
        if area_diff_pct <= 0.1:  # Exact match (within 0.1%)
            score_breakdown['parcel_area'] = config.parcel_area_weight
        elif area_diff_pct <= 0.5:  # Near match
            score_breakdown['parcel_area'] = int(config.parcel_area_weight * config.area_near_match_multiplier)
        elif area_diff_pct <= 1.0:  # Fuzzy match (within 1%)
            score_breakdown['parcel_area'] = int(config.parcel_area_weight * config.area_fuzzy_match_multiplier)
        else:
            score_breakdown['parcel_area'] = 0
        
        total += score_breakdown['parcel_area']
    
    # 2. Construction Year Matching (+30 points max)
    if stavba and 'construction_year' in listing_data and listing_data['construction_year']:
        listing_year = int(listing_data['construction_year'])
        if stavba.leto_izgradnje:
            year_diff = abs(listing_year - stavba.leto_izgradnje)
            
            if year_diff == 0:  # Exact match
                score_breakdown['construction_year'] = config.construction_year_weight
            elif year_diff <= 1:  # ±1 year
                score_breakdown['construction_year'] = int(config.construction_year_weight * config.year_near_match_multiplier)
            else:
                score_breakdown['construction_year'] = 0
            
            total += score_breakdown['construction_year']
    
    # 3. Building Floor Area Matching (+40 points max)
    if stavba and 'net_floor_area_m2' in listing_data and listing_data['net_floor_area_m2']:
        listing_floor_area = float(listing_data['net_floor_area_m2'])
        if stavba.neto_tloris:
            stavba_floor_area = float(stavba.neto_tloris)
            floor_diff_pct = abs(listing_floor_area - stavba_floor_area) / listing_floor_area * 100
            
            if floor_diff_pct <= 0.1:  # Exact match (within 0.1 m²)
                score_breakdown['building_area'] = config.building_area_weight
            elif floor_diff_pct <= 1.0:  # Within 1%
                score_breakdown['building_area'] = int(config.building_area_weight * config.area_near_match_multiplier)
            elif floor_diff_pct <= 2.0:  # Within 2%
                score_breakdown['building_area'] = int(config.building_area_weight * config.area_fuzzy_match_multiplier)
            else:
                score_breakdown['building_area'] = 0
            
            total += score_breakdown['building_area']
    
    # 4. Bonus: Street Name Match (+15 points)
    if stavba and 'street_name' in listing_data and listing_data['street_name']:
        listing_street = listing_data['street_name'].lower()
        if stavba.naslov_ulica and listing_street in stavba.naslov_ulica.lower():
            score_breakdown['street_match'] = config.street_match_bonus
            total += config.street_match_bonus
    
    # 5. Bonus: Building Type Match (+10 points)
    if stavba and 'property_type' in listing_data:
        listing_type = listing_data['property_type'].lower()
        if stavba.tip:
            # Simple matching (can be enhanced with mapping)
            if 'hiša' in listing_type or 'house' in listing_type:
                if 'stanov' in stavba.tip.lower():  # stanovanjska
                    score_breakdown['building_type'] = config.building_type_bonus
                    total += config.building_type_bonus
    
    # 6. Bonus: Settlement Match (+5 points)
    if 'settlement' in listing_data and listing_data['settlement']:
        listing_settlement = listing_data['settlement'].lower()
        # Extract main settlement name (remove district info like "- Center")
        main_settlement = listing_settlement.split('-')[0].strip()
        
        if main_settlement in parcela.ko_ime.lower():
            score_breakdown['settlement_match'] = config.settlement_match_bonus
            total += config.settlement_match_bonus
    
    # Calculate confidence percentage
    confidence = config.calculate_confidence(total)
    
    return MatchScore(
        total_score=total,
        confidence=confidence,
        breakdown=score_breakdown,
        parcela=parcela,
        stavba=stavba
    )


def rank_candidates(
    match_scores: List[MatchScore],
    max_results: int = 3
) -> List[MatchScore]:
    """
    Rank and filter match scores by confidence
    
    Args:
        match_scores: List of MatchScore objects
        max_results: Maximum number of results to return
    
    Returns:
        Sorted list of top match scores
    """
    # Sort by total score descending
    sorted_scores = sorted(match_scores, key=lambda x: x.total_score, reverse=True)
    
    # Return top N results
    return sorted_scores[:max_results]


def filter_by_confidence(
    match_scores: List[MatchScore],
    min_confidence: float = 50.0
) -> List[MatchScore]:
    """
    Filter match scores by minimum confidence threshold
    
    Args:
        match_scores: List of MatchScore objects
        min_confidence: Minimum confidence percentage (0-100)
    
    Returns:
        Filtered list of match scores above threshold
    """
    return [score for score in match_scores if score.confidence >= min_confidence]


# Export
__all__ = ['MatchScore', 'calculate_match_score', 'rank_candidates', 'filter_by_confidence']

"""
PropertyDetective Matcher - Fuzzy Matching Algorithm
Finds probable parcels matching real estate listing data
"""

from typing import List, Dict, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from fuzzywuzzy import fuzz

from .models import Parcela, Stavba
from .scoring import MatchScore, calculate_match_score, rank_candidates, filter_by_confidence
from .config import PropertyDetectiveConfig, default_config
from ..database.connection import session_scope


class PropertyMatcher:
    """
    Main class for fuzzy matching real estate listings with GURS data
    """
    
    def __init__(self, config: PropertyDetectiveConfig = None):
        """
        Initialize PropertyMatcher
        
        Args:
            config: PropertyDetectiveConfig instance (uses default if None)
        """
        self.config = config if config else default_config
    
    def find_probable_parcels(self, listing_data: dict) -> dict:
        """
        Find probable parcels matching listing data
        
        Args:
            listing_data: Dictionary with listing information
                Required fields:
                - settlement: str (e.g., "Ljubljana - Center")
                - parcel_area_m2: float (e.g., 542.0)
                
                Optional fields:
                - construction_year: int
                - net_floor_area_m2: float
                - property_type: str ("Hiša", "Stanovanje", etc.)
                - street_name: str
        
        Returns:
            Dictionary with results:
                {
                    'success': bool,
                    'matches': List[dict],  # Top N matches with scores
                    'geojson': dict,  # GeoJSON FeatureCollection
                    'count': int,
                    'message': str
                }
        """
        # Validate input
        if not listing_data.get('settlement') or not listing_data.get('parcel_area_m2'):
            return {
                'success': False,
                'message': 'Missing required fields: settlement and parcel_area_m2',
                'matches': [],
                'geojson': None,
                'count': 0
            }
        
        try:
            with session_scope() as session:
                # Step 1: Find candidate parcels
                candidates = self._find_candidates(session, listing_data)
                
                if not candidates:
                    return {
                        'success': True,
                        'message': 'No matching parcels found',
                        'matches': [],
                        'geojson': None,
                        'count': 0
                    }
                
                # Step 2: Calculate scores for all candidates
                match_scores = []
                for parcela, stavba in candidates:
                    score = calculate_match_score(
                        listing_data,
                        parcela,
                        stavba,
                        self.config.scoring
                    )
                    match_scores.append(score)
                
                # Step 3: Filter by minimum confidence
                filtered_scores = filter_by_confidence(
                    match_scores,
                    self.config.matching.min_confidence
                )
                
                if not filtered_scores:
                    return {
                        'success': True,
                        'message': f'Found candidates but none meet minimum confidence threshold of {self.config.matching.min_confidence}%',
                        'matches': [],
                        'geojson': None,
                        'count': 0
                    }
                
                # Step 4: Rank and get top N
                top_matches = rank_candidates(
                    filtered_scores,
                    self.config.matching.max_results
                )
                
                # Step 5: Convert to output format
                from .geojson_utils import parcels_to_geojson
                
                matches_list = [self._match_to_dict(match) for match in top_matches]
                geojson = parcels_to_geojson(top_matches, self.config.geojson)
                
                # Generate message
                best_confidence = top_matches[0].confidence if top_matches else 0
                message = f"AI je z {best_confidence:.1f}% verjetnostjo ugotovil, da gre za parcelo št. {top_matches[0].parcela.parcela_stevilka} v KO {top_matches[0].parcela.ko_ime}"
                
                return {
                    'success': True,
                    'message': message,
                    'matches': matches_list,
                    'geojson': geojson,
                    'count': len(top_matches)
                }
        
        except Exception as e:
            return {
                'success': False,
                'message': f'Error during matching: {str(e)}',
                'matches': [],
                'geojson': None,
                'count': 0
            }
    
    def _find_candidates(
        self,
        session: Session,
        listing_data: dict
    ) -> List[tuple[Parcela, Optional[Stavba]]]:
        """
        Find candidate parcels using fuzzy SQL queries
        
        Returns:
            List of tuples (Parcela, Optional[Stavba])
        """
        # Extract search parameters
        settlement = listing_data['settlement']
        parcel_area = float(listing_data['parcel_area_m2'])
        
        # Calculate tolerance ranges
        area_min, area_max = self.config.matching.get_parcel_area_range(parcel_area)
        
        # Build base query for parcels
        query = session.query(Parcela)
        
        # Filter by settlement (fuzzy match)
        settlement_filters = self._build_settlement_filter(settlement)
        query = query.filter(settlement_filters)
        
        # Filter by parcel area (with tolerance)
        query = query.filter(
            and_(
                Parcela.povrsina >= area_min,
                Parcela.povrsina <= area_max
            )
        )
        
        # If building data provided, join with stavbe table
        if ('construction_year' in listing_data or 'net_floor_area_m2' in listing_data):
            return self._find_with_building_join(session, query, listing_data)
        else:
            # Return parcels without building data
            parcels = query.all()
            return [(p, None) for p in parcels]
    
    def _build_settlement_filter(self, settlement: str):
        """Build filter for settlement name with fuzzy matching"""
        # Clean settlement name (remove district info)
        main_settlement = settlement.split('-')[0].strip()
        
        # Simple pattern matching (can be enhanced with PostgreSQL full-text search)
        return or_(
            Parcela.ko_ime.ilike(f'%{main_settlement}%'),
            Parcela.ko_ime.ilike(f'{main_settlement}%'),
        )
    
    def _find_with_building_join(
        self,
        session: Session,
        parcela_query,
        listing_data: dict
    ) -> List[tuple[Parcela, Stavba]]:
        """
        Find candidates with building data join
        """
        # Join with stavbe table
        query = parcela_query.join(Stavba, Parcela.id == Stavba.parcela_id)
        
        # Add building filters if provided
        filters = []
        
        if 'construction_year' in listing_data and listing_data['construction_year']:
            year = int(listing_data['construction_year'])
            year_min, year_max = self.config.matching.get_year_range(year)
            filters.append(
                and_(
                    Stavba.leto_izgradnje >= year_min,
                    Stavba.leto_izgradnje <= year_max
                )
            )
        
        if 'net_floor_area_m2' in listing_data and listing_data['net_floor_area_m2']:
            floor_area = float(listing_data['net_floor_area_m2'])
            area_min, area_max = self.config.matching.get_building_area_range(floor_area)
            filters.append(
                and_(
                    Stavba.neto_tloris >= area_min,
                    Stavba.neto_tloris <= area_max
                )
            )
        
        if filters:
            query = query.filter(and_(*filters))
        
        # Execute query and get results
        results = query.add_columns(Stavba).all()
        
        # Results are tuples of (Parcela, Stavba)
        return [(parcela, stavba) for parcela, stavba in results]
    
    def _match_to_dict(self, match_score: MatchScore) -> dict:
        """Convert MatchScore to dictionary for JSON response"""
        result = {
            'parcela': match_score.parcela.to_dict(),
            'confidence': round(match_score.confidence, 2),
            'score': match_score.total_score,
            'score_breakdown': match_score.breakdown,
        }
        
        if match_score.stavba:
            result['stavba'] = match_score.stavba.to_dict()
        
        return result


# Convenience function for direct use
def find_probable_parcels(listing_data: dict, config: PropertyDetectiveConfig = None) -> dict:
    """
    Convenience function to find probable parcels
    
    Args:
        listing_data: Dictionary with listing information
        config: Optional PropertyDetectiveConfig instance
    
    Returns:
        Dictionary with match results
    """
    matcher = PropertyMatcher(config)
    return matcher.find_probable_parcels(listing_data)


# Export
__all__ = ['PropertyMatcher', 'find_probable_parcels']

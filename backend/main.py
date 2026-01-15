"""
GNEP FastAPI Backend Application
Main entry point for the API server
"""

from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import Optional, List
import logging
from datetime import datetime

from property_detective import find_probable_parcels
from database.connection import test_connection, initialize_database

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="GNEP API",
    description="AI-Powered Real Estate Matching for GURS Cadastral Data",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS Configuration for Vercel Frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow ALL origins temporarily to fix Vercel connection
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic Models for API

class ListingData(BaseModel):
    """Input model for real estate listing data"""
    settlement: str = Field(..., description="Settlement or cadastral municipality name", example="Ljubljana - Center")
    parcel_area_m2: float = Field(..., description="Parcel area in square meters", example=542.0, gt=0)
    construction_year: Optional[int] = Field(None, description="Year of construction", example=1974, ge=1800, le=2030)
    net_floor_area_m2: Optional[float] = Field(None, description="Net floor area in square meters", example=185.4, gt=0)
    property_type: Optional[str] = Field(None, description="Property type", example="Hiša")
    street_name: Optional[str] = Field(None, description="Street name", example="Slovenska cesta")
    
    class Config:
        json_schema_extra = {
            "example": {
                "settlement": "Ljubljana - Center",
                "parcel_area_m2": 542.0,
                "construction_year": 1974,
                "net_floor_area_m2": 185.4,
                "property_type": "Hiša",
                "street_name": "Slovenska cesta"
            }
        }


class MatchResponse(BaseModel):
    """Response model for parcel matching"""
    success: bool
    message: str
    matches: List[dict]
    geojson: Optional[dict]
    count: int


class HealthResponse(BaseModel):
    """Health check response"""
    status: str
    timestamp: str
    database_connected: bool
    version: str


# API Endpoints

@app.on_event("startup")
async def startup_event():
    """Initialize database connection on startup"""
    logger.info("Starting GNEP API server...")
    initialize_database()
    logger.info("Database initialized successfully")



class CoordinateSearch(BaseModel):
    """Input model for coordinate-based search"""
    lng: float
    lat: float
    address: Optional[str] = None

@app.post("/api/find-parcel-by-point", response_model=MatchResponse, tags=["Search"])
async def find_parcel_by_point_endpoint(data: CoordinateSearch):
    """Find a parcel containing a specific point (lng, lat)"""
    from property_detective.geojson_utils import parcels_to_geojson
    from database.connection import session_scope
    from property_detective.models import Parcela
    from sqlalchemy import func
    
    logger.info(f"Searching for parcel at coordinates: {data.lng}, {data.lat}")
    
    try:
        with session_scope() as session:
            # Create a point geometry from coordinates (ST_SetSRID(ST_Point(lng, lat), 4326))
            # Then transform to Slovenian grid (3794)
            # Find parcel that contains this point
            
            point_geom = func.ST_Transform(
                func.ST_SetSRID(func.ST_Point(data.lng, data.lat), 4326),
                3794
            )
            
            parcel = session.query(Parcela).filter(
                func.ST_Contains(Parcela.geom, point_geom)
            ).first()
            
            if not parcel:
                return {
                    "success": False,
                    "message": f"No parcel found at location: {data.address or 'Coordinates'}",
                    "matches": [],
                    "geojson": None,
                    "count": 0
                }
                
            # Found a parcel!
            # Format match object (similar to Matcher output)
            match_dict = {
                "parcela": {
                    "id": parcel.id,
                    "parcela_stevilka": parcel.parcela_stevilka,
                    "ko_sifra": parcel.ko_sifra,
                    "ko_ime": parcel.ko_ime,
                    "povrsina": parcel.povrsina
                },
                "stavba": None,
                "confidence": 100.0,  # Exact match
                "score": 1.0,
                "notes": ["Exact location match"]
            }
            
            # Create GeoJSON
            # We need to attach the match object to a mock 'candidate' object for the util
            class MockMatch:
                def __init__(self, p):
                    self.parcela = p
                    self.confidence = 100.0
            
            geojson = parcels_to_geojson([MockMatch(parcel)])
            
            return {
                "success": True,
                "message": f"Found parcel {parcel.parcela_stevilka} in KO {parcel.ko_ime} at address {data.address}",
                "matches": [match_dict],
                "geojson": geojson,
                "count": 1
            }
            
    except Exception as e:
        logger.error(f"Error in coordinate search: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/", tags=["Root"])
async def root():
    """Root endpoint - API information"""
    return {
        "name": "GNEP API",
        "version": "1.0.0",
        "description": "AI-Powered Real Estate Matching for GURS Cadastral Data",
        "docs": "/docs",
        "health": "/health"
    }


@app.get("/health", response_model=HealthResponse, tags=["Health"])
async def health_check():
    """
    Health check endpoint for monitoring
    Returns API status and database connection status
    """
    db_connected = test_connection()
    
    return HealthResponse(
        status="healthy" if db_connected else "unhealthy",
        timestamp=datetime.utcnow().isoformat(),
        database_connected=db_connected,
        version="1.0.0"
    )


@app.post("/api/find-probable-parcels", response_model=MatchResponse, tags=["PropertyDetective"])
async def api_find_probable_parcels(listing: ListingData):
    """
    Find probable parcels matching real estate listing data
    
    Uses AI-powered fuzzy matching to identify the most likely cadastral parcels
    based on listing characteristics like area, construction year, and location.
    
    Returns:
    - Top 3 most probable parcels with confidence scores
    - GeoJSON data for map visualization
    - Detailed scoring breakdown
    """
    try:
        logger.info(f"Finding probable parcels for: {listing.settlement}, {listing.parcel_area_m2}m²")
        
        # Convert Pydantic model to dict
        listing_dict = listing.model_dump()
        
        # Call PropertyDetective
        result = find_probable_parcels(listing_dict)
        
        logger.info(f"Found {result['count']} matches with confidence")
        
        return MatchResponse(**result)
    
    except Exception as e:
        logger.error(f"Error in find_probable_parcels: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing request: {str(e)}"
        )


@app.post("/api/check-permit", tags=["PropertyDetective"])
async def api_check_permit(listing: ListingData):
    """
    Check building permit status (Placeholder for future AI enhancement)
    
    This endpoint will use AI to verify if a building has proper permits
    by cross-referencing GURS cadastral data with building registry.
    
    Currently returns a placeholder response.
    """
    # Placeholder implementation
    return {
        "success": True,
        "message": "AI preverjanje gradbenih dovoljenj - Coming Soon!",
        "has_permit": None,
        "permit_details": None,
        "note": "This feature is under development"
    }


@app.get("/api/parcels/{parcela_id}", tags=["Parcels"])
async def get_parcel_details(parcela_id: int):
    """
    Get detailed information about a specific parcel
    
    Returns cadastral data, ownership information, and buildings on the parcel.
    """
    try:
        from database.connection import session_scope
        from property_detective.models import Parcela
        
        with session_scope() as session:
            parcela = session.query(Parcela).filter(Parcela.id == parcela_id).first()
            
            if not parcela:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Parcel with ID {parcela_id} not found"
                )
            
            result = parcela.to_dict()
            
            # Add buildings
            result['stavbe'] = [stavba.to_dict() for stavba in parcela.stavbe]
            
            # Add ownership (if available)
            result['lastniki'] = [lastnik.to_dict() for lastnik in parcela.lastniki]
            
            return {
                "success": True,
                "data": result
            }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting parcel details: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving parcel data: {str(e)}"
        )


@app.get("/api/analyze/flood/{parcel_id}", tags=["Analysis"])
async def get_flood_risk(parcel_id: int):
    """
    Analyze flood risk for a specific parcel
    
    Checks for intersection with:
    - Running waters (Rivers/Streams)
    - Standing waters (Lakes)
    - Wetlands
    """
    from property_detective.analyzers.flood_risk import analyze_flood_risk
    from database.connection import session_scope
    
    try:
        with session_scope() as session:
            result = analyze_flood_risk(parcel_id, session)
            return result
    except Exception as e:
        logger.error(f"Error analyzing flood risk: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error analyzing flood risk: {str(e)}"
        )


@app.post("/api/admin/seed", tags=["Admin"])
async def seed_database_endpoint():
    """
    Seed the database with sample data (Admin only)
    
    Populates the database with sample Slovenian cadastral data 
    for demonstration and testing purposes.
    """
    try:
        from database.seed_data import seed_database
        seed_database()
        return {
            "success": True,
            "message": "Database seeded successfully"
        }
    except Exception as e:
        logger.error(f"Error seeding database: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error seeding database: {str(e)}"
        )


# Error handlers

@app.exception_handler(404)
async def not_found_handler(request, exc):
    """Custom 404 error handler"""
    return JSONResponse(
        status_code=404,
        content={
            "success": False,
            "message": "Endpoint not found",
            "path": str(request.url)
        }
    )


@app.exception_handler(500)
async def internal_error_handler(request, exc):
    """Custom 500 error handler"""
    logger.error(f"Internal server error: {exc}")
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "message": "Internal server error",
            "detail": str(exc) if app.debug else "An unexpected error occurred"
        }
    )


# Run with: uvicorn main:app --reload --host 0.0.0.0 --port 8000
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )

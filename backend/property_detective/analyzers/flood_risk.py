from sqlalchemy import text
from property_detective.geojson_utils import serialize_db_row

def analyze_flood_risk(parcel_id: int, db_session):
    """
    Analyze flood risk for a specific parcel by checking intersection and proximity
    to water bodies (Hydrography).
    """
    
    # query: Check for direct intersection (High Risk) and proximity (Medium Risk)
    # Using 10m buffer for proximity.
    
    sql = text("""
        WITH parcel AS (
            SELECT geom FROM parcele WHERE id = :parcel_id
        ),
        intersections AS (
            SELECT 
                wb.type,
                wb.name,
                'HIGH' as risk_level,
                0 as distance
            FROM water_bodies wb, parcel p
            WHERE ST_Intersects(wb.geom, p.geom)
        ),
        proximate AS (
            SELECT 
                wb.type,
                wb.name,
                'MEDIUM' as risk_level,
                ST_Distance(wb.geom, p.geom) as distance
            FROM water_bodies wb, parcel p
            WHERE ST_DWithin(wb.geom, p.geom, 50) -- 50m check
            AND NOT ST_Intersects(wb.geom, p.geom)
        )
        SELECT * FROM intersections
        UNION ALL
        SELECT * FROM proximate
        ORDER BY distance ASC
        LIMIT 5;
    """)
    
    results = db_session.execute(sql, {'parcel_id': parcel_id}).fetchall()
    
    risks = []
    overall_risk = "NONE"
    
    for row in results:
        risk_data = {
            "type": row.type,
            "name": row.name,
            "level": row.risk_level,
            "distance_m": round(row.distance, 1)
        }
        risks.append(risk_data)
        
        # Determine max risk
        if row.risk_level == "HIGH":
            overall_risk = "HIGH"
        elif row.risk_level == "MEDIUM" and overall_risk != "HIGH":
            overall_risk = "MEDIUM"
            
    return {
        "overall_risk": overall_risk,
        "details": risks
    }

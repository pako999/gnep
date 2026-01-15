-- Valuation Zones Schema
-- Evidence modelov vrednotenja (Valuation Models)

CREATE TABLE IF NOT EXISTS valuation_zones (
    id SERIAL PRIMARY KEY,
    
    -- Zone identification
    zone_code VARCHAR(10) NOT NULL,           -- Zone type code (DRZ, GAR, etc.)
    zone_name VARCHAR(100),                    -- Zone name
    
    -- Valuation parameters
    base_value DECIMAL(12, 2),                -- Base value per m²
    adjustment_factor DECIMAL(5, 2),          -- Adjustment factor
    zone_category VARCHAR(50),                 -- Category (residential, commercial, etc.)
    
    -- Geometry
    geom GEOMETRY(POLYGON, 3794),             -- Zone boundary
    
    -- Metadata
    valid_from DATE,
    valid_to DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create spatial index
CREATE INDEX IF NOT EXISTS idx_valuation_zones_geom ON valuation_zones USING GIST(geom);
CREATE INDEX IF NOT EXISTS idx_valuation_zones_code ON valuation_zones(zone_code);

-- Transaction history table
CREATE TABLE IF NOT EXISTS property_transactions (
    id SERIAL PRIMARY KEY,
    
    -- Property reference
    parcela_id INTEGER REFERENCES parcele(id),
    
    -- Transaction details
    transaction_date DATE NOT NULL,
    transaction_type VARCHAR(50),              -- Sale, rental, etc.
    price DECIMAL(12, 2) NOT NULL,
    price_per_m2 DECIMAL(10, 2),
    
    -- Property details at time of transaction
    area_m2 DECIMAL(10, 2),
    building_year INTEGER,
    condition VARCHAR(50),
    
    -- Location
    settlement VARCHAR(100),
    municipality VARCHAR(100),
    
    -- Metadata
    source VARCHAR(100),                       -- GURS, agency, etc.
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_transactions_parcela ON property_transactions(parcela_id);
CREATE INDEX IF NOT EXISTS idx_transactions_date ON property_transactions(transaction_date);
CREATE INDEX IF NOT EXISTS idx_transactions_settlement ON property_transactions(settlement);

COMMENT ON TABLE valuation_zones IS 'GURS valuation model zones for automated property valuations';
COMMENT ON TABLE property_transactions IS 'Historical property transaction data for market analysis';

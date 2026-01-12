-- PropertyDetective Database Schema
-- GURS Cadastral Data for Slovenia
-- Requires PostGIS extension

-- Enable PostGIS extension
CREATE EXTENSION IF NOT EXISTS postgis;

-- ============================================================
-- PARCELE (Land Parcels) Table
-- ============================================================
CREATE TABLE IF NOT EXISTS parcele (
    id SERIAL PRIMARY KEY,
    
    -- Parcel identification
    parcela_stevilka VARCHAR(50) NOT NULL,  -- e.g., "123/4"
    ko_sifra VARCHAR(10) NOT NULL,          -- Cadastral municipality code
    ko_ime VARCHAR(100) NOT NULL,           -- Cadastral municipality name
    
    -- Parcel properties
    povrsina DECIMAL(12, 2) NOT NULL,       -- Surface area in m²
    
    -- Spatial data
    geom GEOMETRY(POLYGON, 3794),           -- Slovenian coordinate system (D96/TM)
    
    -- Metadata
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Indexes for faster queries
    CONSTRAINT unique_parcela UNIQUE (parcela_stevilka, ko_sifra)
);

-- Create spatial index on geometry
CREATE INDEX IF NOT EXISTS idx_parcele_geom ON parcele USING GIST(geom);

-- Create indexes for fuzzy matching queries
CREATE INDEX IF NOT EXISTS idx_parcele_povrsina ON parcele(povrsina);
CREATE INDEX IF NOT EXISTS idx_parcele_ko_sifra ON parcele(ko_sifra);
CREATE INDEX IF NOT EXISTS idx_parcele_ko_ime ON parcele(ko_ime);

-- Create GIN index for text search on settlement names
-- Using 'simple' configuration (Supabase doesn't support 'slovenian')
CREATE INDEX IF NOT EXISTS idx_parcele_ko_ime_gin ON parcele USING GIN(to_tsvector('simple', ko_ime));

-- ============================================================
-- STAVBE (Buildings) Table
-- ============================================================
CREATE TABLE IF NOT EXISTS stavbe (
    id SERIAL PRIMARY KEY,
    
    -- Foreign key to parcel
    parcela_id INTEGER NOT NULL REFERENCES parcele(id) ON DELETE CASCADE,
    
    -- Building identification
    stavba_stevilka VARCHAR(50),             -- Building number
    
    -- Building properties
    leto_izgradnje INTEGER,                  -- Construction year
    neto_tloris DECIMAL(10, 2),             -- Net floor area in m²
    stevilo_etaz INTEGER,                    -- Number of floors
    tip VARCHAR(50),                         -- Building type (stanovanjska, poslovna, etc.)
    
    -- Address information
    naslov_ulica VARCHAR(200),               -- Street name
    naslov_hisna_st VARCHAR(20),            -- House number
    naslov_naselje VARCHAR(100),            -- Settlement name
    naslov_posta VARCHAR(50),               -- Postal name
    naslov_postna_st VARCHAR(10),           -- Postal code
    
    -- Metadata
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for fuzzy matching queries
CREATE INDEX IF NOT EXISTS idx_stavbe_parcela_id ON stavbe(parcela_id);
CREATE INDEX IF NOT EXISTS idx_stavbe_leto_izgradnje ON stavbe(leto_izgradnje);
CREATE INDEX IF NOT EXISTS idx_stavbe_neto_tloris ON stavbe(neto_tloris);
CREATE INDEX IF NOT EXISTS idx_stavbe_tip ON stavbe(tip);
CREATE INDEX IF NOT EXISTS idx_stavbe_naslov_naselje ON stavbe(naslov_naselje);

-- Create composite index for common query patterns
CREATE INDEX IF NOT EXISTS idx_stavbe_matching ON stavbe(leto_izgradnje, neto_tloris);

-- ============================================================
-- LASTNIKI (Owners) Table - Optional for ownership data
-- ============================================================
CREATE TABLE IF NOT EXISTS lastniki (
    id SERIAL PRIMARY KEY,
    
    -- Foreign key to parcel
    parcela_id INTEGER NOT NULL REFERENCES parcele(id) ON DELETE CASCADE,
    
    -- Owner information
    ime VARCHAR(200),                        -- Name (individual or company)
    vrsta VARCHAR(50),                       -- Type (fizična oseba, pravna oseba)
    
    -- Ownership details
    delež VARCHAR(50),                       -- Share/portion (e.g., "1/1", "1/2")
    pravica VARCHAR(100),                    -- Type of right (lastništvo, služnost, etc.)
    
    -- Metadata
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_lastniki_parcela_id ON lastniki(parcela_id);

-- ============================================================
-- Helper Functions
-- ============================================================

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create triggers for auto-updating timestamps
CREATE TRIGGER update_parcele_updated_at BEFORE UPDATE ON parcele
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_stavbe_updated_at BEFORE UPDATE ON stavbe
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_lastniki_updated_at BEFORE UPDATE ON lastniki
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- ============================================================
-- Views for Common Queries
-- ============================================================

-- View combining parcels with buildings for easier querying
CREATE OR REPLACE VIEW parcele_stavbe AS
SELECT 
    p.id as parcela_id,
    p.parcela_stevilka,
    p.ko_sifra,
    p.ko_ime,
    p.povrsina as parcela_povrsina,
    p.geom,
    s.id as stavba_id,
    s.stavba_stevilka,
    s.leto_izgradnje,
    s.neto_tloris,
    s.stevilo_etaz,
    s.tip,
    s.naslov_ulica,
    s.naslov_hisna_st,
    s.naslov_naselje,
    s.naslov_posta,
    s.naslov_postna_st
FROM parcele p
LEFT JOIN stavbe s ON p.id = s.parcela_id;

-- ============================================================
-- Comments for Documentation
-- ============================================================
COMMENT ON TABLE parcele IS 'GURS cadastral parcels (land plots) with spatial data';
COMMENT ON TABLE stavbe IS 'Buildings registered in GURS cadastre';
COMMENT ON TABLE lastniki IS 'Ownership information for parcels';
COMMENT ON COLUMN parcele.geom IS 'Parcel geometry in Slovenian coordinate system D96/TM (EPSG:3794)';
COMMENT ON COLUMN parcele.povrsina IS 'Parcel surface area in square meters';
COMMENT ON COLUMN stavbe.neto_tloris IS 'Net floor area in square meters (key for matching)';

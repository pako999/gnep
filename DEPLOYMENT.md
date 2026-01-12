# GNEP - Quick Start Deployment Guide

## 🚀 Deploy Backend to Render (5 minutes)

### Step 1: Prepare Your Repo
```bash
cd /Users/admin/GIT/gurs/gnep
git add .
git commit -m "Initial GNEP full-stack implementation"
git push origin main
```

### Step 2: Deploy on Render
1. Go to https://render.com and sign in
2. Click **New +** → **Blueprint**
3. Connect your GitHub repo: `pako999/gnep`
4. Render will automatically detect `render.yaml`
5. Click **Apply** - Render creates:
   - ✅ Web Service: `gnep-api`
   - ✅ PostgreSQL database with PostGIS
   - ✅ All environment variables auto-configured

**Your API will be live at**: `https://gnep-api.onrender.com` (or similar)

### Step 3: Initialize Database
```bash
# Get database connection string from Render dashboard
# Then run schema:
psql <DATABASE_URL> -f database/schema.sql
```

---

## 🌐 Deploy Frontend to Vercel (3 minutes)

### Step 1: Configure Vercel
1. Go to https://vercel.com and sign in
2. Click **Add New → Project**
3. Import your GitHub repo: `pako999/gnep`
4. **Important**: Set **Root Directory** to `frontend`
5. Framework will auto-detect as **Next.js**

### Step 2: Add Environment Variables
In Vercel project settings → Environment Variables:

```env
NEXT_PUBLIC_API_URL=https://gnep-api.onrender.com
NEXT_PUBLIC_MAPBOX_TOKEN=<get from https://account.mapbox.com/access-tokens/>
```

### Step 3: Deploy
Click **Deploy** - Done! ✅

Your site will be live at: `https://gnep.vercel.app`

---

## 🧪 Test the Deployment

### 1. Test Backend Health
```bash
curl https://gnep-api.onrender.com/health
```

Expected response:
```json
{
  "status": "healthy",
  "database_connected": true,
  "version": "1.0.0"
}
```

### 2. Test PropertyDetective Endpoint
```bash
curl -X POST https://gnep-api.onrender.com/api/find-probable-parcels \
  -H "Content-Type: application/json" \
  -d '{
    "settlement": "Ljubljana",
    "parcel_area_m2": 542
  }'
```

### 3. Test Frontend
Visit: `https://gnep.vercel.app`
- ✅ Search form loads
- ✅ Map displays (if Mapbox token configured)
- ✅ Can submit test query

---

## 📊 Import GURS Data

### Option 1: Manual Import (Recommended for First Time)
```sql
-- Example: Insert test parcel
INSERT INTO parcele (parcela_stevilka, ko_sifra, ko_ime, povrsina, geom)
VALUES (
  '123/4',
  '2690',
  'Ljubljana - Center',
  542.0,
  ST_GeomFromText('POLYGON((...))', 3794)
);

-- Insert test building
INSERT INTO stavbe (parcela_id, leto_izgradnje, neto_tloris, naslov_naselje)
VALUES (1, 1974, 185.4, 'Ljubljana');
```

### Option 2: Bulk Import from GURS Files
```bash
# Download GURS data
wget https://egp.gu.gov.si/egp/jgp_data_download/...

# Convert SHP to SQL (using ogr2ogr)
ogr2ogr -f PostgreSQL PG:"dbname=gurs_gnep" parcele.shp -nln parcele

# Or create import script (future enhancement)
python scripts/import_gurs_data.py --input gurs_export.zip
```

---

## 🔧 Local Development

### Backend
```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set up .env
cp .env.example .env
# Edit .env with local database credentials

# Run server
uvicorn main:app --reload
```

Access at: http://localhost:8000

### Frontend
```bash
cd frontend

# Install dependencies
npm install

# Set up environment
cp .env.example .env.local
# Edit .env.local:
#   NEXT_PUBLIC_API_URL=http://localhost:8000
#   NEXT_PUBLIC_MAPBOX_TOKEN=your_token

# Run dev server
npm run dev
```

Access at: http://localhost:3000

---

## ⚙️ Configuration

### Adjust Matching Tolerances

Edit backend `.env`:
```env
PARCEL_AREA_TOLERANCE=0.01     # 1% (lower = stricter)
BUILDING_AREA_TOLERANCE=0.01
YEAR_TOLERANCE=1                # ±1 year
MIN_CONFIDENCE=50.0             # Minimum score to show
MAX_RESULTS=3                   # Top N results
```

### Adjust Scoring Weights

Edit `property_detective/config.py`:
```python
parcel_area_weight = 50      # Increase if area is most important
construction_year_weight = 30
building_area_weight = 40
```

---

## 📈 Monitoring

### Render Dashboard
- Web Service metrics (CPU, memory, requests)
- Database metrics (connections, queries)
- Logs and error tracking

### Health Check Endpoint
Set up monitoring (UptimeRobot, Pingdom) to call:
```
https://gnep-api.onrender.com/health
```

---

## 🆘 Troubleshooting

### Backend not starting?
1. Check Render logs in dashboard
2. Verify environment variables are set
3. Check database connection string

### Frontend can't connect to backend?
1. Verify `NEXT_PUBLIC_API_URL` in Vercel
2. Check CORS settings in `main.py`
3. Ensure backend is deployed and healthy

### Map not showing?
1. Verify `NEXT_PUBLIC_MAPBOX_TOKEN` is set
2. Check browser console for errors
3. Ensure GeoJSON data is valid

### Low match confidence?
1. Import more GURS data
2. Adjust tolerances in config
3. Ensure listing data has all fields (year, floor area)

---

## ✅ Deployment Checklist

- [ ] Backend deployed to Render
- [ ] Database created with PostGIS
- [ ] Schema initialized (`schema.sql` run)
- [ ] Frontend deployed to Vercel
- [ ] Environment variables configured
- [ ] Mapbox token added
- [ ] Health check returns "healthy"
- [ ] Test API endpoint works
- [ ] Frontend can connect to backend
- [ ] Map displays correctly
- [ ] GURS data imported (at least test data)

**You're live!** 🎉

# Vercel & Render Deployment - Updated Structure

## ✅ Project Structure (Updated)

The project has been restructured for easier Vercel deployment:

```
gnep/
├── Frontend (Root) - Deploys to Vercel
│   ├── app/
│   ├── components/
│   ├── lib/
│   ├── package.json
│   └── next.config.js
│
└── backend/ - Deploys to Render
    ├── main.py
    ├── property_detective/
    ├── database/
    ├── requirements.txt
    ├── Dockerfile
    └── render.yaml
```

---

## 🌐 Deploy Frontend to Vercel (DONE!)

### You've already deployed! ✅

Your Vercel deployment is live. To access it:

1. Check your Vercel dashboard for the deployment URL
2. It should be something like: `https://gnep-xxxxx.vercel.app`

### Fix ESLint Warning (Optional)

To remove the ESLint build warning, add this to `package.json`:

```bash
# Quick fix - disable ESLint during builds
npm install --save-dev eslint eslint-config-next

# Or add to package.json scripts:
"scripts": {
  "build": "next build",
  "lint": "next lint"
}
```

Then commit and push:
```bash
git add package.json
git commit -m "Fix: Add ESLint for builds"
git push
```

Vercel will auto-redeploy.

---

## 🚀 Deploy Backend to Render

### Step 1: Update render.yaml Path

Since we moved backend files to `backend/`, we need to update the build path:

```bash
# In your repo root, update render.yaml location
# render.yaml is now in backend/ folder
```

### Step 2: Deploy to Render

**Option A: Use Blueprint (Recommended)**

1. Go to https://render.com/dashboard
2. Click **New +** → **Blueprint**
3. Connect your GitHub repo: `pako999/gnep`
4. Render will look for `render.yaml`
5. **⚠️ Important**: Update the blueprint to point to `backend/`

**Option B: Manual Setup**

1. Go to https://render.com/dashboard
2. Click **New +** → **Web Service**
3. Connect GitHub repo: `pako999/gnep`
4. Configure:
   - **Name**: `gnep-api`
   - **Root Directory**: `backend`
   - **Runtime**: Python 3
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn main:app --host 0.0.0.0 --port $PORT`
5. Add **PostgreSQL** database (click "New Database")
6. Click **Create Web Service**

### Step 3: Set Environment Variables

In Render dashboard → Environment:
```env
DB_HOST=(auto-filled from database)
DB_PORT=(auto-filled from database)
DB_NAME=(auto-filled from database)
DB_USER=(auto-filled from database)
DB_PASSWORD=(auto-filled from database)
```

### Step 4: Initialize Database

Once database is created:
```bash
# Get database URL from Render dashboard
psql <DATABASE_INTERNAL_URL> -f backend/database/schema.sql
```

---

## 🔗 Connect Frontend to Backend

### Update Frontend Environment Variables

1. Go to Vercel Dashboard → Your Project → Settings → Environment Variables
2. Update `NEXT_PUBLIC_API_URL`:
   ```
   NEXT_PUBLIC_API_URL=https://gnep-api.onrender.com
   ```
   (Replace with your actual Render URL)
3. Redeploy frontend (Vercel → Deployments → Redeploy)

---

## ✅ Deployment Checklist

### Frontend (Vercel)
- [x] Deployed to Vercel
- [ ] ESLint warning fixed (optional)
- [ ] `NEXT_PUBLIC_MAPBOX_TOKEN` environment variable added
- [ ] `NEXT_PUBLIC_API_URL` updated with Render backend URL
- [ ] Tested on live URL

### Backend (Render)
- [ ] Web Service created
- [ ] PostgreSQL database created
- [ ] Database schema initialized
- [ ] Environment variables set
- [ ] Health check endpoint working: `/health`
- [ ] Test API endpoint: `/api/find-probable-parcels`

---

## 🧪 Testing

### Test Frontend
Visit your Vercel URL: `https://gnep-xxxxx.vercel.app`
- ✅ Page loads
- ✅ Form is visible
- ✅ Map component shows

### Test Backend
```bash
# Health check
curl https://gnep-api.onrender.com/health

# Test matching endpoint
curl -X POST https://gnep-api.onrender.com/api/find-probable-parcels \
  -H "Content-Type: application/json" \
  -d '{"settlement": "Ljubljana", "parcel_area_m2": 542}'
```

---

## 📝 Updated File Locations

| File | Old Location | New Location |
|------|-------------|--------------|
| Frontend files | `frontend/` | Root `/` |
| Backend files | Root `/` | `backend/` |
| `render.yaml` | Root | `backend/render.yaml` |
| `package.json` | `frontend/` | Root `/` |

---

## 🆘 Troubleshooting

### Vercel ESLint Error
**Solution**: The build still succeeds. To fix completely:
```bash
npm install --save-dev eslint eslint-config-next
git add . && git commit -m "Add ESLint" && git push
```

### Render can't find render.yaml
**Solution**: Use Manual Setup (Option B above) or move `render.yaml` to root:
```bash
mv backend/render.yaml .
git add . && git commit -m "Move render.yaml to root" && git push
```

### Backend CORS errors
**Solution**: Update `backend/main.py` CORS to include your Vercel URL:
```python
allow_origins=[
    "https://gnep-xxxxx.vercel.app",  # Your actual Vercel URL
    "https://*.vercel.app",
]
```

---

**Next**: Deploy your backend to Render and connect it to the frontend!

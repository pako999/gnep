# Vercel Import - Step-by-Step Fix

## ✅ Issue Resolved
I've added all missing Next.js files. Your frontend is now ready to import!

## Files Added:
- ✅ `app/layout.tsx` - Required root layout
- ✅ `app/globals.css` - Global styles with Tailwind
- ✅ `tailwind.config.js` - Tailwind configuration
- ✅ `postcss.config.js` - PostCSS for Tailwind
- ✅ `.eslintrc.json` - ESLint config
- ✅ `.gitignore` - Ignore patterns
- ✅ `public/` directory - Static assets

## 🚀 Deploy to Vercel Now

### Step 1: Push to GitHub
```bash
cd /Users/admin/GIT/gurs/gnep
git add .
git commit -m "Add complete Next.js frontend structure"
git push origin main
```

### Step 2: Import to Vercel

1. **Go to Vercel**: https://vercel.com/new
2. **Import Git Repository**:
   - Select your GitHub account
   - Search for: `pako999/gnep`
   - Click **Import**

3. **⚠️ CRITICAL: Configure Root Directory**:
   
   ![Vercel Configuration](/Users/admin/.gemini/antigravity/brain/99e9d816-f7ae-4abc-a1c5-40ad06042463/vercel_root_directory_1768204713455.png)
   
   - Click **Edit** next to "Root Directory"
   - Enter: `frontend`
   - Press **Continue**
   
   > [!IMPORTANT]
   > **This is the most common issue!** If you don't set the Root Directory to `frontend`, Vercel won't find your Next.js app and the import will fail.

4. **Framework Preset**:
   - Should auto-detect: **Next.js**
   - If not, select it manually

5. **Environment Variables** (Click "Add"):
   ```
   Name: NEXT_PUBLIC_API_URL
   Value: https://gnep-api.onrender.com
   (or http://localhost:8000 for testing)
   ```
   
   ```
   Name: NEXT_PUBLIC_MAPBOX_TOKEN
   Value: pk.eyJ... (get from https://account.mapbox.com/access-tokens/)
   ```

6. **Click Deploy** ✅

## 🧪 Test Locally First (Optional)

```bash
cd frontend

# Install dependencies
npm install

# Create local environment
cp .env.example .env.local

# Edit .env.local and add:
# NEXT_PUBLIC_API_URL=http://localhost:8000
# NEXT_PUBLIC_MAPBOX_TOKEN=your_token

# Run dev server
npm run dev
```

Visit: http://localhost:3000

## 🔍 Common Vercel Import Issues

### Issue: "No framework detected"
**Solution**: Make sure Root Directory is set to `frontend`

### Issue: "Build failed"
**Solution**: Check that all environment variables are set in Vercel dashboard

### Issue: "Module not found: Can't resolve 'mapbox-gl'"
**Solution**: Run `npm install` in frontend directory first, then push package-lock.json

### Issue: API calls fail with CORS error
**Solution**: 
1. Check `NEXT_PUBLIC_API_URL` is set correctly
2. Verify backend CORS allows your Vercel domain
3. Update `main.py` CORS if needed:
   ```python
   allow_origins=[
       "https://your-project.vercel.app",
       "https://*.vercel.app",
   ]
   ```

## ✅ Verification Checklist

After deployment:
- [ ] Vercel build succeeds (green checkmark)
- [ ] Site loads at https://your-project.vercel.app
- [ ] Form is visible
- [ ] Map component loads (check browser console for errors)
- [ ] Can submit test search
- [ ] No CORS errors in console

## 🎯 Next: Deploy Backend

Once frontend works, deploy the backend:

1. Go to https://render.com
2. New → Blueprint
3. Connect `pako999/gnep` repo
4. Render auto-reads `render.yaml`
5. Wait for deployment
6. Update `NEXT_PUBLIC_API_URL` in Vercel to your Render URL

Then redeploy frontend on Vercel!

---

**Need help?** Check the error logs in:
- Vercel: Deployments tab → Click deployment → View logs
- Local: Terminal output from `npm run dev`

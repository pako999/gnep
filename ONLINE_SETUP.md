# Online Deployment & Data Import Guide

Since you are skipping the local setup, here is the direct path to getting the **Online AI & Data** working.

## 1. Deploy (Backend)

The `render.yaml` configuration has been updated to include the AI requirement (`OPENAI_API_KEY`).

**If using Render:**
1.  Push your changes to GitHub.
2.  Go to [Render Dashboard](https://dashboard.render.com).
3.  Create a **Blueprint** from your repo.
4.  Enter `OPENAI_API_KEY` when prompted.

**If using Railway:**
1.  Push your changes to GitHub.
2.  Go to [Railway Dashboard](https://railway.app).
3.  Deploy from GitHub repo.
4.  Go to **Variables** and add `OPENAI_API_KEY`.

## 2. Import Data to Online Database

Run the import script **locally** but connect it to your **remote** database (Render OR Railway).

1.  **Get the External Database URL**:
    - **Render**: Dashboard -> Select Database -> Copy External Connection String.
    - **Railway**: Dashboard -> Select PostgreSQL -> Connect -> Copy "Postgres Connection URL".

2.  **Initialize Database Schema** (Important!):
    Run this to create the tables with the correct structure/indexes:
    
    ```bash
    psql "<YOUR_EXTERNAL_URL>" -f backend/database/schema.sql
    ```

3.  **Run the Import**:
    Run the following command in your terminal, replacing `<YOUR_EXTERNAL_URL>` with the one you copied:
    
    ```bash
    # Set the remote DB URL and run the batch import
    export DATABASE_URL="<YOUR_EXTERNAL_URL>"
    python3 backend/scripts/batch_import_zips.py
    ```

    *Note: This uploads the data from your local `gurs_data` folder to the cloud database.*

## 3. Verify AI

Once deployed and imported:
1.  Visit your Frontend (Vercel).
2.  The AI Chat should work if `OPENAI_API_KEY` was set correctly in Environment Variables.
3.  The Search/Globe should work (Map Tiles Fixed!).

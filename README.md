# GNEP Frontend

Next.js frontend for the GNEP AI Real Estate Locator.

## Quick Start

```bash
# Install dependencies
npm install

# Run development server
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) in your browser.

## Environment Variables

Create a `.env.local` file:

```env
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_MAPBOX_TOKEN=your_mapbox_token_here
```

## Deploy to Vercel

1. Push code to GitHub
2. Import project in Vercel
3. **Important**: Set Root Directory to `frontend`
4. Add environment variables in Vercel dashboard
5. Deploy!

See [../DEPLOYMENT.md](../DEPLOYMENT.md) for detailed instructions.

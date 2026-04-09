# Frontend (Static)

This frontend has been refactored to a static HTML/JavaScript app (no Node, no React, no Vite).

Quick run (local static server):

```bash
cd project/frontend
python -m http.server 5173
# open http://localhost:5173 in your browser
```

Run with Docker (builds a small Nginx static image):

```bash
cd project/frontend
docker build -t dnd-frontend:static .
docker run --rm -p 8080:80 dnd-frontend:static
# open http://localhost:8080
```

Run with Docker Compose (from project root):

```bash
docker compose up --build
# frontend will be available at http://localhost:8080
```

Notes:
- The app expects the API to be accessible at `http://localhost:5000/api` by default.
- If you run the backend separately, keep it available on host port `5000` so the frontend can call it.

If you want an alternative port or to embed an API base URL into the static build, I can add an index-time replacement step or runtime config snippet.

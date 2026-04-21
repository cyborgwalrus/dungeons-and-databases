# Frontend (Static)
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
- The nginx frontend proxies `/api` to the backend container, so the browser only talks to `http://localhost:8080`.
- If you run the static frontend without nginx, set `window.__API_BASE__` yourself or serve it through a proxy that forwards `/api`.

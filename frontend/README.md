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

- The frontend reverse proxy forwards `/api` to the backend container, so the browser only talks to `http://localhost:8080`.
- The shared admin gateway is available at `http://localhost:8080/admin`, with the dashboard at `/admin/dashboard` and Adminer at `/admin/adminer`. Adminer uses the bundled `login-password-less.php` plugin and the same `ADMIN_PASSWORD` as the dashboard.
- If you run the static frontend without the proxy, set `window.__API_BASE__` yourself or serve it through a proxy that forwards `/api`.
- The Swagger UI is available at `http://localhost:8080/api/docs` through the same `/api` proxy.

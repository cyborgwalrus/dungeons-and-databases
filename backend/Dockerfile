FROM python:3.12-slim

WORKDIR /app

COPY pyproject.toml /app/pyproject.toml
COPY backend /app/backend

RUN pip install --no-cache-dir uv && uv sync
RUN chmod +x /app/backend/start-backend.sh

EXPOSE 5000

# Default to running the startup script which handles DB init/seed and launches Gunicorn
CMD ["/app/backend/start-backend.sh"]

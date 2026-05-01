FROM python:3.12-slim

WORKDIR /app

RUN pip install --no-cache-dir uv
COPY pyproject.toml /app/pyproject.toml
RUN uv sync --no-cache

COPY backend /app/backend

RUN chmod +x /app/backend/start-backend.sh

ENV PATH="/app/.venv/bin:$PATH"

EXPOSE 5000

# Default to running the startup script which handles DB init/seed and launches Gunicorn
CMD ["/app/backend/start-backend.sh"]

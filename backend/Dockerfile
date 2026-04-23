FROM python:3.12-slim

WORKDIR /

COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

COPY . /app/backend
RUN chmod +x /app/backend/start-backend.sh

WORKDIR /app

EXPOSE 5000

# Default to running the startup script which handles DB init/seed and launches Gunicorn
CMD ["/app/backend/start-backend.sh"]

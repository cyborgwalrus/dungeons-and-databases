FROM python:3.11-slim

WORKDIR /

COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

COPY . /app/backend
RUN chmod +x /app/backend/start-backend.sh

WORKDIR /app

EXPOSE 5000

# Default to running the startup script which handles DB init/seed and runs the server
CMD ["/app/backend/start-backend.sh"]

FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app.py .
COPY start-backend.sh .
RUN chmod +x start-backend.sh

EXPOSE 5000

# Default to running the startup script which handles DB init/seed and runs the server
CMD ["./start-backend.sh"]

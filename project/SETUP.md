# Dungeons and Databases Setup Guide

## Quick Start with Docker Compose

### Prerequisites

- Docker and Docker Compose installed on your system

### 1. Navigate to the project root

```bash
cd "Project"
```

### 2. Start all services

```bash
docker-compose up
```

This will:

- Build both the backend and frontend Docker images
- Start the Flask backend on `http://localhost:5000`
- Start the React frontend on `http://localhost:3000`
- Create a shared network between containers

### 3. Access the application

Open your browser and navigate to: `http://localhost:3000`

### 4. Stop the services

```bash
docker-compose down
```

---

## Manual Setup (Without Docker)

### Prerequisites

- Python 3.8+ installed on your system
- Node.js 18+ installed
- pip package manager

### 1. Navigate to the backend folder

```bash
cd backend
```

### 2. Create a virtual environment (optional but recommended)

```bash
python -m venv venv
```

### 3. Activate the virtual environment

**On Windows:**

```bash
venv\Scripts\activate
```

**On macOS/Linux:**

```bash
source venv/bin/activate
```

### 4. Install dependencies

```bash
pip install -r requirements.txt
```

## Running the Flask Server

### Start the Flask development server

```bash
python app.py
```

The server will start on `http://localhost:5000`

## API Endpoints

### GET /api/player

- Returns the current player stats

### PUT /api/player

- Updates player stats
- Body: `{ "health": 100, "damage": 10, "level": 1 }`

### POST /api/player/level-up

- Increases player level and boosts stats

### POST /api/health

- Apply damage to the player
- Body: `{ "damage": 10 }`

## Running the Full Application (Without Docker)

1. **Terminal 1 - Backend:**

   ```bash
   cd backend
   python app.py
   ```

2. **Terminal 2 - Frontend:**
   ```bash
   cd Dnd
   npm run dev
   ```

Then open `http://localhost:5173` in your browser.

## Docker Architecture

The application uses Docker Compose to orchestrate:

- **Backend Service**: Python Flask running in a lightweight Python 3.11 container
- **Frontend Service**: React app built and served in a Node.js Alpine container
- **Network**: Both containers communicate via a shared Docker network

The frontend can access the backend at `http://backend:5000` within the Docker network.

### Building images separately

```bash
# Build backend
docker build -t dnd_backend ./backend

# Build frontend
docker build -t dnd_frontend ./Dnd

# Run with docker-compose
docker-compose up
```

### Docker Files

- `docker-compose.yml` - Orchestrates both services
- `backend/Dockerfile` - Python Flask backend
- `Dnd/Dockerfile` - React frontend (multi-stage build)
- `backend/.dockerignore` - Excludes unnecessary files from backend image
- `Dnd/.dockerignore` - Excludes unnecessary files from frontend image

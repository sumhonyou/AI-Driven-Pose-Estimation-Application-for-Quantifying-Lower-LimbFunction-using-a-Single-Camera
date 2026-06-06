# AI-Driven Pose Estimation for Lower-Limb Function

FYP web application for camera-based lower-limb functional checking and rehabilitation grading using pose estimation.

**Stack:** React + TypeScript + Tailwind (frontend), FastAPI (backend), PostgreSQL (database).

**Disclaimer:** This application supports movement checking and rehab feedback. It does not provide medical diagnosis.

## Prerequisites

- Node.js LTS
- Python 3.11 or 3.12
- Docker Desktop

## First Time Setup (for new users)

**Do this once after cloning the repository:**

### Step 1: Ensure Docker Desktop is running
Open Docker Desktop from Applications. Wait until the whale icon in the menu bar shows it's running (green indicator or stops animating).

### Step 2: Start PostgreSQL container
From project root:
```bash
docker compose up -d
```
Verify: `http://localhost:5432` should be accessible (or `curl http://localhost:8000/health/db` once backend is up).

### Step 3: Backend setup & database migrations
From project root:
```bash
python3 -m venv backend/.venv
source backend/.venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r backend/requirements.txt
cp backend/.env.example backend/.env

# Run database migrations (creates tables)
alembic upgrade head

# Seed exercise catalog
PYTHONPATH=backend python -m app.seed

# Start the API
cd backend && uvicorn app.main:app --reload
```

**Keep this terminal running.** The backend will be at `http://localhost:8000`.

Verify:
- `http://localhost:8000/health` → `{"status":"ok"}`
- `http://localhost:8000/health/db` → database connected
- `http://localhost:8000/docs` → Swagger API docs

### Step 4: Frontend setup (new terminal)
```bash
cd frontend
npm install
cp .env.example .env
npm run dev
```

The app will open at `http://localhost:5173`.

---

## Quick start (after first setup)

Once everything is set up, you only need:

### Terminal 1: Database
```bash
docker compose up -d
```

### Terminal 2: Backend
```bash
source backend/.venv/bin/activate
cd backend && uvicorn app.main:app --reload
```

### Terminal 3: Frontend
```bash
cd frontend && npm run dev
```

---

## Testing Phase 1B

After all three services start, try:

1. **Register** a new account in the UI (`http://localhost:5173`)
2. **Dashboard** → Mode → Exercise → Start session → End set
3. **Session History** should show your completed session
4. **Database check** (optional): Use DBeaver/pgAdmin to confirm rows in `users` and `sessions` tables

## Project structure

```text
frontend/     React + Vite + Tailwind UI
backend/      FastAPI API
docker-compose.yml   Local PostgreSQL
```

## Development tasks

See [task.md](./task.md) for phased development progress.

## Related docs

- [FYP_PROJECT_DESCRIPTION_AND_IMPLEMENTATION_PLAN.md](./FYP_PROJECT_DESCRIPTION_AND_IMPLEMENTATION_PLAN.md)
- [rules.md](./rules.md)

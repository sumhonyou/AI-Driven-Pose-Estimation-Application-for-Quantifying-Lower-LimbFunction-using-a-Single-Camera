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

Once everything is set up, you need to start three services **every time you develop**. The database container does not persist across system restarts, so `docker compose up -d` must run first.

### Option 1: Automated startup (Recommended)

**macOS/Linux:**

```bash
chmod +x startup.sh
./startup.sh
```

**Windows (PowerShell):**

```powershell
.\startup.bat
```

This will automatically start all three services in the correct order.

### Option 2: Manual startup (3 terminals)

**Terminal 1: Start the database container**

```bash
docker compose up -d
```

This starts PostgreSQL in the background. The `-d` flag means "detached mode." You only need to run this once per session—the container stays running even if you close the terminal.

**Verify database is ready:**

```bash
docker compose ps
# Should show fyp_postgres with status "Up"
```

**Terminal 2: Start the backend API**

```bash
source backend/.venv/bin/activate   # Windows: backend\.venv\Scripts\activate
cd backend && uvicorn app.main:app --reload
```

The backend will be at `http://localhost:8000`. You'll see `Application startup complete.` when ready.

**Terminal 3: Start the frontend** (new terminal)

```bash
cd frontend && npm run dev
```

The app will open at `http://localhost:5173`.

---

## Stopping services (when you're done)

How you stop things depends on **how you started them**.

### If you started manually (3 separate terminals)

Use **`Ctrl + C`** in each terminal:

1. **Frontend terminal** (`npm run dev`) → `Ctrl + C`
2. **Backend terminal** (`uvicorn app.main:app --reload`) → `Ctrl + C`
3. **PostgreSQL** (runs in Docker, not in that terminal) → from project root:

```bash
docker stop fyp_postgres
```

Verify:

```bash
docker compose ps
# fyp_postgres should no longer show status "Up"
```

### If you started with `./startup.sh` or `startup.bat`

**`Ctrl + C` alone is usually not enough.**

Those scripts start backend and frontend **in the background** (`&`), so pressing `Ctrl + C` often only stops the startup script — **uvicorn and Vite may keep running**.

After `Ctrl + C`, stop everything explicitly:

```bash
pkill -f "uvicorn app.main:app"
pkill -f "vite"
docker stop fyp_postgres
```

Or use the PIDs printed when `./startup.sh` started (example):

```bash
kill <BACKEND_PID> <FRONTEND_PID>
docker stop fyp_postgres
```

**Tip:** If you prefer simple `Ctrl + C` shutdown, use **manual startup (3 terminals)** instead of `./startup.sh`.

---

## Troubleshooting

### Backend won't start: `ModuleNotFoundError: No module named 'app'`

**Cause:** Running uvicorn from the wrong directory.
**Fix:** Always run from the `backend/` directory:

```bash
cd backend
uvicorn app.main:app --reload
```

### `ERR_CONNECTION_REFUSED` when signing up

**Cause:** Backend is not running on port 8000.
**Fix:**

1. Ensure the backend is started: `cd backend && uvicorn app.main:app --reload`
2. Check it's accessible: `curl http://localhost:8000/health` should return `{"status":"ok"}`

### `Error: connect ECONNREFUSED 127.0.0.1:5432`

**Cause:** PostgreSQL container is not running.
**Fix:**

```bash
docker compose up -d
docker compose ps  # Verify fyp_postgres is "Up"
```

### Port already in use (address already in use)

If port 8000, 5173, or 5432 is already taken:

```bash
# List what's using the port (e.g., 8000)
lsof -i :8000

# Kill the process (replace PID)
kill -9 <PID>

# Or just change ports in .env files and docker-compose.yml
```

### Frontend shows blank page or old version

**Fix:** Clear cache and rebuild:

```bash
cd frontend
npm cache clean --force
rm -rf node_modules
npm install
npm run dev
```

### Virtual environment issues (Windows)

If `.venv\Scripts\activate` doesn't work, try:

```powershell
.venv\Scripts\Activate.ps1
```

If you get a permissions error, run PowerShell as Administrator.

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

## Datasets Used

This project's Module B (rehabilitation grading) is trained and evaluated on the following public datasets:

- **REHAB24-6** — <https://zenodo.org/records/13305826>

  Černek, A., Sedmidubsky, J., Budikova, P., Jánošová, M., Katzer, L., & Procházka, M. (2024). _REHAB24-6: A multi-modal dataset of physical rehabilitation exercises_ (Version 1) [Data set]. Zenodo. https://doi.org/10.5281/zenodo.13305826

**Running the web app does not require downloading REHAB24-6.** The trained squat model is already committed under `ml/artifacts/`. The derived training feature table used for that model is committed at `ml/data/squat_features.csv` (98 side-view squat repetitions from REHAB24-6, with pose features + Good/Poor labels).

### Retraining Module B (optional)

Only needed if you want to rebuild the squat model from the public dataset:

1. Download **REHAB24-6** from the Zenodo link above and unpack it locally.
2. Edit `ml/config.yaml` so `dataset_paths.rehab246` points at your local videos / segmentation / joints folders (replace the developer machine paths).
3. Follow the setup and pipeline steps in [`ml/README.md`](./ml/README.md) (`extract_landmarks.py` → `build_features.py` → `train_squat.py` → `export_squat_model.py`).

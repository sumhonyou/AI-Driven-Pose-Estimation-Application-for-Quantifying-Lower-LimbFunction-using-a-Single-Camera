from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import (auth_routes, dashboard_routes, exercise_routes,
                     session_routes, user_routes)
from app.core.config import settings
from app.db.database import check_database_connection
from app.module_a.rest_router import router as module_a_router

app = FastAPI(
    title="FYP Pose Rehab API",
    description="Backend API for lower-limb pose estimation and rehab grading.",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[origin.strip() for origin in settings.cors_origins.split(",")],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_routes.router)
app.include_router(user_routes.router)
app.include_router(exercise_routes.router)
app.include_router(session_routes.router)
app.include_router(dashboard_routes.router)
app.include_router(module_a_router)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/health/db")
def health_db():
    try:
        check_database_connection()
        return {"status": "ok", "database": "connected"}
    except Exception as exc:
        return {"status": "error", "database": "disconnected", "detail": str(exc)}

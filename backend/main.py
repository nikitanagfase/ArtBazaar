"""
main.py  –  ArtBazaar FastAPI application entry point.
"""

import os
from pathlib import Path
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

load_dotenv()

from database import engine, Base
import models  # noqa: F401  (ensure models are registered)

from routers import users, artworks, orders, custom_orders, ai, analytics

# ── Create all tables ──────────────────────────────────────────────────────
Base.metadata.create_all(bind=engine)

# ── Ensure upload directories exist ───────────────────────────────────────
for sub in ("avatars", "artworks", "reference"):
    Path(f"uploads/{sub}").mkdir(parents=True, exist_ok=True)

# ── App ────────────────────────────────────────────────────────────────────
app = FastAPI(
    title="ArtBazaar API",
    description="Handmade Art Marketplace – FastAPI Backend",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
)

# ── CORS ───────────────────────────────────────────────────────────────────
origins = os.getenv("FRONTEND_URL", "http://localhost:5500").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins + ["http://127.0.0.1:5500"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Static files ───────────────────────────────────────────────────────────
app.mount("/static", StaticFiles(directory="uploads"), name="static")

# ── Routers ────────────────────────────────────────────────────────────────
app.include_router(users.router)
app.include_router(artworks.router)
app.include_router(orders.router)
app.include_router(custom_orders.router)
app.include_router(ai.router)
app.include_router(analytics.router)


# ── Health check ──────────────────────────────────────────────────────────
@app.get("/api/health", tags=["health"])
def health():
    return {"status": "ok", "version": "1.0.0"}


# ── Run ────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
    )

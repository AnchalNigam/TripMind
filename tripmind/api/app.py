"""FastAPI Application Entry Point."""

import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from tripmind.config import settings
from tripmind.api.routes import router, router_v2

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)

app = FastAPI(
    title="TripMind 🏔️ — Autonomous Adaptive Trip Planner",
    description="Level 1: ReAct Engine | Level 2: Plan-and-Solve Engine",
    version="0.2.0",
)

# Enable CORS for frontend dashboard or external clients
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

import os
from fastapi.staticfiles import StaticFiles

app.include_router(router)
app.include_router(router_v2)

# Mount React Frontend if built
frontend_dist = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "frontend", "dist")
if os.path.exists(frontend_dist):
    app.mount("/", StaticFiles(directory=frontend_dist, html=True), name="frontend")
else:
    @app.get("/")
    def root():
        return {
            "message": "TripMind V1 ReAct Engine is running. Visit /docs for Swagger API.",
            "docs_url": "/docs",
        }

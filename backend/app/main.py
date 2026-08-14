"""
SimpyLIGA API — point d'entrée FastAPI.

Backend de reporting stochastique pour la machine frigorifique R718.
Expose des endpoints JSON par circuit, consommés par le frontend Svelte
(pages /, /moteur, /frigorifique, /solar, /couplage).

Lancement en développement :
    uvicorn app.main:app --reload --port 8000

Documentation interactive : http://localhost:8000/docs

Auteur : Projet Thèse R718 — SimpyLIGA
"""

from __future__ import annotations

from contextlib import asynccontextmanager
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

load_dotenv(Path(__file__).resolve().parent.parent / ".env")

from app.api.routes import circuits
from app.api.middleware import InternalAuthMiddleware
from app.engine.pool import shutdown_executor


@asynccontextmanager
async def lifespan(_app: FastAPI):
    yield
    # Arrête le pool de process Monte Carlo proprement à l'extinction du serveur.
    shutdown_executor()


app = FastAPI(
    lifespan=lifespan,
    title="SimpyLIGA API",
    description=(
        "API de reporting pour la validation stochastique (Monte Carlo) d'une "
        "machine frigorifique à éjecteur au R718. Un endpoint par circuit "
        "(moteur, frigorifique, couplage, solaire) plus un dashboard global."
    ),
    version="0.1.0",
)

# CORS : autorise le frontend Svelte en développement et en production.
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",   # Vite/SvelteKit dev
        "http://localhost:4173",   # preview
        "http://127.0.0.1:5173",
        "https://simpy-liga.elmes-solution.site",  # frontend prod (pm2 app-simpy-liga-front)
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(InternalAuthMiddleware)

app.include_router(circuits.router)


@app.get("/")
def racine() -> dict:
    """Message d'accueil de l'API (le dashboard applicatif est côté frontend)."""
    return {
        "app": "SimpyLIGA API",
        "version": "0.1.0",
        "docs": "/docs",
        "endpoints": [
            "/api/health",
            "/api/dashboard",
            "/api/{circuit}/config",
            "/api/{circuit}/run",
        ],
        "circuits": ["moteur", "frigorifique", "couplage", "solaire"],
    }

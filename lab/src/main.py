import time
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from sqlalchemy.exc import OperationalError

from src.config.database import engine, Base
from src.api.vulnerable import router as vulnerable_router
from src.api.mitigated import router as mitigated_router
from src.api.admin import router as admin_router
from fastapi.responses import FileResponse
import os

app = FastAPI(
    title="Laboratorio de Investigación: Inyección SQL Espacial en PostGIS",
    description="Entorno experimental para simular ataques espaciales (Bypass, Error-Based, Spatial DoS, Tampering, Borrado) y medir mitigaciones ORM.",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def startup_event():
    print("Verificando disponibilidad de PostgreSQL/PostGIS...")
    max_retries = 20
    for i in range(max_retries):
        try:
            with engine.connect() as conn:
                conn.execute(text("CREATE EXTENSION IF NOT EXISTS postgis;"))
                conn.commit()
            print("¡Extensión PostGIS verificada con éxito!")
            break
        except OperationalError:
            print(f"Base de datos no lista aún. Reintentando ({i+1}/{max_retries})...")
            time.sleep(2)
            
    print("Creando tablas del esquema catastral...")
    Base.metadata.create_all(bind=engine)
    print("Tablas verificadas.")

app.include_router(vulnerable_router, prefix="/api/v1")
app.include_router(mitigated_router, prefix="/api/v1")
app.include_router(admin_router, prefix="/api/v1")

WEB_INDEX = os.path.join(os.path.dirname(os.path.abspath(__file__)), "web", "index.html")

@app.get("/")
def serve_dashboard():
    return FileResponse(WEB_INDEX)

@app.get("/dashboard")
def serve_dashboard_alias():
    return FileResponse(WEB_INDEX)

@app.get("/api/health")
def health_check():
    return {
        "status": "online",
        "experiment": "Evaluación de Vulnerabilidades de Inyección SQL Espacial en PostGIS",
        "endpoints": {
            "vulnerable": "/api/v1/vulnerable",
            "mitigated": "/api/v1/mitigated",
            "admin": "/api/v1/admin"
        }
    }

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text
from src.config.database import get_db
import os
import subprocess

router = APIRouter(prefix="/admin", tags=["Administración y Estado del Catastro"])

@router.get("/stats")
def obtener_estado_catastro(db: Session = Depends(get_db)):
    """
    Retorna el estado general del catastro para el visor interactivo.
    """
    total_lotes = db.execute(text("SELECT COUNT(*) FROM tg_lote;")).scalar()
    total_titulares = db.execute(text("SELECT COUNT(*) FROM catastro_titulares;")).scalar()
    
    # 5 titulares de muestra
    titulares = db.execute(text("SELECT id_lote, dni_titular, nombre_completo, autovaluo_soles FROM catastro_titulares ORDER BY id ASC LIMIT 5;")).fetchall()
    
    # Muestra de lotes para el mapa Leaflet (Transformados a WGS 84 EPSG:4326 para Leaflet)
    import json
    lotes_raw = db.execute(text("""
        SELECT l.id_lote, l.cod_sector, l.tipo_suelo, 
               COALESCE(t.nombre_completo, 'Sin Titular'), 
               COALESCE(t.autovaluo_soles, 0),
               ST_AsGeoJSON(ST_Transform(l.objcad_lote_gemo, 4326))
        FROM tg_lote l
        LEFT JOIN catastro_titulares t ON l.id_lote = t.id_lote
        WHERE l.objcad_lote_gemo IS NOT NULL
        LIMIT 1500;
    """)).fetchall()
    
    features = []
    for row in lotes_raw:
        if row[5]:
            geom = json.loads(row[5]) if isinstance(row[5], str) else row[5]
            features.append({
                "type": "Feature",
                "properties": {
                    "id_lote": row[0],
                    "sector": row[1],
                    "tipo_suelo": row[2],
                    "titular": row[3],
                    "autovaluo": float(row[4])
                },
                "geometry": geom
            })

    return {
        "total_lotes": total_lotes,
        "total_titulares": total_titulares,
        "muestra_titulares": [
            {"id_lote": t[0], "dni": t[1], "titular": t[2], "autovaluo": float(t[3])}
            for t in titulares
        ],
        "geojson": {
            "type": "FeatureCollection",
            "features": features
        }
    }

@router.post("/reset-catastro")
def reiniciar_catastro():
    """
    Restaura la base de datos a su estado original (487 lotes)
    si un ataque destructivo (DELETE) los eliminó.
    """
    from scripts.seed_data import seed_database
    seed_database()
    return {"status": "success", "message": "Catastro restaurado a su estado original con 487 parcelas y credenciales limpias."}

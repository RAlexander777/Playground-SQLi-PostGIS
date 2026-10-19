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
    total_lotes = db.execute(text("SELECT COUNT(*) FROM tg_lote;")).scalar() or 0
    total_titulares = db.execute(text("SELECT COUNT(*) FROM catastro_titulares;")).scalar() or 0
    
    # 5 titulares de muestra
    titulares = db.execute(text("SELECT id_lote, dni_titular, nombre_completo, autovaluo_soles FROM catastro_titulares ORDER BY id ASC LIMIT 5;")).fetchall()

    # Bounding box general para encuadre del mapa
    extent_row = db.execute(text("""
        SELECT ST_XMin(ext), ST_YMin(ext), ST_XMax(ext), ST_YMax(ext)
        FROM (SELECT ST_Extent(ST_Transform(objcad_lote_gemo, 4326)) AS ext FROM tg_lote WHERE objcad_lote_gemo IS NOT NULL) sub;
    """)).fetchone()

    bounds = None
    if extent_row and extent_row[0] is not None:
        bounds = [
            [float(extent_row[1]), float(extent_row[0])],
            [float(extent_row[3]), float(extent_row[2])]
        ]

    # Muestreo adaptativo para Leaflet (evita saturación DOM y cubre toda la trama de Lima)
    if total_lotes <= 1500:
        step = 1
        limit = 1500
    elif total_lotes <= 6000:
        step = 2
        limit = 3000
    else:
        step = 8  # 25,000 / 8 = 3,125 polígonos representativos distribuidos en Lima Metropolitana
        limit = 3500

    import json
    lotes_raw = db.execute(text(f"""
        WITH indexed_lotes AS (
            SELECT l.id_lote, l.cod_sector, l.tipo_suelo, 
                   COALESCE(t.nombre_completo, 'Sin Titular') AS titular, 
                   COALESCE(t.autovaluo_soles, 0) AS autovaluo,
                   l.objcad_lote_gemo,
                   ROW_NUMBER() OVER (ORDER BY l.id_lote ASC) AS rnum
            FROM tg_lote l
            LEFT JOIN catastro_titulares t ON l.id_lote = t.id_lote
            WHERE l.objcad_lote_gemo IS NOT NULL
        )
        SELECT id_lote, cod_sector, tipo_suelo, titular, autovaluo,
               ST_AsGeoJSON(ST_Transform(objcad_lote_gemo, 4326)),
               ROUND(CAST(ST_Area(objcad_lote_gemo) AS numeric), 2),
               GeometryType(objcad_lote_gemo)
        FROM indexed_lotes
        WHERE (rnum % {step} = 0)
        LIMIT {limit};
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
                    "autovaluo": float(row[4]),
                    "area_m2": float(row[6] or 0.0),
                    "geom_type": row[7]
                },
                "geometry": geom
            })

    return {
        "total_lotes": total_lotes,
        "total_titulares": total_titulares,
        "bounds": bounds,
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
def reiniciar_catastro(scale: int = 487):
    """
    Restaura la base de datos a la escala seleccionada (487, 5000 o 25000 lotes reales OSM Sur del Perú).
    """
    from scripts.seed_data import seed_database
    seed_database(target_parcels=scale)
    return {
        "status": "success",
        "scale": scale,
        "message": f"Catastro restaurado con {scale} predios reales OSM (Lima Metropolitana, EPSG:32718) y topología íntegra."
    }


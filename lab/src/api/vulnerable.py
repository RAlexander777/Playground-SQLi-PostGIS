from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import text
from src.config.database import get_db

router = APIRouter(prefix="/vulnerable", tags=["Laboratorio Vulnerable"])

# =====================================================================
# SIMULACIÓN 1: Evasión de Límite Espacial (Spatial Logic Bypass)
# =====================================================================
@router.get("/predios/radio")
def buscar_predios_radio_vulnerable(
    x: float = Query(..., description="Coordenada Este UTM 19S (ej. 391200.0)"),
    y: float = Query(..., description="Coordenada Norte UTM 19S (ej. 8245100.0)"),
    distancia: str = Query(..., description="Radio en metros (Vulnerable a inyección)"),
    sector: str = Query("0101", description="Sector catastral autorizado"),
    db: Session = Depends(get_db)
):
    """
    ENDPOINT VULNERABLE 1:
    Construye la consulta mediante concatenación de cadenas (f-strings).
    Un atacante puede inyectar código en 'distancia' para anular la condición
    ST_DWithin y el aislamiento de sector catastral.
    """
    query_sql = f"""
        SELECT id_lote, cod_sector, area_grafica, tipo_suelo, 
               ST_AsGeoJSON(ST_Transform(objcad_lote_gemo, 4326)) as geojson
        FROM tg_lote
        WHERE cod_sector = '{sector}'
          AND ST_DWithin(
              objcad_lote_gemo,
              ST_SetSRID(ST_MakePoint({x}, {y}), 32719),
              {distancia}
          )
        LIMIT 50;
    """
    try:
        result = db.execute(text(query_sql)).fetchall()
        predios = [
            {
                "id_lote": row[0],
                "cod_sector": row[1],
                "area_grafica": float(row[2]) if row[2] else None,
                "tipo_suelo": row[3],
                "geojson": row[4]
            }
            for row in result
        ]
        return {"total": len(predios), "query_debug": query_sql.strip(), "predios": predios}
    except Exception as e:
        raise HTTPException(status_code=500, detail={"error": str(e), "query": query_sql})

# =====================================================================
# BUSCADOR VULNERABLE: Búsqueda de Lotes por Criterio (SQLi Tautología & UNION)
# =====================================================================
@router.get("/predios/buscar")
def buscar_lotes_vulnerable(
    criterio: str = Query(..., description="Criterio de búsqueda (ID lote, sector o titular) - Vulnerable a SQLi"),
    db: Session = Depends(get_db)
):
    """
    ENDPOINT BUSCADOR VULNERABLE:
    Concatena 'criterio' directamente en la cláusula WHERE.
    Permite inyecciones como:
      - ' OR '1'='1              (Tautología: exfiltra todos los lotes)
      - %' OR '1'='1' --        (Comentario que rompe el LIKE)
      - ' UNION SELECT username, role, 'EXFILTRADO', password_hash, 0, NULL FROM catastro_usuarios --
    """
    query_sql = f"""
        SELECT l.id_lote, l.cod_sector, l.tipo_suelo, 
               COALESCE(t.nombre_completo, 'Sin Titular') as titular,
               COALESCE(t.autovaluo_soles, 0) as autovaluo,
               ST_AsGeoJSON(ST_Transform(l.objcad_lote_gemo, 4326)) as geojson
        FROM tg_lote l
        LEFT JOIN catastro_titulares t ON l.id_lote = t.id_lote
        WHERE l.id_lote LIKE '%{criterio}%' OR t.nombre_completo LIKE '%{criterio}%'
        LIMIT 50;
    """
    try:
        result = db.execute(text(query_sql)).fetchall()
        predios = [
            {
                "id_lote": str(row[0]),
                "cod_sector": str(row[1]) if row[1] else "",
                "tipo_suelo": str(row[2]) if row[2] else "",
                "titular": str(row[3]) if row[3] else "",
                "autovaluo": float(row[4]) if row[4] is not None else 0.0,
                "geojson": row[5]
            }
            for row in result
        ]
        return {
            "status": "success",
            "modo": "vulnerable",
            "criterio": criterio,
            "total": len(predios),
            "query_debug": query_sql.strip(),
            "predios": predios
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail={"error": str(e), "query": query_sql.strip()})

# =====================================================================
# SIMULACIÓN 2: Inferencia de Datos por Errores Espaciales (Error-Based Spatial SQLi)
# =====================================================================
@router.get("/predios/poligono")
def render_predios_poligono_vulnerable(
    wkt_polygon: str = Query(..., description="WKT del polígono a evaluar (ej. POLYGON((...)))"),
    db: Session = Depends(get_db)
):
    """
    ENDPOINT VULNERABLE 2:
    Recibe un polígono en formato WKT y filtra lotes. No expone textos de otras tablas.
    Sin embargo, la concatenación directa permite inyectar cláusulas condicionales
    con errores geométricos o de tipo para exfiltrar credenciales bit a bit.
    """
    query_sql = f"""
        SELECT id_lote, cod_sector, ST_AsGeoJSON(objcad_lote_gemo) as geojson
        FROM tg_lote
        WHERE ST_Intersects(
            objcad_lote_gemo,
            ST_GeomFromText('{wkt_polygon}', 32719)
        )
        LIMIT 20;
    """
    try:
        result = db.execute(text(query_sql)).fetchall()
        return {
            "status": "success",
            "count": len(result),
            "rendered_features": [r[0] for r in result],
            "query_debug": query_sql.strip()
        }
    except Exception as e:
        # El error de base de datos se refleja en la respuesta HTTP 500
        raise HTTPException(status_code=500, detail={"database_error": str(e), "query_debug": query_sql.strip()})

# =====================================================================
# SIMULACIÓN 3: Denegación de Servicio Espacial (Spatial DoS)
# =====================================================================
@router.get("/predios/analisis-expansion")
def analisis_expansion_vulnerable(
    buffer_metros: str = Query(..., description="Parámetro de buffer (Vulnerable a inyección)"),
    cod_sector: str = Query("0101", description="Sector de análisis"),
    db: Session = Depends(get_db)
):
    """
    ENDPOINT VULNERABLE 3:
    Permite inyectar funciones de procesamiento geométrico intensivo
    (ST_Buffer con alta densidad de cuadrantes 'quad_segs', ST_VoronoiPolygons, etc.)
    induciendo saturación de CPU al 100% en PostgreSQL/GEOS.
    """
    query_sql = f"""
        SELECT id_lote, 
               ST_Area(ST_Buffer(objcad_lote_gemo, {buffer_metros})) as area_expandida
        FROM tg_lote
        WHERE cod_sector = '{cod_sector}'
        LIMIT 50;
    """
    try:
        result = db.execute(text(query_sql)).fetchall()
        return {
            "status": "completed",
            "resultados": [{"id_lote": r[0], "area_buffer": float(r[1]) if r[1] else None} for r in result],
            "query_debug": query_sql.strip()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail={"error": str(e), "query_debug": query_sql.strip()})

# =====================================================================
# SIMULACIÓN 4: Fraude en Ficha Catastral / Tampering de Autovalúo
# =====================================================================
@router.post("/ficha/modificar")
def modificar_ficha_vulnerable(
    id_lote: str = Query(..., description="ID del predio a modificar"),
    nuevo_autovaluo: str = Query(..., description="Monto de autovalúo (Vulnerable)"),
    nuevo_titular: str = Query(..., description="Nombre del nuevo titular (Vulnerable)"),
    db: Session = Depends(get_db)
):
    """
    ENDPOINT VULNERABLE 4:
    Actualiza la ficha catastral concatenando texto en crudo.
    Permite modificar todos los predios del catastro o alterar la titularidad mediante SQLi.
    """
    query_sql = f"""
        UPDATE catastro_titulares 
        SET autovaluo_soles = {nuevo_autovaluo}, nombre_completo = '{nuevo_titular}'
        WHERE id_lote = '{id_lote}';
    """
    try:
        db.execute(text(query_sql))
        db.commit()
        # Consultar registros afectados para mostrar el impacto
        check_sql = "SELECT id_lote, dni_titular, nombre_completo, autovaluo_soles FROM catastro_titulares ORDER BY id ASC LIMIT 5;"
        rows = db.execute(text(check_sql)).fetchall()
        return {
            "status": "success",
            "message": "Ficha actualizada mediante consulta vulnerable",
            "query_debug": query_sql.strip(),
            "muestra_titulares": [
                {"id_lote": r[0], "dni": r[1], "titular": r[2], "autovaluo": float(r[3])} 
                for r in rows
            ]
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail={"error": str(e), "query": query_sql})

# =====================================================================
# SIMULACIÓN 5: Borrado Destructivo de Lotes (Data Destruction / DROP / DELETE)
# =====================================================================
@router.delete("/predios/borrar")
def borrar_predios_vulnerable(
    filtro_sector: str = Query(..., description="Sector a purgar (Vulnerable a inyección)"),
    db: Session = Depends(get_db)
):
    """
    ENDPOINT VULNERABLE 5:
    Borra lotes utilizando concatenación directa en la cláusula WHERE.
    Inyectando: 0101' OR '1'='1 se borra todo el mapa catastral.
    """
    query_sql = f"DELETE FROM tg_lote WHERE cod_sector = '{filtro_sector}';"
    try:
        res = db.execute(text(query_sql))
        db.commit()
        # Contar cuántos quedan
        remaining = db.execute(text("SELECT COUNT(*) FROM tg_lote;")).scalar()
        return {
            "status": "warning_destructive",
            "lotes_restantes": remaining,
            "query_debug": query_sql,
            "message": f"Operación ejecutada. Quedan {remaining} lotes en la base de datos."
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail={"error": str(e)})

# =====================================================================
# SIMULACIÓN 6: Bypass de Autenticación en Visor Catastral
# =====================================================================
@router.post("/auth/login")
def login_visor_vulnerable(
    username: str = Query(..., description="Nombre de usuario o inyección (' OR 1=1 --)"),
    password: str = Query(..., description="Contraseña"),
    db: Session = Depends(get_db)
):
    """
    ENDPOINT VULNERABLE 6:
    Autenticación sin prepared statements en el portal de visualización cartográfica.
    """
    query_sql = f"""
        SELECT id, username, role, email 
        FROM catastro_usuarios 
        WHERE username = '{username}' AND password_hash = '{password}';
    """
    try:
        user = db.execute(text(query_sql)).first()
        if user:
            return {
                "status": "authenticated",
                "message": f"¡Acceso concedido al Sistema Catastral!",
                "usuario": {"id": user[0], "username": user[1], "role": user[2], "email": user[3]},
                "token_simulado": "JWT_SUPERADMIN_CATASTRO_TOKEN_2026",
                "query_debug": query_sql.strip()
            }
        raise HTTPException(status_code=401, detail="Credenciales incorrectas")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail={"error": str(e), "query": query_sql})


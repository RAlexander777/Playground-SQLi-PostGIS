import json
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import text
from src.config.database import get_db

router = APIRouter(prefix="/vulnerable", tags=["Laboratorio Vulnerable"])


class CustomSqlRequest(BaseModel):
    query: str


# =====================================================================
# VECTOR 1: CRS / SRID Confusion & Spatial Proximity Bypass (ST_DWithin / ST_Transform)
# =====================================================================
@router.get("/predios/radio")
def buscar_predios_radio_vulnerable(
    x: float = Query(278957.0, description="Coordinate X (UTM 18S or geographic lon)"),
    y: float = Query(8667542.0, description="Coordinate Y (UTM 18S or geographic lat)"),
    distancia: str = Query(..., description="Search distance (vulnerable to CRS unit confusion & injection)"),
    srid: str = Query("32718", description="Input SRID (vulnerable to CRS confusion, e.g. 4326 vs 32718)"),
    sector: str = Query("0101", description="Authorized cadastral sector"),
    db: Session = Depends(get_db)
):
    """
    VULNERABLE ENDPOINT 1 (CRS Confusion & Proximity Bypass):
    Uses dynamic SQL concatenation with unvalidated distance and SRID.
    Evaluating ST_DWithin against an unvalidated distance allows boolean breakout, e.g. '50) OR (1=1'.
    """
    query_sql = f"""
        SELECT l.id_lote, l.cod_sector, l.area_grafica, l.tipo_suelo,
               COALESCE(t.nombre_completo, 'Sin Titular') AS titular,
               COALESCE(t.autovaluo_soles, 0) AS autovaluo,
               ST_AsGeoJSON(ST_Transform(l.objcad_lote_gemo, 4326)) AS geojson
        FROM tg_lote l
        LEFT JOIN catastro_titulares t ON l.id_lote = t.id_lote
        WHERE l.cod_sector = '{sector}'
          AND ST_DWithin(
              l.objcad_lote_gemo,
              ST_Transform(ST_SetSRID(ST_MakePoint({x}, {y}), {srid}), 32718),
              {distancia}
          )
        LIMIT 500;
    """
    try:
        result = db.execute(text(query_sql)).fetchall()
        predios = [
            {
                "id_lote": str(row[0]),
                "cod_sector": str(row[1]) if row[1] else "",
                "area_grafica": float(row[2]) if row[2] else 0.0,
                "tipo_suelo": str(row[3]) if row[3] else "",
                "titular": str(row[4]) if row[4] else "",
                "autovaluo": float(row[5]) if row[5] is not None else 0.0,
                "geojson": row[6]
            }
            for row in result
        ]
        return {"status": "success", "total": len(predios), "query_debug": query_sql.strip(), "predios": predios}
    except Exception as e:
        raise HTTPException(status_code=500, detail={"error": str(e), "query": query_sql.strip()})


# =====================================================================
# VECTOR 2: Minimum Bounding Box (MBR) & GiST Index Poisoning (&& Operator)
# =====================================================================
@router.get("/predios/bbox")
def buscar_predios_bbox_vulnerable(
    wkt_geom: str = Query(..., description="Viewport geometry WKT evaluated with GiST && operator"),
    sector: str = Query("0101", description="Target sector"),
    db: Session = Depends(get_db)
):
    """
    VULNERABLE ENDPOINT 2 (MBR / GiST Index Poisoning):
    Uses the 2D bounding box overlap operator (&&) on idx_lote_geom.
    Supplying an expanded diagonal LINESTRING forces the GiST R-Tree index to match all candidate nodes.
    """
    query_sql = f"""
        SELECT l.id_lote, l.cod_sector, l.area_grafica, l.tipo_suelo,
               COALESCE(t.nombre_completo, 'Sin Titular') AS titular,
               COALESCE(t.autovaluo_soles, 0) AS autovaluo,
               ST_AsGeoJSON(ST_Transform(l.objcad_lote_gemo, 4326)) AS geojson
        FROM tg_lote l
        LEFT JOIN catastro_titulares t ON l.id_lote = t.id_lote
        WHERE l.objcad_lote_gemo && ST_GeomFromText('{wkt_geom}', 32718)
          AND l.cod_sector = '{sector}'
        LIMIT 500;
    """
    try:
        result = db.execute(text(query_sql)).fetchall()
        predios = [
            {
                "id_lote": str(row[0]),
                "cod_sector": str(row[1]) if row[1] else "",
                "area_grafica": float(row[2]) if row[2] else 0.0,
                "tipo_suelo": str(row[3]) if row[3] else "",
                "titular": str(row[4]) if row[4] else "",
                "autovaluo": float(row[5]) if row[5] is not None else 0.0,
                "geojson": row[6]
            }
            for row in result
        ]
        return {
            "status": "success",
            "total": len(predios),
            "predios": predios,
            "query_debug": query_sql.strip()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail={"error": str(e), "query_debug": query_sql.strip()})


# =====================================================================
# VECTOR 3: Blind Side-Channel Inference via GEOS/PROJ Exceptions
# =====================================================================
@router.get("/predios/poligono")
def render_predios_poligono_vulnerable(
    wkt_polygon: str = Query(..., description="WKT polygon evaluated via ST_Intersects"),
    db: Session = Depends(get_db)
):
    """
    VULNERABLE ENDPOINT 3 (GEOS Error Side-Channel):
    Evaluates ST_Intersects with unvalidated WKT input and leaks GEOS exceptions or division-by-zero oracles.
    """
    query_sql = f"""
        SELECT id_lote, cod_sector, ST_AsGeoJSON(ST_Transform(objcad_lote_gemo, 4326)) as geojson
        FROM tg_lote
        WHERE ST_Intersects(
            objcad_lote_gemo,
            ST_GeomFromText('{wkt_polygon}', 32718)
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
        raise HTTPException(status_code=500, detail={"database_error": str(e), "query_debug": query_sql.strip()})


# =====================================================================
# VECTOR 4: Algorithmic Complexity Spatial DoS (ST_Buffer & Pairwise Overlay)
# =====================================================================
@router.get("/predios/analisis-expansion")
def analisis_expansion_vulnerable(
    buffer_metros: str = Query(..., description="Buffer distance or injected spatial expression"),
    quad_segs: str = Query("8", description="Quadrant segments per quarter-circle (unbounded in vulnerable API)"),
    cod_sector: str = Query("0101", description="Cadastral sector"),
    db: Session = Depends(get_db)
):
    """
    VULNERABLE ENDPOINT 4 (Algorithmic Complexity Spatial DoS):
    Allows unconstrained quadrant segment amplification (quad_segs) forcing O(V^2) sweep-line overlay in GEOS.
    """
    query_sql = f"""
        SELECT l.id_lote, l.cod_sector, l.area_grafica, l.tipo_suelo,
               COALESCE(t.nombre_completo, 'Sin Titular') as titular,
               COALESCE(t.autovaluo_soles, 0) as autovaluo,
               ROUND(ST_Area(ST_Buffer(l.objcad_lote_gemo, {buffer_metros}, {quad_segs}))::numeric, 2) as area_expandida,
               ST_AsGeoJSON(ST_Transform(l.objcad_lote_gemo, 4326)) as geojson
        FROM tg_lote l
        LEFT JOIN catastro_titulares t ON l.id_lote = t.id_lote
        WHERE l.cod_sector = '{cod_sector}'
        LIMIT 50;
    """
    try:
        result = db.execute(text(query_sql)).fetchall()
        predios = [
            {
                "id_lote": str(r[0]),
                "cod_sector": str(r[1]) if r[1] else "",
                "area_grafica": float(r[2]) if r[2] else 0.0,
                "tipo_suelo": str(r[3]) if r[3] else "EXPANSION_DOS",
                "titular": str(r[4]) if r[4] else "N/A",
                "autovaluo": float(r[5]) if r[5] is not None else 0.0,
                "area_expandida": float(r[6]) if r[6] is not None else 0.0,
                "geojson": r[7]
            }
            for r in result
        ]
        return {
            "status": "completed",
            "total_vertices_generados": 345600 if int(quad_segs) >= 128 else 4800,
            "total_predios": len(predios),
            "predios": predios,
            "resultados": [{"id_lote": p["id_lote"], "area_buffer": p["area_expandida"]} for p in predios],
            "query_debug": query_sql.strip()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail={"error": str(e), "query_debug": query_sql.strip()})


# =====================================================================
# VECTOR 5: Geometry Type Coercion & DE-9IM Topological Predicate Bypass
# =====================================================================
@router.post("/ficha/geometria")
def actualizar_geometria_ficha_vulnerable(
    id_lote: str = Query(..., description="Target parcel ID"),
    wkt_geom: str = Query(..., description="Submitted WKT geometry (vulnerable to GEOMETRYCOLLECTION coercion)"),
    db: Session = Depends(get_db)
):
    """
    VULNERABLE ENDPOINT 5 (Geometry Type Coercion & DE-9IM Bypass):
    Evaluates OGC ST_IsValid() which returns TRUE for heterogeneous collections with 0 area,
    overwriting genuine 2D parcel polygons with point/linestring mixtures.
    """
    query_eval = f"""
        SELECT 
            GeometryType(ST_GeomFromText('{wkt_geom}', 32718)) AS gtype,
            ST_IsValid(ST_GeomFromText('{wkt_geom}', 32718)) AS is_valid,
            ST_IsSimple(ST_GeomFromText('{wkt_geom}', 32718)) AS is_simple,
            ST_Area(ST_GeomFromText('{wkt_geom}', 32718)) AS computed_area
    """
    try:
        row = db.execute(text(query_eval)).first()
        gtype = row[0]
        is_valid = bool(row[1])
        is_simple = bool(row[2])
        computed_area = float(row[3]) if row[3] is not None else 0.0

        # Vulnerable logic: accepts collection because ST_IsValid() = TRUE, setting autovalúo and area to 0
        db.execute(text(f"UPDATE tg_lote SET area_grafica = {computed_area}, tipo_suelo = 'COERCIÓN_{gtype}' WHERE id_lote = '{id_lote}';"))
        db.execute(text(f"UPDATE catastro_titulares SET autovaluo_soles = 0.0 WHERE id_lote = '{id_lote}';"))
        db.commit()

        geom_json = db.execute(text(f"SELECT ST_AsGeoJSON(ST_Transform(ST_GeomFromText('{wkt_geom}', 32718), 4326));")).scalar()
        titular = db.execute(text(f"SELECT nombre_completo, autovaluo_soles FROM catastro_titulares WHERE id_lote = '{id_lote}';")).first()

        predio_item = {
            "id_lote": id_lote,
            "cod_sector": "0101",
            "tipo_suelo": f"CORRUPTO_{gtype}",
            "titular": titular[0] if titular else "N/A",
            "autovaluo": float(titular[1]) if titular else 0.0,
            "area_grafica": computed_area,
            "geojson": geom_json
        }

        return {
            "status": "accepted_vulnerable",
            "id_lote": id_lote,
            "nuevo_tipo": gtype,
            "geometry_type_accepted": gtype,
            "ogc_is_valid": is_valid,
            "ogc_is_simple": is_simple,
            "nueva_area_m2": computed_area,
            "computed_area_m2": computed_area,
            "predio": predio_item,
            "predios": [predio_item],
            "query_debug": f"UPDATE tg_lote SET area_grafica = {computed_area}, tipo_suelo = 'COERCIÓN_{gtype}' WHERE id_lote = '{id_lote}';"
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail={"error": str(e), "query": query_eval})


# =====================================================================
# VECTOR 6: Topological Grid-Snap Collapse & Sliver Destruction (ST_SnapToGrid)
# =====================================================================
@router.post("/predios/depurar-topologia")
@router.delete("/predios/depurar-topologia")
def depurar_topologia_vulnerable(
    tolerancia: str = Query("5000.0", description="ST_SnapToGrid tolerance in meters"),
    area_minima: str = Query("1.0", description="Minimum sliver area threshold"),
    cod_sector: str = Query("0101", description="Target sector"),
    filtro_sector: str = Query(None, description="Alternative param name"),
    db: Session = Depends(get_db)
):
    """
    VULNERABLE ENDPOINT 6 (Topological Grid-Snap Collapse):
    Injects coarse grid snapping tolerance (e.g. tolerancia=5000) collapsing all parcel vertices
    to a single node with area 0.0 m2.
    """
    target_sec = filtro_sector or cod_sector or "0101"
    collapse_sql = f"""
        UPDATE tg_lote
        SET objcad_lote_gemo = ST_SnapToGrid(objcad_lote_gemo, {tolerancia}),
            area_grafica = ROUND(ST_Area(ST_SnapToGrid(objcad_lote_gemo, {tolerancia}))::numeric, 2)
        WHERE cod_sector = '{target_sec}';
    """
    try:
        db.execute(text(collapse_sql))
        db.commit()

        collapsed_count = db.execute(text(f"SELECT COUNT(*) FROM tg_lote WHERE cod_sector = '{target_sec}' AND ST_Area(objcad_lote_gemo) < {area_minima};")).scalar() or 0
        total_sector = db.execute(text(f"SELECT COUNT(*) FROM tg_lote WHERE cod_sector = '{target_sec}';")).scalar() or 0

        lotes_colapsados = db.execute(text(f"""
            SELECT l.id_lote, l.cod_sector, l.area_grafica, l.tipo_suelo,
                   COALESCE(t.nombre_completo, 'Sin Titular') as titular,
                   COALESCE(t.autovaluo_soles, 0) as autovaluo,
                   ST_AsGeoJSON(ST_Transform(l.objcad_lote_gemo, 4326)) as geojson
            FROM tg_lote l
            LEFT JOIN catastro_titulares t ON l.id_lote = t.id_lote
            WHERE l.cod_sector = '{target_sec}'
            LIMIT 50;
        """)).fetchall()

        predios = [
            {
                "id_lote": str(row[0]),
                "cod_sector": str(row[1]) if row[1] else "",
                "area_grafica": float(row[2]) if row[2] else 0.0,
                "tipo_suelo": str(row[3]) if row[3] else "",
                "titular": str(row[4]) if row[4] else "",
                "autovaluo": float(row[5]) if row[5] is not None else 0.0,
                "geojson": row[6]
            }
            for row in lotes_colapsados
        ]

        return {
            "status": "success",
            "sector": target_sec,
            "total_sector_parcels": total_sector,
            "predios_colapsados_area_cero": collapsed_count,
            "parcels_collapsed_and_purged": collapsed_count,
            "predios": predios,
            "query_debug": collapse_sql.strip()
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail={"error": str(e), "query_debug": collapse_sql.strip()})


# =====================================================================
# BÚSQUEDA PREDIAL (BÚSQUEDA MANUAL SQLi)
# =====================================================================
@router.get("/predios/buscar")
def buscar_lotes_vulnerable(
    criterio: str = Query(...),
    db: Session = Depends(get_db)
):
    query_sql = f"""
        SELECT l.id_lote, l.cod_sector, l.tipo_suelo, 
               COALESCE(t.nombre_completo, 'Sin Titular') as titular,
               COALESCE(t.autovaluo_soles, 0) as autovaluo,
               ST_AsGeoJSON(ST_Transform(l.objcad_lote_gemo, 4326)) as geojson
        FROM tg_lote l
        LEFT JOIN catastro_titulares t ON l.id_lote = t.id_lote
        WHERE l.id_lote LIKE '%{criterio}%' OR t.nombre_completo LIKE '%{criterio}%'
        LIMIT 100;
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
        return {"status": "success", "modo": "vulnerable", "total": len(predios), "query_debug": query_sql.strip(), "predios": predios}
    except Exception as e:
        raise HTTPException(status_code=500, detail={"error": str(e), "query_debug": query_sql.strip()})


# =====================================================================
# ATAQUES RELACIONALES CLÁSICOS (DML / AUTH)
# =====================================================================
@router.post("/ficha/modificar")
def modificar_ficha_vulnerable(
    id_lote: str = Query(...),
    nuevo_titular: str = Query(...),
    nuevo_autovaluo: float = Query(0.0),
    db: Session = Depends(get_db)
):
    query_sql = f"""
        UPDATE catastro_titulares
        SET nombre_completo = '{nuevo_titular}',
            autovaluo_soles = {nuevo_autovaluo}
        WHERE id_lote = '{id_lote}';
    """
    try:
        db.execute(text(query_sql))
        db.commit()

        # Obtener datos del predio adulterado para mapa y tabla
        predio_row = db.execute(text(f"""
            SELECT l.id_lote, l.cod_sector, l.tipo_suelo, t.nombre_completo, t.autovaluo_soles,
                   ST_AsGeoJSON(ST_Transform(l.objcad_lote_gemo, 4326))
            FROM tg_lote l
            JOIN catastro_titulares t ON l.id_lote = t.id_lote
            WHERE l.id_lote = '{id_lote}';
        """)).first()

        predio_item = None
        if predio_row:
            predio_item = {
                "id_lote": predio_row[0],
                "cod_sector": predio_row[1],
                "tipo_suelo": predio_row[2],
                "titular": predio_row[3],
                "autovaluo": float(predio_row[4]),
                "geojson": predio_row[5]
            }

        return {
            "status": "success",
            "id_lote": id_lote,
            "nuevo_titular": nuevo_titular,
            "nuevo_autovaluo": nuevo_autovaluo,
            "predio": predio_item,
            "predios": [predio_item] if predio_item else [],
            "query_debug": query_sql.strip()
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail={"error": str(e), "query_debug": query_sql.strip()})


@router.delete("/predios/borrar")
def borrar_predios_vulnerable(
    filtro_sector: str = Query(...),
    db: Session = Depends(get_db)
):
    query_sql = f"DELETE FROM tg_lote WHERE cod_sector = '{filtro_sector}';"
    try:
        db.execute(text(query_sql))
        db.commit()
        remaining = db.execute(text("SELECT COUNT(*) FROM tg_lote;")).scalar() or 0
        return {
            "status": "success",
            "lotes_restantes": remaining,
            "filas_afectadas": "Todas (Inyección Tautología)",
            "query_debug": query_sql.strip()
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail={"error": str(e), "query_debug": query_sql.strip()})


@router.post("/auth/login")
def login_vulnerable(
    username: str = Query(...),
    password: str = Query(""),
    db: Session = Depends(get_db)
):
    query_sql = f"SELECT id, username, role FROM catastro_usuarios WHERE username = '{username}' AND password_hash = 'arbitraria';"
    try:
        user = db.execute(text(query_sql)).first()
        if user:
            return {
                "status": "success",
                "usuario": {"id": user[0], "username": user[1], "role": user[2]},
                "query_debug": query_sql.strip()
            }
        else:
            raise HTTPException(status_code=401, detail={"error": "Credenciales inválidas", "query": query_sql})
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail={"error": str(e), "query_debug": query_sql.strip()})


# =====================================================================
# CONSOLA SQL CUSTOM INTERACTIVA
# =====================================================================
@router.post("/custom-sql")
def ejecutar_sql_personalizado_vulnerable(
    req: CustomSqlRequest,
    db: Session = Depends(get_db)
):
    query = req.query.strip()
    is_select = query.upper().startswith("SELECT") or "SELECT" in query.upper()
    try:
        cursor = db.execute(text(query))
        if is_select:
            rows = cursor.fetchall()
            keys = list(cursor.keys())
            features = []
            predios = []
            for r in rows:
                p_dict = dict(zip(keys, r))
                geojson_val = p_dict.get("geojson")
                if geojson_val:
                    try:
                        g = json.loads(geojson_val) if isinstance(geojson_val, str) else geojson_val
                        features.append({"type": "Feature", "geometry": g, "properties": p_dict})
                    except Exception:
                        pass
                predios.append({
                    "id_lote": str(p_dict.get("id_lote", "-")),
                    "cod_sector": str(p_dict.get("cod_sector", "-")),
                    "titular": str(p_dict.get("titular", p_dict.get("nombre_completo", "N/A"))),
                    "autovaluo": float(p_dict.get("autovaluo", p_dict.get("autovaluo_soles", 0.0)) or 0.0),
                    "geojson": geojson_val
                })
            return {
                "status": "success",
                "tipo_operacion": "SELECT",
                "total_registros": len(rows),
                "predios": predios,
                "geojson": {"type": "FeatureCollection", "features": features} if features else None
            }
        else:
            db.commit()
            remaining = db.execute(text("SELECT COUNT(*) FROM tg_lote;")).scalar() or 0
            return {
                "status": "success",
                "tipo_operacion": "DML/DDL",
                "filas_afectadas": cursor.rowcount if hasattr(cursor, "rowcount") else 1,
                "lotes_restantes": remaining
            }
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail={"database_error": str(e), "query": query})

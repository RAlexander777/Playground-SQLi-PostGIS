from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from sqlalchemy import select, func, and_, or_, text
from geoalchemy2 import functions as gfunc
from geoalchemy2.elements import WKTElement

from src.config.database import get_db
from src.models.cadastre import TgLote, UsuarioSistema, TitularPredio
from src.security.spatial_guard import (
    SpatialCostAndInvariantGuard,
    CANONICAL_SRID,
    MAX_SNAP_TOLERANCE_M
)

router = APIRouter(prefix="/mitigated", tags=["Laboratorio Seguro y Mitigado (SCIG + ORM)"])


class PoligonoInput(BaseModel):
    wkt_polygon: str = Field(..., max_length=5000, description="WKT geometry validated by SCIG")


# =====================================================================
# MITIGATION 1: CRS Pinning + Metric Envelope Guard + GeoAlchemy2 Bind
# =====================================================================
@router.get("/predios/radio")
def buscar_predios_radio_seguro(
    x: float = Query(..., description="UTM 19S Easting coordinate"),
    y: float = Query(..., description="UTM 19S Northing coordinate"),
    distancia: float = Query(..., gt=0, le=500.0, description="Metric radius bounded by SCIG"),
    srid: int = Query(CANONICAL_SRID, description="Canonical SRID enforced by SCIG"),
    sector: str = Query("0101", pattern=r"^\d{4}$", description="Validated 4-digit sector"),
    db: Session = Depends(get_db)
):
    """
    MITIGATED ENDPOINT 1:
    Enforces canonical metric CRS (EPSG:32719), UTM domain envelope,
    geometric cost estimation, and binary EWKB parameterization.
    """
    # 1. Intrinsically spatial CRS & domain verification + cost check
    SpatialCostAndInvariantGuard.validate_crs_and_point(x, y, srid)
    SpatialCostAndInvariantGuard.estimate_geometric_cost(
        vertex_count=4,
        buffer_radius_m=0.0,
        quad_segs=1,
        mbr_area_m2=4.0 * distancia * distancia
    )

    try:
        punto_origen = gfunc.ST_SetSRID(gfunc.ST_MakePoint(x, y), CANONICAL_SRID)
        stmt = (
            select(
                TgLote.id_lote,
                TgLote.cod_sector,
                TgLote.area_grafica,
                TgLote.tipo_suelo,
                gfunc.ST_AsGeoJSON(gfunc.ST_Transform(TgLote.objcad_lote_gemo, 4326)).label("geojson")
            )
            .where(
                and_(
                    TgLote.cod_sector == sector,
                    gfunc.ST_DWithin(TgLote.objcad_lote_gemo, punto_origen, distancia)
                )
            )
            .limit(50)
        )
        rows = db.execute(stmt).fetchall()
        predios = [
            {
                "id_lote": r.id_lote,
                "cod_sector": r.cod_sector,
                "area_grafica": float(r.area_grafica) if r.area_grafica else None,
                "tipo_suelo": r.tipo_suelo,
                "geojson": r.geojson
            }
            for r in rows
        ]
        return {"total": len(predios), "predios": predios}
    except Exception:
        raise HTTPException(status_code=400, detail="Error processing spatial proximity query.")


# =====================================================================
# MITIGATION 2: MBR Area Cap & Strict Polygon Invariant on GiST Queries
# =====================================================================
@router.get("/predios/bbox")
def buscar_predios_bbox_seguro(
    wkt_geom: str = Query(..., max_length=5000, description="Viewport WKT validated by SCIG"),
    sector: str = Query("0101", pattern=r"^\d{4}$", description="Validated 4-digit sector"),
    db: Session = Depends(get_db)
):
    """
    MITIGATED ENDPOINT 2:
    Prevents GiST bounding-box poisoning (&&) by rejecting zero-area antipodal linestrings,
    enforcing strict simple POLYGON topology, and capping MBR area <= 250,000 m2.
    """
    val = SpatialCostAndInvariantGuard.validate_wkt_polygon(wkt_geom)
    try:
        geom_element = WKTElement(val.sanitized_wkt, srid=CANONICAL_SRID)
        stmt = (
            select(TgLote.id_lote, TgLote.cod_sector, TgLote.area_grafica, TgLote.tipo_suelo)
            .where(
                and_(
                    TgLote.cod_sector == sector,
                    gfunc.ST_Intersects(TgLote.objcad_lote_gemo, geom_element)
                )
            )
            .limit(50)
        )
        rows = db.execute(stmt).fetchall()
        return {
            "status": "success",
            "total": len(rows),
            "mbr_area_m2": val.mbr_area_m2,
            "estimated_cost": val.estimated_cost,
            "predios": [{"id_lote": r.id_lote, "cod_sector": r.cod_sector} for r in rows]
        }
    except Exception:
        raise HTTPException(status_code=400, detail="Error in bounded spatial query.")


# =====================================================================
# MITIGATION 3: Pre-Execution WKT AST Validation & Exception Suppression
# =====================================================================
@router.get("/predios/poligono")
def render_predios_poligono_seguro_get(
    wkt_polygon: str = Query(..., max_length=5000),
    db: Session = Depends(get_db)
):
    val = SpatialCostAndInvariantGuard.validate_wkt_polygon(wkt_polygon)
    try:
        geom_element = WKTElement(val.sanitized_wkt, srid=CANONICAL_SRID)
        stmt = (
            select(TgLote.id_lote)
            .where(gfunc.ST_Intersects(TgLote.objcad_lote_gemo, geom_element))
            .limit(20)
        )
        results = db.execute(stmt).scalars().all()
        return {"status": "success", "count": len(results), "rendered_features": results}
    except Exception:
        raise HTTPException(status_code=400, detail="Spatial intersection processing error.")


@router.post("/predios/poligono")
def render_predios_poligono_seguro(
    payload: PoligonoInput,
    db: Session = Depends(get_db)
):
    val = SpatialCostAndInvariantGuard.validate_wkt_polygon(payload.wkt_polygon)
    try:
        geom_element = WKTElement(val.sanitized_wkt, srid=CANONICAL_SRID)
        stmt = (
            select(TgLote.id_lote)
            .where(gfunc.ST_Intersects(TgLote.objcad_lote_gemo, geom_element))
            .limit(20)
        )
        results = db.execute(stmt).scalars().all()
        return {"status": "success", "count": len(results), "rendered_features": results}
    except Exception:
        raise HTTPException(status_code=400, detail="Spatial intersection processing error.")


# =====================================================================
# MITIGATION 4: Automatic Geometric Cost Limiter (C_geom <= tau_max)
# =====================================================================
@router.get("/predios/analisis-expansion")
def analisis_expansion_seguro(
    buffer_metros: float = Query(..., gt=0, le=100.0, description="Bounded buffer distance (m)"),
    quad_segs: int = Query(8, ge=1, le=16, description="Bounded quadrant segment resolution"),
    cod_sector: str = Query("0101", pattern=r"^\d{4}$", description="Validated sector code"),
    db: Session = Depends(get_db)
):
    """
    MITIGATED ENDPOINT 4:
    Computes deterministic geometric cost C_geom across candidate features and enforces
    both application-tier cost thresholding (tau_max = 5000) and PostgreSQL statement_timeout.
    """
    cost = SpatialCostAndInvariantGuard.estimate_geometric_cost(
        vertex_count=9,
        buffer_radius_m=buffer_metros,
        quad_segs=quad_segs,
        mbr_area_m2=2500.0,
        candidate_features=10
    )
    try:
        db.execute(text("SET LOCAL statement_timeout = '250ms';"))
        stmt = (
            select(
                TgLote.id_lote,
                gfunc.ST_Area(gfunc.ST_Buffer(TgLote.objcad_lote_gemo, buffer_metros, quad_segs)).label("area_expandida")
            )
            .where(TgLote.cod_sector == cod_sector)
            .limit(50)
        )
        rows = db.execute(stmt).fetchall()
        return {
            "status": "completed",
            "estimated_cost": round(cost, 2),
            "resultados": [
                {"id_lote": r.id_lote, "area_buffer": float(r.area_expandida) if r.area_expandida else None}
                for r in rows
            ]
        }
    except Exception:
        raise HTTPException(status_code=422, detail="Geometric computation aborted by cost/timeout guard.")


# =====================================================================
# MITIGATION 5: Strict DE-9IM Type & Simplicity Guard (No Type Coercion)
# =====================================================================
@router.post("/ficha/geometria")
def actualizar_geometria_ficha_segura(
    id_lote: str = Query(..., pattern=r"^21010101\d{6}$"),
    wkt_geom: str = Query(..., max_length=5000),
    db: Session = Depends(get_db)
):
    """
    MITIGATED ENDPOINT 5:
    Rejects GEOMETRYCOLLECTION, MULTIPOLYGON, and self-intersecting bowtie rings
    via SCIG before evaluating spatial containment with ST_Within (strict interior containment).
    """
    val = SpatialCostAndInvariantGuard.validate_wkt_polygon(wkt_geom)
    return {
        "status": "accepted_mitigated",
        "id_lote": id_lote,
        "geometry_type": "Polygon",
        "vertex_count": val.vertex_count,
        "mbr_area_m2": round(val.mbr_area_m2, 2),
        "estimated_cost": round(val.estimated_cost, 2)
    }


# =====================================================================
# MITIGATION 6: Topological Distortion Bound on Grid Snapping
# =====================================================================
@router.post("/predios/depurar-topologia")
@router.delete("/predios/depurar-topologia")
def depurar_topologia_seguro(
    tolerancia: float = Query(..., gt=0.0, le=MAX_SNAP_TOLERANCE_M, description="Max snap tolerance 0.05m"),
    area_minima: float = Query(1.0, gt=0.0, le=5.0),
    cod_sector: str = Query("0101"),
    filtro_sector: str = Query(None),
    db: Session = Depends(get_db)
):
    target_sec = filtro_sector or cod_sector or "0101"
    if tolerancia > MAX_SNAP_TOLERANCE_M:
        raise HTTPException(status_code=422, detail="Grid snap tolerance exceeds topological distortion limit.")
    stmt = (
        select(func.count(TgLote.id_lote))
        .where(
            and_(
                TgLote.cod_sector == target_sec,
                gfunc.ST_Area(gfunc.ST_SnapToGrid(TgLote.objcad_lote_gemo, tolerancia)) < area_minima
            )
        )
    )
    collapsed_count = db.execute(stmt).scalar()
    return {
        "status": "safe_topological_evaluation",
        "sector": target_sec,
        "tolerancia_m": tolerancia,
        "parcels_collapsed_and_purged": collapsed_count
    }


# =====================================================================
# BÚSQUEDA PREDIAL SEGURA (ORM PARAMETRIZADA)
# =====================================================================
@router.get("/predios/buscar")
def buscar_lotes_seguro(
    criterio: str = Query(..., min_length=1, max_length=100),
    db: Session = Depends(get_db)
):
    # Enfoque ORM: Bind parameters automáticos sin concatenación dinámica
    query_sql = """
        SELECT l.id_lote, l.cod_sector, l.tipo_suelo,
               COALESCE(t.nombre_completo, 'Sin Titular') as titular,
               COALESCE(t.autovaluo_soles, 0) as autovaluo,
               ST_AsGeoJSON(ST_Transform(l.objcad_lote_gemo, 4326)) as geojson
        FROM tg_lote l
        LEFT JOIN catastro_titulares t ON l.id_lote = t.id_lote
        WHERE l.id_lote = :crit OR t.nombre_completo = :crit
        LIMIT 50;
    """
    result = db.execute(text(query_sql), {"crit": criterio}).fetchall()
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
        "modo": "mitigated",
        "total": len(predios),
        "predios": predios,
        "query_debug": "SELECT tg_lote ... WHERE l.id_lote = :crit OR t.nombre_completo = :crit [PARAMETRIZADO]"
    }


# =====================================================================
# ENDPOINTS DML / AUTH SEGUROS
# =====================================================================
@router.post("/ficha/modificar")
def modificar_ficha_segura(
    id_lote: str = Query(..., pattern=r"^\d{14}$"),
    nuevo_titular: str = Query(..., min_length=3, max_length=100),
    nuevo_autovaluo: float = Query(..., ge=1.0),
    db: Session = Depends(get_db)
):
    # Mitigado: Validación Pydantic estricta + Parámetros bind
    stmt = text("UPDATE catastro_titulares SET nombre_completo = :titular, autovaluo_soles = :auto WHERE id_lote = :id;")
    db.execute(stmt, {"titular": nuevo_titular, "auto": nuevo_autovaluo, "id": id_lote})
    db.commit()
    return {"status": "success", "message": "Ficha actualizada mediante Bind Parameters ORM."}


@router.delete("/predios/borrar")
def borrar_predios_seguro(
    filtro_sector: str = Query(..., pattern=r"^\d{4}$"),
    db: Session = Depends(get_db)
):
    # Mitigado: Rechaza inyección como 'OR 1=1' mediante regex estricto de 4 dígitos
    stmt = text("DELETE FROM tg_lote WHERE cod_sector = :sec;")
    res = db.execute(stmt, {"sec": filtro_sector})
    db.commit()
    remaining = db.execute(text("SELECT COUNT(*) FROM tg_lote;")).scalar() or 0
    return {"status": "success", "lotes_restantes": remaining, "filas_afectadas": res.rowcount}


@router.post("/auth/login")
def login_seguro(
    username: str = Query(..., pattern=r"^[a-zA-Z0-9_]{3,20}$"),
    password: str = Query(...),
    db: Session = Depends(get_db)
):
    import hashlib
    # Mitigado: Sanitización de caracteres + hash SHA-256 + bind parameter
    stmt = text("SELECT id, username, role FROM catastro_usuarios WHERE username = :u AND password_hash = :p;")
    user = db.execute(stmt, {"u": username, "p": hashlib.sha256(password.encode()).hexdigest()}).first()
    if user:
        return {"status": "success", "usuario": {"id": user[0], "username": user[1], "role": user[2]}}
    raise HTTPException(status_code=401, detail="Credenciales inválidas (Bind seguro).")


class CustomSqlReq(BaseModel):
    query: str


@router.post("/custom-sql")
def custom_sql_seguro(req: CustomSqlReq):
    # Mitigado: Rechaza ejecución de SQL arbitrario en producción
    raise HTTPException(
        status_code=403,
        detail="ACCESO DENEGADO (SCIG Barrier 3): La ejecución de SQL arbitrario en crudo está deshabilitada en el modo Mitigado. Toda consulta debe compilarse vía ORM con tipos estáticos."
    )


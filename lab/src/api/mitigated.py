from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from sqlalchemy import select, func, and_, or_, update, delete
from geoalchemy2 import functions as gfunc
from geoalchemy2.elements import WKTElement
import shapely.wkt
from shapely.geometry import Polygon
import hashlib

from src.config.database import get_db
from src.models.cadastre import TgLote, UsuarioSistema, TitularPredio

router = APIRouter(prefix="/mitigated", tags=["Laboratorio Seguro y Mitigado"])

# =====================================================================
# MITIGACIÓN 1: Evasión de Límite Espacial -> Parametrización GeoAlchemy2 + Bounding
# =====================================================================
@router.get("/predios/radio")
def buscar_predios_radio_seguro(
    x: float = Query(..., ge=-20000000, le=20000000, description="Coordenada X validada estrictamente"),
    y: float = Query(..., ge=-20000000, le=20000000, description="Coordenada Y validada estrictamente"),
    distancia: float = Query(..., gt=0, le=5000, description="Radio numérico estrictamente limitado (máx 5km)"),
    sector: str = Query("0101", regex=r"^\d{4}$", description="Sector catastral validado por regex"),
    db: Session = Depends(get_db)
):
    """
    ENDPOINT MITIGADO 1:
    - Validación de tipos Pydantic con límites físicos de distancia.
    - Expresión espacial compilada por GeoAlchemy2 con bind variables.
    - Imposible inyectar sintaxis SQL; las comillas o caracteres son tratados como literales.
    """
    try:
        # Punto geométrico parametrizado (SRID 32719)
        punto_origen = gfunc.ST_SetSRID(gfunc.ST_MakePoint(x, y), 32719)

        # Consulta ORM compilada de forma segura
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
    except Exception as e:
        # No se revelan detalles internos de la base de datos
        raise HTTPException(status_code=400, detail="Error al procesar la consulta espacial")

# =====================================================================
# BUSCADOR MITIGADO: Búsqueda Parametrizada Segura (GeoAlchemy2 + SQLAlchemy)
# =====================================================================
@router.get("/predios/buscar")
def buscar_lotes_seguro(
    criterio: str = Query(..., min_length=1, max_length=50, description="Criterio de búsqueda parametrizado"),
    db: Session = Depends(get_db)
):
    """
    ENDPOINT BUSCADOR MITIGADO:
    Utiliza bind parameters de SQLAlchemy con ILIKE.
    Cualquier intento de inyección (' OR '1'='1) se trata como un valor literal
    de búsqueda y no como código SQL ejecutable.
    """
    try:
        clean_param = f"%{criterio}%"
        stmt = (
            select(
                TgLote.id_lote,
                TgLote.cod_sector,
                TgLote.tipo_suelo,
                func.coalesce(TitularPredio.nombre_completo, 'Sin Titular').label("titular"),
                func.coalesce(TitularPredio.autovaluo_soles, 0).label("autovaluo"),
                gfunc.ST_AsGeoJSON(gfunc.ST_Transform(TgLote.objcad_lote_gemo, 4326)).label("geojson")
            )
            .outerjoin(TitularPredio, TgLote.id_lote == TitularPredio.id_lote)
            .where(
                or_(
                    TgLote.id_lote.ilike(clean_param),
                    TitularPredio.nombre_completo.ilike(clean_param)
                )
            )
            .limit(50)
        )
        rows = db.execute(stmt).fetchall()
        predios = [
            {
                "id_lote": str(r.id_lote),
                "cod_sector": str(r.cod_sector) if r.cod_sector else "",
                "tipo_suelo": str(r.tipo_suelo) if r.tipo_suelo else "",
                "titular": str(r.titular) if r.titular else "",
                "autovaluo": float(r.autovaluo) if r.autovaluo is not None else 0.0,
                "geojson": r.geojson
            }
            for r in rows
        ]
        return {
            "status": "success",
            "modo": "mitigated",
            "criterio": criterio,
            "total": len(predios),
            "query_debug": "SELECT l.id_lote, l.cod_sector, ... FROM tg_lote l LEFT JOIN catastro_titulares t WHERE l.id_lote ILIKE :clean_param OR t.nombre_completo ILIKE :clean_param LIMIT 50 [Bind params: :clean_param = '%" + criterio.replace("'", "\\'") + "%']",
            "predios": predios
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail="Error en la consulta segura de predios")

# =====================================================================
# MITIGACIÓN 2: Error-Based -> Validación de Esquema Geométrico con Shapely
# =====================================================================
class PoligonoInput(BaseModel):
    wkt_polygon: str = Field(..., max_length=5000, description="Geometría WKT sanitizada")

@router.get("/predios/poligono")
def render_predios_poligono_seguro_get(
    wkt_polygon: str = Query(..., max_length=5000, description="Geometría WKT sanitizada"),
    db: Session = Depends(get_db)
):
    """
    ENDPOINT MITIGADO 2 (GET):
    - Análisis topológico previo con Shapely en memoria de aplicación.
    - Se rechaza cualquier payload que no sea un POLYGON válido antes de tocar el motor SQL.
    - Se utiliza WKTElement parametrizado.
    """
    try:
        geom = shapely.wkt.loads(wkt_polygon)
        if not isinstance(geom, Polygon):
            raise HTTPException(status_code=422, detail="La geometría debe ser un POLYGON válido")
        if not geom.is_valid:
            raise HTTPException(status_code=422, detail="Topología geométrica corrupta o auto-intersecante")
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=422, detail="Formato WKT inválido o sintaxis no reconocible")

    try:
        geom_element = WKTElement(geom.wkt, srid=32719)
        stmt = (
            select(TgLote.id_lote)
            .where(gfunc.ST_Intersects(TgLote.objcad_lote_gemo, geom_element))
            .limit(20)
        )
        results = db.execute(stmt).scalars().all()
        return {
            "status": "success", 
            "count": len(results), 
            "rendered_features": results,
            "query_debug": "SELECT tg_lote.id_lote FROM tg_lote WHERE ST_Intersects(tg_lote.objcad_lote_gemo, ST_GeomFromEWKB(:geom_element)) LIMIT 20"
        }
    except Exception:
        raise HTTPException(status_code=500, detail="Error interno del servicio geoespacial")

@router.post("/predios/poligono")
def render_predios_poligono_seguro(
    payload: PoligonoInput,
    db: Session = Depends(get_db)
):
    """
    ENDPOINT MITIGADO 2 (POST):
    - Análisis topológico previo con Shapely en memoria de aplicación.
    - Se rechaza cualquier payload que no sea un POLYGON válido antes de tocar el motor SQL.
    - Se utiliza WKTElement parametrizado.
    """
    # 1. Validación estricta con Shapely
    try:
        geom = shapely.wkt.loads(payload.wkt_polygon)
        if not isinstance(geom, Polygon):
            raise HTTPException(status_code=422, detail="La geometría debe ser un POLYGON válido")
        if not geom.is_valid:
            raise HTTPException(status_code=422, detail="Topología geométrica corrupta o auto-intersecante")
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=422, detail="Formato WKT inválido o sintaxis no reconocible")

    # 2. Ejecución con bind variable GeoAlchemy2
    try:
        geom_element = WKTElement(geom.wkt, srid=32719)
        stmt = (
            select(TgLote.id_lote)
            .where(gfunc.ST_Intersects(TgLote.objcad_lote_gemo, geom_element))
            .limit(20)
        )
        results = db.execute(stmt).scalars().all()
        return {
            "status": "success", 
            "count": len(results), 
            "rendered_features": results,
            "query_debug": "SELECT tg_lote.id_lote FROM tg_lote WHERE ST_Intersects(tg_lote.objcad_lote_gemo, ST_GeomFromEWKB(:geom_element)) LIMIT 20"
        }
    except Exception:
        raise HTTPException(status_code=500, detail="Error interno del servicio geoespacial")

# =====================================================================
# MITIGACIÓN 3: Spatial DoS -> Parámetros Tipados y Bounded Execution
# =====================================================================
@router.get("/predios/analisis-expansion")
def analisis_expansion_seguro(
    buffer_metros: float = Query(..., gt=0, le=100.0, description="Distancia de buffer estrictamente acotada (máx 100m)"),
    cod_sector: str = Query("0101", regex=r"^\d{4}$", description="Sector catastral validado"),
    db: Session = Depends(get_db)
):
    """
    ENDPOINT MITIGADO 3:
    - Imposibilidad de inyectar 'quad_segs' u operaciones recursivas de buffer.
    - Restricción en tiempo de diseño del radio máximo computable para prevenir DoS.
    """
    try:
        stmt = (
            select(
                TgLote.id_lote,
                gfunc.ST_Area(gfunc.ST_Buffer(TgLote.objcad_lote_gemo, buffer_metros)).label("area_expandida")
            )
            .where(TgLote.cod_sector == cod_sector)
            .limit(50)
        )
        rows = db.execute(stmt).fetchall()
        return {
            "status": "completed",
            "resultados": [
                {"id_lote": r.id_lote, "area_buffer": float(r.area_expandida) if r.area_expandida else None} 
                for r in rows
            ],
            "query_debug": f"SELECT tg_lote.id_lote, ST_Area(ST_Buffer(tg_lote.objcad_lote_gemo, :buffer_metros)) FROM tg_lote WHERE tg_lote.cod_sector = :cod_sector LIMIT 50 [Bind: buffer={buffer_metros}, sector='{cod_sector}']"
        }
    except Exception:
        raise HTTPException(status_code=500, detail="Error en cálculo geométrico seguro")

# =====================================================================
# MITIGACIÓN 4: Ficha Catastral Segura -> ORM Parametrizado y Tipado Estricto
# =====================================================================
@router.post("/ficha/modificar")
def modificar_ficha_segura(
    id_lote: str = Query(..., regex=r"^21010101\d{6}$", description="Código catastral validado por patrón exacto"),
    nuevo_autovaluo: float = Query(..., gt=0, le=10000000.0, description="Monto numérico estrictamente acotado"),
    nuevo_titular: str = Query(..., min_length=3, max_length=100, regex=r"^[a-zA-ZáéíóúÁÉÍÓÚñÑ\s]+$", description="Solo caracteres alfabéticos"),
    db: Session = Depends(get_db)
):
    """
    ENDPOINT MITIGADO 4:
    - Validación de tipo y expresión regular que impide inyección de SQL.
    - Ejecución mediante ORM con bind parameters.
    """
    stmt = (
        update(TitularPredio)
        .where(TitularPredio.id_lote == id_lote)
        .values(autovaluo_soles=nuevo_autovaluo, nombre_completo=nuevo_titular)
    )
    res = db.execute(stmt)
    db.commit()
    if res.rowcount == 0:
        raise HTTPException(status_code=404, detail="Predio no encontrado")

    # Devolver registro actualizado seguro
    titular = db.execute(select(TitularPredio).where(TitularPredio.id_lote == id_lote)).scalar_one_or_none()
    return {
        "status": "success",
        "message": "Ficha actualizada de forma segura con ORM",
        "predio": {
            "id_lote": titular.id_lote,
            "titular": titular.nombre_completo,
            "autovaluo": float(titular.autovaluo_soles)
        }
    }

# =====================================================================
# MITIGACIÓN 5: Borrado Seguro -> Control de Acceso y Prepared Delete
# =====================================================================
@router.delete("/predios/borrar")
def borrar_predios_seguro(
    filtro_sector: str = Query(..., regex=r"^\d{4}$", description="Código de sector validado por regex"),
    db: Session = Depends(get_db)
):
    """
    ENDPOINT MITIGADO 5:
    - El filtro se valida estrictamente como 4 dígitos.
    - Se compila como parámetro bind: cualquier intento de ' OR '1'='1 es tratado como literal.
    """
    stmt = delete(TgLote).where(TgLote.cod_sector == filtro_sector)
    res = db.execute(stmt)
    db.commit()
    remaining = db.execute(select(func.count(TgLote.id_lote))).scalar()
    return {
        "status": "controlled_deletion",
        "lotes_eliminados": res.rowcount,
        "lotes_restantes": remaining,
        "message": f"Se eliminaron {res.rowcount} lotes del sector {filtro_sector}. Restan {remaining} lotes."
    }

# =====================================================================
# MITIGACIÓN 6: Autenticación Segura -> Hash Criptográfico y Prepared Statements
# =====================================================================
@router.post("/auth/login")
def login_visor_seguro(
    username: str = Query(..., min_length=3, max_length=50, regex=r"^[a-zA-Z0-9_]+$"),
    password: str = Query(...),
    db: Session = Depends(get_db)
):
    """
    ENDPOINT MITIGADO 6:
    - Validación alfanumérica de usuario (sin comillas ni operadores SQL).
    - Hashing seguro SHA-256 de la contraseña antes de la consulta.
    - Consulta con prepared statement en SQLAlchemy.
    """
    input_hash = hashlib.sha256(password.encode()).hexdigest()
    stmt = select(UsuarioSistema).where(
        and_(
            UsuarioSistema.username == username,
            UsuarioSistema.password_hash == input_hash
        )
    )
    user = db.execute(stmt).scalar_one_or_none()
    if user:
        return {
            "status": "authenticated",
            "message": "Autenticación segura exitosa",
            "usuario": {"id": user.id, "username": user.username, "role": user.role}
        }
    raise HTTPException(status_code=401, detail="Credenciales incorrectas")


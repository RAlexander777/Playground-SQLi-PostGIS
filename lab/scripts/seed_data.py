import json
import os
import sys
from shapely.geometry import Polygon
from sqlalchemy.orm import Session
from sqlalchemy import text
from geoalchemy2.shape import from_shape
from datetime import date
import hashlib

# Añadir directorio raíz al path para importar módulos
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.config.database import SessionLocal, engine, Base
from src.models.cadastre import TgLote, UsuarioSistema, TitularPredio

def seed_database():
    print("Inicializando estructura de base de datos...")
    with engine.connect() as conn:
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS postgis;"))
        conn.commit()
    Base.metadata.create_all(bind=engine)

    db: Session = SessionLocal()

    # 1. Poblar usuarios del sistema (Objetivo de la Simulación 2)
    print("Poblando usuarios y credenciales administrativas...")
    db.execute(text("TRUNCATE TABLE catastro_usuarios, catastro_titulares CASCADE;"))
    db.commit()

    admin_pass = hashlib.sha256("TokenCatastralSecreto2026".encode()).hexdigest()
    user_admin = UsuarioSistema(
        username="admin",
        password_hash=admin_pass,
        role="superadmin_catastro",
        email="admin.catastro@infraestructura.gob.pe"
    )
    user_operador = UsuarioSistema(
        username="operador1",
        password_hash=hashlib.sha256("OperadorPuno2026".encode()).hexdigest(),
        role="tecnico_gis",
        email="operador1@infraestructura.gob.pe"
    )
    db.add_all([user_admin, user_operador])
    db.commit()

    # 2. Cargar geometrías reales de Puno
    json_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "puno_raw_data.json")
    if not os.path.exists(json_path):
        print(f"Error: no se encontró {json_path}")
        return

    print(f"Leyendo archivo de polígonos catastrales reales: {json_path}...")
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    elements = data.get("elements", [])
    nodos = {e["id"]: (e["lon"], e["lat"]) for e in elements if e["type"] == "node"}
    vias = [e for e in elements if e["type"] == "way"]

    print("Limpiando tabla 'tg_lote'...")
    db.execute(text("TRUNCATE TABLE tg_lote CASCADE;"))
    db.commit()

    print(f"Procesando {len(vias)} polígonos potenciales...")
    lotes_insertados = 0
    titulares = []

    for idx, via in enumerate(vias):
        node_ids = via.get("nodes", [])
        if len(node_ids) < 3:
            continue

        coords = [nodos[n_id] for n_id in node_ids if n_id in nodos]
        if len(coords) < 3:
            continue
        if coords[0] != coords[-1]:
            coords.append(coords[0])

        try:
            poly_wgs84 = Polygon(coords)
            if not poly_wgs84.is_valid:
                continue

            # Crear WKT con SRID 4326 y transformar a UTM 19S (32719) en PostGIS
            geom_wkt = poly_wgs84.wkt
            id_lote = f"21010101{idx:06d}"
            sector = "0101" if idx % 2 == 0 else "0102"
            zonif = "RESIDENCIAL_R3" if idx % 3 == 0 else ("COMERCIAL_C2" if idx % 3 == 1 else "ZONA_PROTEGIDA_ZP")

            # Inserción con transformación de coordenadas
            sql_insert = text("""
                INSERT INTO tg_lote (id_lote, cod_sector, area_grafica, peri_grafico, tipo_suelo, fech_actua, objcad_lote_gemo)
                VALUES (
                    :id, 
                    :sector, 
                    ST_Area(ST_Transform(ST_SetSRID(ST_GeomFromText(:wkt), 4326), 32719)),
                    ST_Perimeter(ST_Transform(ST_SetSRID(ST_GeomFromText(:wkt), 4326), 32719)),
                    :tipo,
                    :fecha,
                    ST_Transform(ST_SetSRID(ST_GeomFromText(:wkt), 4326), 32719)
                )
            """)
            db.execute(sql_insert, {
                "id": id_lote,
                "sector": sector,
                "wkt": geom_wkt,
                "tipo": zonif,
                "fecha": date.today()
            })

            # Asociar titular con datos sensibles
            titulares.append(TitularPredio(
                id_lote=id_lote,
                dni_titular=f"{70000000 + idx:08d}",
                nombre_completo=f"Contribuyente Predial {idx}",
                autovaluo_soles=50000.0 + (idx * 150.0)
            ))

            lotes_insertados += 1
            if lotes_insertados >= 1500: # Tomamos una muestra de 1500 polígonos representativos para agilidad
                break
        except Exception:
            continue

    db.add_all(titulares)
    db.commit()
    db.close()
    print(f"¡Base de datos poblada exitosamente con {lotes_insertados} parcelas catastrales reales!")

if __name__ == "__main__":
    seed_database()

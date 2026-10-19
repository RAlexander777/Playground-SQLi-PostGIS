import argparse
import json
import os
import sys
import hashlib
from sqlalchemy.orm import Session
from sqlalchemy import text

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.config.database import SessionLocal, engine, Base
from src.models.cadastre import TgLote, UsuarioSistema, TitularPredio


def seed_database(target_parcels: int = 487, target_scale: int = None):
    if target_scale is not None:
        target_parcels = target_scale
    print(f"Initializing database schema and seeding target={target_parcels} real OSM parcels (Lima Metropolitana EPSG:32718)...")
    with engine.connect() as conn:
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS postgis;"))
        conn.commit()
    Base.metadata.create_all(bind=engine)

    db: Session = SessionLocal()

    db.execute(text("TRUNCATE TABLE catastro_usuarios, catastro_titulares, tg_lote CASCADE;"))
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
        password_hash=hashlib.sha256("OperadorLima2026".encode()).hexdigest(),
        role="tecnico_gis",
        email="operador1@infraestructura.gob.pe"
    )
    db.add_all([user_admin, user_operador])
    db.commit()

    data_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
    real_osm_path = os.path.join(data_dir, "lima_osm_real.json")
    if not os.path.exists(real_osm_path):
        real_osm_path = os.path.join(data_dir, "sur_peru_osm_real.json")

    if not os.path.exists(real_osm_path):
        raise FileNotFoundError(f"Real OSM dataset not found at {real_osm_path}. Run ingest_lima.py first.")

    with open(real_osm_path, "r", encoding="utf-8") as f:
        osm_payload = json.load(f)

    polygons = osm_payload.get("polygons", [])[:target_parcels]
    print(f"Loaded {len(polygons)} 100% real OpenStreetMap parcels from {real_osm_path}.")

    db.execute(text("DROP TABLE IF EXISTS _staging_osm_lotes;"))
    db.execute(text("""
        CREATE TEMP TABLE _staging_osm_lotes (
            row_idx INT,
            wkt TEXT
        );
    """))

    batch_size = 2500
    for start in range(0, len(polygons), batch_size):
        chunk = [
            {"idx": idx, "wkt": rec["wkt"]}
            for idx, rec in enumerate(polygons[start:start + batch_size], start=start)
        ]
        db.execute(
            text("INSERT INTO _staging_osm_lotes (row_idx, wkt) VALUES (:idx, :wkt)"),
            chunk
        )
    db.commit()

    db.execute(
        text("""
            WITH geom_transformed AS (
                SELECT
                    row_idx,
                    ST_Transform(ST_SetSRID(ST_GeomFromText(wkt), 4326), 32718) AS geom
                FROM _staging_osm_lotes
            )
            INSERT INTO tg_lote (id_lote, cod_sector, area_grafica, peri_grafico, tipo_suelo, fech_actua, objcad_lote_gemo)
            SELECT
                '150101' || LPAD(row_idx::text, 8, '0'),
                CASE WHEN (row_idx < 487 AND row_idx % 2 = 0) THEN '0101'
                     WHEN (row_idx < 487 AND row_idx % 2 = 1) THEN '0102'
                     ELSE LPAD((103 + (row_idx / 500))::text, 4, '0')
                END,
                ROUND(ST_Area(geom)::numeric, 2),
                ROUND(ST_Perimeter(geom)::numeric, 2),
                CASE WHEN row_idx % 3 = 0 THEN 'RESIDENCIAL_R3'
                     WHEN row_idx % 3 = 1 THEN 'COMERCIAL_C2'
                     ELSE 'ZONA_PROTEGIDA_ZP'
                END,
                CURRENT_DATE,
                geom
            FROM geom_transformed
            ORDER BY row_idx;
        """)
    )

    db.execute(text("""
        INSERT INTO catastro_titulares (id_lote, dni_titular, nombre_completo, autovaluo_soles)
        SELECT
            id_lote,
            LPAD((70000000 + ROW_NUMBER() OVER (ORDER BY id_lote))::text, 8, '0'),
            'Contribuyente Predial ' || (ROW_NUMBER() OVER (ORDER BY id_lote))::text,
            50000.0 + ((ROW_NUMBER() OVER (ORDER BY id_lote)) * 120.0)
        FROM tg_lote;
    """))

    db.execute(text("CREATE INDEX IF NOT EXISTS idx_lote_geom ON tg_lote USING GIST (objcad_lote_gemo);"))
    db.execute(text("CREATE INDEX IF NOT EXISTS idx_lote_sector ON tg_lote (cod_sector);"))
    db.execute(text("ANALYZE tg_lote;"))
    db.execute(text("ANALYZE catastro_titulares;"))
    db.commit()

    total_actual = db.execute(text("SELECT COUNT(*) FROM tg_lote;")).scalar()
    db.close()
    print(f"[OK] Seeded {total_actual} 100% real OpenStreetMap parcels in tg_lote (EPSG:32718) with GiST spatial index.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--scale", type=int, default=487, help="Number of real OSM parcels to seed (e.g., 487, 5000, 25000)")
    args = parser.parse_args()
    seed_database(args.scale)

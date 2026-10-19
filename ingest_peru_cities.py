import json
import os
import sys
import time
import requests
try:
    from shapely.geometry import Polygon
    HAS_SHAPELY = True
except ImportError:
    HAS_SHAPELY = False

# Mirrors oficiales de Overpass API para extracción cartográfica resiliente
OVERPASS_MIRRORS = [
    "https://overpass-api.de/api/interpreter",
    "https://z.overpass-api.de/api/interpreter",
    "https://lz4.overpass-api.de/api/interpreter",
    "https://overpass.kumi.systems/api/interpreter",
]

HEADERS = {
    "User-Agent": "PostGIS_Doctoral_Research_Lima/2.0 (74761925@epg.unap.edu.pe)",
    "Accept": "application/json",
}

# Trama catastral urbana contigua de Lima Metropolitana dentro del Huso UTM 18S (EPSG:32718)
# Coordenadas WGS84: (min_lat, min_lon, max_lat, max_lon)
CITIES = [
    ("Lima Centro Histórico - Plaza Mayor", (-12.065, -77.045, -12.035, -77.030)),
    ("Lima Centro Histórico - Barrios Altos", (-12.065, -77.030, -12.035, -77.015)),
    ("Lima Centro-Sur (Breña, Jesús María y Lince)", (-12.095, -77.055, -12.065, -77.025)),
    ("Lima Moderna (San Isidro y Miraflores)", (-12.125, -77.050, -12.095, -77.020)),
    ("Lima Este-Sur (La Victoria y San Borja)", (-12.095, -77.025, -12.065, -76.995)),
    ("Lima Norte (Rímac y San Martín de Porres)", (-12.035, -77.050, -12.005, -77.015)),
]


def consultar_overpass(query: str):
    """Consulta secuencialmente los mirrors de Overpass API hasta obtener HTTP 200."""
    for mirror in OVERPASS_MIRRORS:
        try:
            res = requests.post(mirror, data={"data": query}, headers=HEADERS, timeout=90)
            if res.status_code == 200:
                return res.json()
            print(f"   [!] Mirror {mirror} respondió HTTP {res.status_code}, probando siguiente...")
        except Exception as e:
            print(f"   [-] Error en {mirror}: {e}")
        time.sleep(2.0)
    return None


def extraer_poligonos_validos(elements, seen_way_ids):
    """Filtra y construye polígonos válidos 2D (ISO 19152 LA_SpatialUnit) sin duplicados."""
    nodos = {e["id"]: (e["lon"], e["lat"]) for e in elements if e.get("type") == "node"}
    vias = [e for e in elements if e.get("type") == "way"]
    valid_records = []

    for via in vias:
        way_id = via.get("id")
        if way_id in seen_way_ids:
            continue
        node_ids = via.get("nodes", [])
        if len(node_ids) < 3:
            continue
        coords = [nodos[nid] for nid in node_ids if nid in nodos]
        if len(coords) < 3:
            continue
        if coords[0] != coords[-1]:
            coords.append(coords[0])
        if len(coords) < 4:
            continue
        try:
            if HAS_SHAPELY:
                poly = Polygon(coords)
                if poly.is_valid and poly.is_simple and poly.area > 0:
                    seen_way_ids.add(way_id)
                    valid_records.append({
                        "osm_id": way_id,
                        "wkt": poly.wkt,
                        "n_vertices": len(poly.exterior.coords),
                    })
            else:
                area2 = sum(
                    coords[i][0] * coords[i + 1][1] - coords[i + 1][0] * coords[i][1]
                    for i in range(len(coords) - 1)
                )
                if abs(area2) > 1e-12:
                    wkt_pts = ", ".join(f"{lon} {lat}" for lon, lat in coords)
                    seen_way_ids.add(way_id)
                    valid_records.append({
                        "osm_id": way_id,
                        "wkt": f"POLYGON (({wkt_pts}))",
                        "n_vertices": len(coords),
                    })
        except Exception:
            continue
    return valid_records


def inyectar_ciudades_lima(target_max: int = 35000):
    print(f"=== INGESTA REAL OSM LIMA METROPOLITANA (EPSG:32718): {len(CITIES)} SECTORES URBANOS ===")
    print("Datos reales de OpenStreetMap (Centro Histórico, Breña, Jesús María, Lince, San Isidro, Miraflores).\n")

    base_dir = os.path.dirname(os.path.abspath(__file__))
    lab_data_dir = os.path.join(base_dir, "lab", "data")
    if not os.path.exists(lab_data_dir):
        lab_data_dir = os.path.join(os.path.dirname(base_dir), "data")
    os.makedirs(lab_data_dir, exist_ok=True)

    lima_file = os.path.join(lab_data_dir, "lima_osm_real.json")
    if os.path.exists(lima_file):
        with open(lima_file, "r", encoding="utf-8") as f:
            existing = json.load(f)
        if existing.get("total_polygons", 0) >= 25000:
            print(f"[OK] Dataset existente en {lima_file} con {existing['total_polygons']:,} polígonos reales.")
            return lima_file

    seen_way_ids = set()
    all_polygons = []
    city_counts = {}

    dq = '"'
    for idx, (name, bbox) in enumerate(CITIES):
        if len(all_polygons) >= target_max:
            break
        min_lat, min_lon, max_lat, max_lon = bbox
        print(f"\n[{idx+1}/{len(CITIES)}] Descargando {name} BBox={bbox}...")
        query = (
            f"[out:json][timeout:90];"
            f"(way[{dq}building{dq}]({min_lat},{min_lon},{max_lat},{max_lon}););"
            f"(._; >;);out body;"
        )
        data = consultar_overpass(query)
        if not data:
            print(f"   [!] No se pudo descargar {name}, continuando...")
            continue

        nuevos = extraer_poligonos_validos(data.get("elements", []), seen_way_ids)
        for rec in nuevos:
            rec["sector"] = name
        all_polygons.extend(nuevos)
        city_counts[name] = len(nuevos)
        print(f"   -> +{len(nuevos):,} parcelas válidas en {name} | Acumulado real: {len(all_polygons):,}")
        time.sleep(2.0)

    out_path = os.path.join(lab_data_dir, "lima_osm_real.json")
    payload = {
        "source": "OpenStreetMap Overpass API (Lima Metropolitana UTM Zone 18S / EPSG:32718)",
        "crs": "EPSG:32718 (UTM Zone 18S)",
        "region": "Lima Metropolitana, Peru",
        "total_polygons": len(all_polygons),
        "sectors": city_counts,
        "polygons": all_polygons,
    }
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False)

    print(f"\n=== INGESTA REAL FINALIZADA ===")
    print(f"Total de parcelas 100% reales guardadas en {out_path}: {len(all_polygons):,}")
    for c_name, c_cnt in city_counts.items():
        print(f"  - {c_name}: {c_cnt:,} parcelas")
    return out_path


if __name__ == "__main__":
    inyectar_ciudades_lima()

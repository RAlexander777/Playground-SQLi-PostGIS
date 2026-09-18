import requests
import json
import time
import os
import sys

# Definición de mirrors de Overpass API para alta disponibilidad y resiliencia
OVERPASS_MIRRORS = [
    "https://z.overpass-api.de/api/interpreter",
    "https://overpass-api.de/api/interpreter",
    "https://lz4.overpass-api.de/api/interpreter",
    "https://overpass.kumi.systems/api/interpreter"
]

# Sectores y cuadrantes urbanos representativos de la ciudad de Puno, Perú
# EPSG geográfico WGS84: Lat ~ -15.84, Lon ~ -70.02 (Lago Titicaca / Altiplano)
PUNO_ZONES = [
    ("Puno Centro Histórico y Plaza de Armas", (-15.845, -70.032, -15.837, -70.024)),
    ("Puno Bellavista y Eje Comercial",        (-15.840, -70.026, -15.832, -70.018)),
    ("Puno Huajsapata y San Antonio",         (-15.848, -70.038, -15.840, -70.029)),
    ("Puno Laykakota y Barrio Porteño",       (-15.845, -70.024, -15.836, -70.015)),
    ("Puno Muelle Lacustre y Malecón Titicaca",(-15.836, -70.020, -15.828, -70.012)),
    ("Puno Arco Deustua e Independencia",     (-15.838, -70.034, -15.830, -70.025)),
    ("Puno Yanamayo y Bellavista Alta",       (-15.828, -70.040, -15.815, -70.020)),
    ("Puno Salcedo y Chanu Chanu",            (-15.865, -70.035, -15.848, -70.010)),
    ("Puno Chejoña y Jayllihuaya",            (-15.890, -70.030, -15.865, -69.995)),
    ("Puno Alto Puno y Ciudad de la Paz",     (-15.830, -70.065, -15.805, -70.035)),
    ("Puno Vallecito y Azoguini",             (-15.845, -70.055, -15.830, -70.035)),
    ("Puno Cancharani y Santa Rosa",          (-15.860, -70.055, -15.845, -70.035))
]

HEADERS = {
    'User-Agent': 'PostGIS_Doctoral_Research_Puno/2.0 (becerra@investigacion.edu.pe)',
    'Accept': 'application/json'
}

def consultar_overpass(query):
    """Prueba secuencialmente los mirrors disponibles hasta obtener respuesta exitosa."""
    for mirror in OVERPASS_MIRRORS:
        try:
            print(f"   [+] Consultando mirror: {mirror}...")
            res = requests.post(mirror, data={'data': query}, headers=HEADERS, timeout=45)
            if res.status_code == 200:
                return res.json()
            elif res.status_code == 429:
                print(f"   [!] Mirror saturado (HTTP 429), probando alternativa...")
            else:
                print(f"   [!] Mirror respondió HTTP {res.status_code}")
        except Exception as e:
            print(f"   [-] Fallo de conexión en {mirror}: {e}")
        time.sleep(1)
    return None

def descargar_catastro_puno(target_buildings=1500):
    print("==========================================================================")
    print("INGESTA CARTOGRÁFICA REAL: CIUDAD DE PUNO, PERÚ (ISO 19152 LADM)")
    print("==========================================================================")
    print(f"Objetivo: Extraer muestra geoespacial auténtica de Puno (~{target_buildings} parcelas)...\n")

    todos_nodos = {}
    todas_vias = {}

    for idx, (zona_nombre, bbox) in enumerate(PUNO_ZONES):
        min_lat, min_lon, max_lat, max_lon = bbox
        print(f"[{idx+1}/{len(PUNO_ZONES)}] Extrayendo: {zona_nombre}")
        print(f"    Coordenadas: Lat [{min_lat}, {max_lat}] | Lon [{min_lon}, {max_lon}]")

        query = f"""
        [out:json][timeout:60];
        (
          way["building"]({min_lat},{min_lon},{max_lat},{max_lon});
        );
        (._; >;);
        out body;
        """

        data = consultar_overpass(query)
        if not data:
            print(f"    [!] No se pudieron obtener datos para {zona_nombre}. Continuando...")
            continue

        elements = data.get("elements", [])
        nodos_zona = {e["id"]: e for e in elements if e.get("type") == "node"}
        vias_zona = [e for e in elements if e.get("type") == "way"]

        todos_nodos.update(nodos_zona)
        for v in vias_zona:
            todas_vias[v["id"]] = v

        print(f"    -> Vías/Lotes acumulados: {len(todas_vias)} | Vértices/Nodos: {len(todos_nodos)}")
        
        if len(todas_vias) >= target_buildings:
            print(f"\n[***] Muestra objetivo alcanzada: {len(todas_vias)} parcelas catastrales reales.")
            break
        time.sleep(2)

    # Consolidar formato raw OSM idéntico a la estructura requerida por el laboratorio
    elementos_finales = list(todos_nodos.values()) + list(todas_vias.values())
    resultado_json = {
        "version": 0.6,
        "generator": "Overpass API Puno Extractor Doctoral",
        "osm3s": {
            "timestamp_osm_base": time.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "copyright": "© OpenStreetMap contributors"
        },
        "elements": elementos_finales
    }

    # Determinar ruta destino en data/puno_raw_data.json
    script_dir = os.path.dirname(os.path.abspath(__file__))
    base_dir = os.path.dirname(script_dir)
    dest_path = os.path.join(base_dir, "data", "puno_raw_data.json")

    print(f"\nGuardando datos auténticos de Puno en: {dest_path}...")
    os.makedirs(os.path.dirname(dest_path), exist_ok=True)
    with open(dest_path, "w", encoding="utf-8") as f:
        json.dump(resultado_json, f, ensure_ascii=False)

    print(f"✅ ¡Ingesta exitosa! Archivo generado con {len(elementos_finales):,} elementos de Puno, Perú.")
    return dest_path

if __name__ == "__main__":
    descargar_catastro_puno()

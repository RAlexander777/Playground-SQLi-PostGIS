# Laboratorio Experimental: Inyección SQL Espacial en PostGIS y Sistemas Catastrales

Entorno experimental dockerizado para la investigación doctoral:
**"Evaluación de vulnerabilidades de Inyección SQL Espacial en Sistemas de Información Catastral basados en PostGIS"**

---

## 1. Arquitectura del Laboratorio

* **Motor Espacial:** `PostgreSQL 15` con extensión `PostGIS 3.3` (Puerto host: `5488`).
* **Capa de Servicios Web:** `FastAPI` (Python 3.11) con Uvicorn (Puerto host: `8020`).
* **Capa ORM y Geometría:** `SQLAlchemy 2.0`, `GeoAlchemy2` y `Shapely 2.0`.
* **Guardia Defensiva:** SCIG (*Spatial Cost and Invariant Guard*) implementada en `src/security/spatial_guard.py`.
* **Dataset Catastral:** Muestra continua de parcelas urbanas de OpenStreetMap de **Lima Metropolitana (Perú)** proyectadas a `EPSG:32718` (WGS 84 / UTM Zona 18 Sur) estructuradas bajo el estándar ISO 19152 (LADM) en tres escalas ($N = 487$, $5{,}000$ y $25{,}000$).

---

## 2. Puesta en Marcha Rápida

### Paso 1: Levantar los contenedores Docker
```bash
cd lab
docker-compose up -d --build
```
Verificar que los contenedores estén saludables:
```bash
docker ps
```

### Paso 2: Poblar la Base de Datos con Parcelas Reales
Desde el host (o dentro del contenedor `catastro_sqli_api`):
```bash
# Escala base: 487 lotes de Lima Centro Histórico
python scripts/seed_data.py --scale 487

# Opcional: Escalas expandidas para pruebas de estrés
python scripts/seed_data.py --scale 5000
python scripts/seed_data.py --scale 25000
```
*Esto inicializa la extensión PostGIS, las tablas del esquema catastral (`tg_lote`, `catastro_usuarios`, `catastro_titulares`), construye el índice espacial GiST y ejecuta `ANALYZE`.*

### Paso 3: Abrir el Playground
Acceder a `http://localhost:8020/` desde el navegador web.

---

## 3. Ejecución de las Simulaciones de Ataque

### Vector 1: Confusión CRS y Evasión ST_DWithin
```bash
python scripts/exploit_1_bypass.py
```

### Vector 4: Fraude en Ficha Catastral (Tampering UPDATE)
```bash
python scripts/exploit_4_tampering.py
```

### Vector 5: Purga Masiva (Tautología DELETE)
```bash
python scripts/exploit_5_destructive_drop.py
```

### Vector 6: Bypass de Autenticación
```bash
python scripts/exploit_6_auth_bypass.py
```

---

## 4. Benchmarking y Comparativa de Rendimiento

Para ejecutar la batería completa de evaluación doctoral con $R = 30$ repeticiones y generar las figuras estadísticas de publicación:
```bash
cd ..
python run_doctoral_experiments.py
```

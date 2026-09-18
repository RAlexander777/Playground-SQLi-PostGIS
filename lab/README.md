# Laboratorio Experimental: Inyección SQL Espacial en PostGIS y Sistemas Catastrales

Entorno experimental dockerizado para la investigación doctoral:
**"Evaluación de vulnerabilidades de Inyección SQL Espacial en Sistemas de Información Catastral basados en PostGIS"**

---

## 1. Arquitectura del Laboratorio

* **Motor Espacial:** `PostgreSQL 15` con extensión `PostGIS 3.3` (Puerto host: `5488`).
* **Capa de Servicios Web:** `FastAPI` (Python 3.11) con Uvicorn (Puerto host: `8020`).
* **Capa ORM y Geometría:** `SQLAlchemy 2.0`, `GeoAlchemy2` y `Shapely 2.0`.
* **Dataset Catastral:** Parcelas reales del catastro urbano de Puno (Perú) proyectadas a `EPSG:32719` (WGS 84 / UTM Zona 19 Sur) conforme al estándar ISO 19152 (LADM).

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
python scripts/seed_data.py
```
*Esto creará la extensión PostGIS, las tablas del esquema catastral (`tg_lote`, `catastro_usuarios`, `catastro_titulares`) y cargará la muestra representativa de parcelas reales.*

---

## 3. Ejecución de las Simulaciones de Ataque

### Simulación 1: Evasión de Límite Espacial (Spatial Logic Bypass)
Demuestra cómo romper el aislamiento multi-tenant y de sector catastral mediante la manipulación de la distancia en `ST_DWithin`:
```bash
python scripts/exploit_1_bypass.py
```

### Simulación 2: Inferencia de Datos por Errores Espaciales (Error-Based Spatial SQLi)
Demuestra la reconstrucción ciega de credenciales administrativas mediante excepciones condicionales en el motor GEOS/PostGIS (`ST_GeomFromText` con topología inválida):
```bash
python scripts/exploit_2_error_spatial.py
```

### Simulación 3: Denegación de Servicio Espacial (Spatial DoS)
Demuestra la inducción de sobrecarga algorítmica ($O(N^2)$) saturando los subprocesos de PostgreSQL mediante el parámetro de cuadrantes en `ST_Buffer`:
```bash
python scripts/exploit_3_dos.py
```

---

## 4. Benchmarking y Comparativa de Rendimiento

Para generar la tabla estadística de latencia (media, p50, p95, p99) y throughput requerida para la sección de Resultados y Discusión del paper:
```bash
python scripts/run_benchmarks.py
```

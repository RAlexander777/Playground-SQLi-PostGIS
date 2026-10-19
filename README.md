# Playground SQLi PostGIS

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![PostgreSQL 15](https://img.shields.io/badge/PostgreSQL-15-336791.svg?logo=postgresql&logoColor=white)](https://www.postgresql.org/)
[![PostGIS 3.3](https://img.shields.io/badge/PostGIS-3.3-green.svg)](https://postgis.net/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-009688.svg?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![ISO 19152 LADM](https://img.shields.io/badge/Standard-ISO%2019152%20LADM-orange.svg)](https://www.iso.org/standard/51206.html)

Interactive laboratory and experimental testbed accompanying the scientific research paper:
> **"Experimental Evaluation of Spatial SQL Injection Vulnerabilities in PostGIS-Based Cadastral Information Systems"**

This repository provides an interactive web playground, reproducible benchmark scripts, and an end-to-end containerized environment (PostgreSQL 15 + PostGIS 3.3 + FastAPI + Leaflet) to simulate, evaluate, and mitigate spatial SQL injection vulnerabilities across the CIA triad (Confidentiality, Integrity, and Availability).

---

## Architecture Overview

The testbed models real-world urban cadastral workflows using contiguous OpenStreetMap parcel cartography from **Lima Metropolitana (Peru)**, projected in `EPSG:32718` (WGS 84 / UTM Zone 18S) across three benchmark scales ($N = 487$ baseline urban core, $N = 5{,}000$ district scale, and $N = 25{,}000$ metropolitan scale) and structured under the **ISO 19152 Land Administration Domain Model (LADM)**:
* `tg_lote`: Spatial unit persistence (`LA_SpatialUnit`, `objcad_lote_gemo`).
* `catastro_titulares`: Fiscal valuation, property codes, and owner records (`LA_Party`).
* `catastro_usuarios`: Role-based authentication and operational credentials.

```
                  ┌─────────────────────────────────────────────────────────┐
                  │                 Playground Web Interface                │
                  │        (Leaflet + Bilingual ES/EN + Real-time AST)      │
                  └───────────────────────────┬─────────────────────────────┘
                                              │ HTTP Requests
                                              ▼
┌───────────────────────────────────────────────────────────────────────────────────────────┐
│ FastAPI Application (Dual-Engine: Vulnerable vs. Mitigated)                               │
│                                                                                           │
│  [Vulnerable Path]                     [SCIG Defense Pipeline (3 Spatial Barriers)]       │
│  • Dynamic SQL concatenation            1. CRS Pinning (EPSG:32718) & MBR Quota           │
│  • Direct AST injection surface            (Area(MBR) <= 25 ha, float bounds).            │
│  • Unrestricted topological calls       2. DE-9IM Invariant & Cost Guard (Shapely)        │
│                                            (Polygon only, is_valid, C_geom <= 5000).      │
│                                         3. GeoAlchemy2 EWKB Parameterization              │
│                                            (Prepared statements, timeout = 250ms).        │
└─────────────────────────────────────────────┬─────────────────────────────────────────────┘
                                              │ Clean EWKB SQL / Prepared Statements
                                              ▼
                  ┌─────────────────────────────────────────────────────────┐
                  │          PostgreSQL 15 + PostGIS 3.3 (Docker)           │
                  │       Port: 5488 | Dataset: N = 487 / 5,000 / 25,000    │
                  └─────────────────────────────────────────────────────────┘
```

---

## Six Evaluated Spatial Attack Vectors

| # | Spatial Vector | Evaluated Endpoint | Representative Payload | CIA Triad & Practical Impact |
|:-:|:---|:---|:---|:---|
| **V1** | **CRS / SRID Confusion & Proximity Bypass** | `GET /predios/radio` | `srid=4326, distancia=0.5` or `50) OR 1=1 --` | **Confidentiality:** Angular degree expansion ($\approx 55.6$~km) or proximity predicate cancellation, exfiltrating all parcels. |
| **V2** | **MBR & GiST Index Poisoning** | `GET /predios/bbox` | `LINESTRING(270000 8660000, 290000 8680000)` into `&&` | **Confidentiality:** Zero-area 1D diagonal forces full $400\text{ km}^2$ MBR scan across GiST index, dumping entire cadastre. |
| **V3** | **GEOS/PROJ Error-Based Side-Channel** | `GET /predios/poligono` | Conditional unclosed `LinearRing` exception oracle | **Confidentiality:** Blind side-channel inferring administrative credentials byte-by-byte via HTTP 500 differential errors. |
| **V4** | **Algorithmic Buffer DoS $\mathcal{O}(V^2)$** | `GET /predios/analisis-expansion` | `ST_Buffer(..., quad_segs=192)` + `ST_Intersection` | **Availability:** Quadratic complexity explosion ($345{,}600$ pairwise vertices); locks PostgreSQL worker threads. |
| **V5** | **Type Coercion & DE-9IM Bypass** | `POST /ficha/geometria` | `GEOMETRYCOLLECTION(POINT(...), POLYGON(...))` | **Integrity:** Point anchor satisfies `ST_Intersects` while coercing dimensions or injecting unauthorized exterior parcel areas. |
| **V6** | **Topological Grid-Snap Collapse** | `POST /predios/depurar-topologia` | `ST_SnapToGrid(geom, tolerancia=5000.0)` | **Integrity & Availability:** Coarse $5{,}000$~m grid snaps all vertices to a single point node with area $0.0\text{ m}^2$. |

### Relational Attacks & Custom SQL Console
The playground also provides:
* **Classic DML / Auth Testing:** Cadastral record tampering (`UPDATE` autovalúo to 0), full table purges (`DELETE` tautology), and login bypass (`admin' --`).
* **Real-time Query Concatenation Inspector:** Displays dynamically how user inputs escape string quotes in vulnerable f-strings vs. how they are bound as safe binary parameters in ORM mode.
* **In-Browser Interactive SQL Console:** Allows executing arbitrary custom spatial SQL queries and observing latency, HTTP status, and defensive pipeline behavior in real time.

---

## Quick Start & Replication Guide

### Prerequisites
* [Docker Desktop](https://www.docker.com/products/docker-desktop/) (Docker Compose v2+)
* [Python 3.11+](https://www.python.org/downloads/)
* Modern web browser (Chrome, Firefox, Edge)

### 1. Clone the Repository
```bash
git clone https://github.com/RAlexander777/Playground-SQLi-PostGIS.git
cd Playground-SQLi-PostGIS
```

### 2. Launch the Environment with Docker Compose
```bash
cd lab
docker-compose up -d --build
```
This spins up:
* **PostGIS Database:** `localhost:5488`
* **FastAPI Backend:** `localhost:8020` (Swagger UI at `http://localhost:8020/docs`)
* **Interactive Web Playground:** `http://localhost:8020/`

### 3. Seed Cadastral Sample Data
From the `lab/` directory, seed the database with real OpenStreetMap parcels from Lima Metropolitana:
```bash
# Baseline scale (N = 487 parcels, Lima Centro Histórico)
python scripts/seed_data.py --scale 487

# Or scale up to district (5,000) or metropolitan (25,000) dataset:
python scripts/seed_data.py --scale 5000
python scripts/seed_data.py --scale 25000
```
*(Or inside the API container: `docker exec -it catastro_sqli_api python scripts/seed_data.py --scale 487`)*

---

## Reproducing Paper Benchmarks

The repository includes the automated replication harness used in the paper:

```bash
# Return to repository root
cd ..

# Install benchmarking dependencies
pip install requests matplotlib numpy

# Run the experimental suite (Concurrency curves, Spatial DoS, Pipeline diagram, Multi-scale evaluation)
python run_doctoral_experiments.py
```

Generated publication figures are saved directly to `figures/`:
* `fig1_defense_pipeline.png`: Architecture diagram of the 3-barrier SCIG + ORM defense pipeline.
* `fig2_concurrency_latency.png`: Latency percentiles ($p_{50}$ and $p_{99}$) and multi-scale dataset scalability ($N = 487$, $5{,}000$, and $25{,}000$).
* `fig3_spatial_dos_complexity.png`: Quadratic execution curve of the geometric buffer-overlay DoS vs. SCIG cost cutoff ($\tau_{\max} = 5{,}000$).

---

## Repository Structure

```
.
├── figures/                          # Publication figures (High-DPI PNGs)
│   ├── fig1_defense_pipeline.png
│   ├── fig2_concurrency_latency.png
│   └── fig3_spatial_dos_complexity.png
├── lab/                              # Dockerized playground & microservices
│   ├── data/                         # Real OpenStreetMap Lima GeoJSON datasets
│   │   └── lima_osm_real.json
│   ├── scripts/                      # Attack scripts, ingestion & seed harness
│   │   ├── exploit_1_bypass.py
│   │   ├── exploit_2_error_spatial.py
│   │   ├── exploit_3_dos.py
│   │   ├── exploit_4_tampering.py
│   │   ├── exploit_5_destructive_drop.py
│   │   ├── exploit_6_auth_bypass.py
│   │   ├── ingest_peru_cities.py
│   │   └── seed_data.py
│   ├── src/
│   │   ├── api/                      # Vulnerable, mitigated, and admin routes
│   │   │   ├── admin.py
│   │   │   ├── mitigated.py
│   │   │   └── vulnerable.py
│   │   ├── config/                   # Database engine & connection settings
│   │   ├── models/                   # SQLAlchemy & GeoAlchemy2 models
│   │   ├── security/                 # Spatial Cost and Invariant Guard (SCIG)
│   │   │   └── spatial_guard.py
│   │   └── web/                      # Interactive Bilingual Playground
│   │       └── index.html
│   ├── docker-compose.yml
│   └── Dockerfile
├── run_doctoral_experiments.py       # Full doctoral benchmark runner
├── LICENSE                           # MIT License
└── README.md                         # Repository documentation
```

---

## Scientific Citation

If you use this playground, dataset, or architectural defense in your research, please cite:

**This paper may be cited as:**

> Becerra-Lucano, R. A., & Ibarra-Cabrera, M. J. (2026). Experimental Evaluation of Spatial SQL Injection Vulnerabilities in PostGIS-Based Cadastral Information Systems. *Preprint / Under Review*.

### BibTeX

```bibtex
@article{becerra2026spatial_sqli,
  title={Experimental Evaluation of Spatial SQL Injection Vulnerabilities in PostGIS-Based Cadastral Information Systems},
  author={Becerra-Lucano, Rodrigo Alexander and Ibarra-Cabrera, Manuel Jesus},
  journal={Journal of Cybersecurity and Privacy},
  note={Under review},
  year={2026}
}
```

---

## License

This project is licensed under the **MIT License** - see the [LICENSE](LICENSE) file for details.

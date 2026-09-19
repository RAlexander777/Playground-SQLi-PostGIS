# Playground SQLi PostGIS

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![PostgreSQL 15](https://img.shields.io/badge/PostgreSQL-15-336791.svg?logo=postgresql&logoColor=white)](https://www.postgresql.org/)
[![PostGIS 3.3](https://img.shields.io/badge/PostGIS-3.3-green.svg)](https://postgis.net/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-009688.svg?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![ISO 19152 LADM](https://img.shields.io/badge/Standard-ISO%2019152%20LADM-orange.svg)](https://www.iso.org/standard/51206.html)

Interactive laboratory and experimental testbed accompanying the scientific research paper:
> **"Evaluación de Vulnerabilidades de Inyección SQL Espacial en Sistemas de Información Catastral basados en PostGIS"** / **"Spatial SQL Injection Vulnerability Assessment in PostGIS-Based Cadastral Information Systems"**

This repository provides an interactive web playground, reproducible benchmark scripts, and an end-to-end containerized environment (PostgreSQL 15 + PostGIS 3.3 + FastAPI + Leaflet) to simulate, evaluate, and mitigate spatial SQL injection vulnerabilities across the CIA triad (Confidentiality, Integrity, and Availability).

---

## Architecture Overview

The testbed models real-world urban cadastral workflows using **487 official parcel polygons** from the city of Puno (Peru), projected in `EPSG:32719` (WGS 84 / UTM Zone 19S) and structured under the **ISO 19152 Land Administration Domain Model (LADM)**:
* `tg_lote`: Spatial unit persistence (`LA_SpatialUnit`).
* `catastro_titulares`: Fiscal valuation, property codes, and owner records (`LA_Party`).
* `catastro_usuarios`: Role-based authentication and operational credentials.

```
                  ┌─────────────────────────────────────────────────────────┐
                  │                 Playground Web Interface                │
                  │         (OpenStreetMap + Leaflet + Real-time AST)       │
                  └───────────────────────────┬─────────────────────────────┘
                                              │ HTTP Requests
                                              ▼
┌───────────────────────────────────────────────────────────────────────────────────────────┐
│ FastAPI Application (Dual-Engine: Vulnerable vs. Mitigated)                               │
│                                                                                           │
│  [Vulnerable Path]                     [Mitigated Defense Pipeline (3 Barriers)]         │
│  • Dynamic SQL concatenation            1. Pydantic: Strict typing, bounding limits &     │
│  • Direct AST injection surface            regex guards.                                  │
│  • Unrestricted topological calls       2. Shapely: In-memory AST topological validation  │
│                                            (rejects self-intersections & invalid WKT).    │
│                                         3. GeoAlchemy2 / SQLAlchemy: Parametric binary    │
│                                            compilation (EWKB bind variables).             │
└─────────────────────────────────────────────┬─────────────────────────────────────────────┘
                                              │ Clean SQL / Prepared Statements
                                              ▼
                  ┌─────────────────────────────────────────────────────────┐
                  │          PostgreSQL 15 + PostGIS 3.3 (Docker)           │
                  │         Port: 5488  |  Dataset: 487 LADM Parcels         │
                  └─────────────────────────────────────────────────────────┘
```

---

## Six Evaluated Attack Vectors

| # | Vector | Evaluated Endpoint | Payload Mechanism | CIA Triad & Practical Impact |
|:-:|:---|:---|:---|:---|
| **V1** | **Spatial Logic Bypass** | `GET /predios/radio` | `50) OR 1=1 --` | **Confidentiality:** Cancels radius distance and sector isolation; exfiltrates all parcels across restricted zones. |
| **V2** | **Error-Based Spatial SQLi** | `GET /predios/poligono` | Geometric error trigger in `CASE WHEN ... THEN CAST(ST_GeomFromText('ERR') AS INT)` | **Confidentiality:** Blind side-channel oracle exfiltrating password hashes character by character via HTTP 500. |
| **V3** | **Spatial Algorithmic DoS** | `GET /predios/analisis-expansion` | `10 + (SELECT COUNT(*) FROM tg_lote a CROSS JOIN tg_lote b ... ST_Buffer(..., 100))` | **Availability:** Quadratic complexity explosion ($O(N^2)$); saturates CPU in GEOS. |
| **V4** | **Cadastral Tampering** | `POST /ficha/modificar` | Multi-statement or parameter tampering (`nuevo_autovaluo = 0`) | **Integrity:** Modifies fiscal property valuations and transfers lot ownership illicitly. |
| **V5** | **Bulk Data Destruction** | `DELETE /predios/borrar` | Tautology injection: `filtro_sector = '0101' OR '1'='1'` | **Integrity & Availability:** Unconditional deletion of all 487 cadastral parcels from PostGIS. |
| **V6** | **Authentication Bypass** | `POST /auth/login` | Comment injection: `username = admin' --` | **Confidentiality & Integrity:** Bypasses password verification; elevates privileges to `superadmin_catastro`. |

---

## Quick Start & Replication Guide

### Prerequisites
* [Docker Desktop](https://www.docker.com/products/docker-desktop/) (Docker Compose v2+)
* [Python 3.11+](https://www.python.org/downloads/) (for running benchmark and replication scripts)
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

### 3. Seed Cadastral Sample Data
From the `lab/` directory, seed the database with the 487 real LADM parcels from Puno:
```bash
python scripts/seed_data.py
```
*(Or inside the API container: `docker exec -it catastro_sqli_api python scripts/seed_data.py`)*

### 4. Open the Playground
Open `lab/src/web/index.html` directly in your browser or serve it with any local static HTTP server:
```bash
# Optional: serve web interface locally
cd src/web
python -m http.server 3000
```
Navigate to `http://localhost:3000` (or double click `lab/src/web/index.html`).

---

## Reproducing Paper Benchmarks

The repository includes the exact automated replication harness used in the paper:

```bash
# Return to repository root
cd ..

# Install benchmarking dependencies
pip install requests matplotlib numpy

# Run the experimental suite (Concurrency curves, Spatial DoS, Pipeline diagram)
python run_doctoral_experiments.py
```

Generated publication figures are saved directly to `figures/`:
* `fig1_defense_pipeline.png`: Architecture diagram of the 3-barrier defense pipeline.
* `fig2_concurrency_latency.png`: Throughput and latency percentiles ($p_{50}$ and $p_{99}$) across 1–100 concurrent clients.
* `fig3_spatial_dos_complexity.png`: Quadratic execution curve of the geometric Cartesian product.

---

## Repository Structure

```
.
├── figures/                          # Publication figures (High-DPI PNGs)
│   ├── fig1_defense_pipeline.png
│   ├── fig2_concurrency_latency.png
│   └── fig3_spatial_dos_complexity.png
├── lab/                              # Dockerized playground & microservices
│   ├── data/                         # OpenStreetMap raw Puno GeoJSON/JSON
│   ├── scripts/                      # Standalone exploit and ingestion scripts
│   │   ├── exploit_1_bypass.py
│   │   ├── exploit_2_error_spatial.py
│   │   ├── exploit_3_dos.py
│   │   ├── exploit_4_tampering.py
│   │   ├── exploit_5_destructive_drop.py
│   │   ├── exploit_6_auth_bypass.py
│   │   └── seed_data.py
│   ├── src/
│   │   ├── api/                      # Vulnerable, mitigated, and admin routes
│   │   │   ├── admin.py
│   │   │   ├── mitigated.py
│   │   │   └── vulnerable.py
│   │   ├── config/                   # Database engine & connection settings
│   │   ├── models/                   # SQLAlchemy & GeoAlchemy2 models
│   │   └── web/                      # Interactive Single-Page Playground
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

> Becerra-Lucano, R. A., & Ibarra-Cabrera, M. J. (2026). Evaluation of Spatial SQL Injection Vulnerabilities in PostGIS-Based Cadastral Information Systems. *International Multidisciplinary Journal of Emerging Technologies and Applications*, 1(1), 1-8. https://imjeta.org/index.php/IMJETA/libraryFiles/downloadPublic/1

### BibTeX

```bibtex
@article{becerra2026evaluation,
  title={Evaluation of Spatial SQL Injection Vulnerabilities in PostGIS-Based Cadastral Information Systems},
  author={Becerra-Lucano, Rodrigo Alexander and Ibarra-Cabrera, Manuel Jesus},
  journal={International Multidisciplinary Journal of Emerging Technologies and Applications (IMJETA)},
  volume={1},
  number={1},
  pages={1--8},
  year={2026},
  url={https://imjeta.org/index.php/IMJETA/libraryFiles/downloadPublic/1}
}
```

---

## License

This project is licensed under the **MIT License** - see the [LICENSE](LICENSE) file for details.

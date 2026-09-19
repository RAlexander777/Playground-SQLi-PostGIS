# Technical Guide and Support Sheet: Playground Architecture and Operation

**Project:** *Interactive Research Playground: Spatial SQL Injection in PostGIS*  
**Author:** Rodrigo Alexander Becerra Lucano  
**Official Repository:** `RAlexander777/Playground-SQLi-PostGIS`  
**Objective:** Provide rigorous technical and conceptual explanations of every module, button, panel, endpoint, and data flow of the interactive lab for a live doctoral defense or presentation.

---

## 1. Playground Purpose and Overall Architecture

The Playground is an interactive cybersecurity web application designed as a **reproducible experimental testbed**. It enables real-time visual comparison, on the exact same cadastral map, between a vulnerable API and a defense-in-depth mitigated API compliant with the international **ISO 19152 (LADM)** standard.

### Technology Stack:
* **Spatial Database:** PostgreSQL 15 with PostGIS 3.3 extension.
* **Backend:** Python 3.11 with the **FastAPI** asynchronous framework and **Uvicorn** ASGI server.
* **ORM & Persistence:** SQLAlchemy 2.0 and **GeoAlchemy2** (spatial type handler and EWKB binary serializer).
* **Software Validation:** **Pydantic v2** (HTTP validation layer) and **Shapely** (in-memory topological validation powered by the GEOS engine).
* **Frontend:** HTML5, Bootstrap 5, CSS3, and **Leaflet.js** over OpenStreetMap base cartography.

---

## 2. Component-by-Component Breakdown

```
+---------------------------------------------------------------------------------------------------+
| 1. TOP BAR: DB Status | Parcel/Owner Counts | Reset DB | Vuln/Mitigated Mode | Language (ES/EN)   |
+---------------------------------------------------------------------------------------------------+
| 2. MANUAL QUERY: Search Criterion Input | Evaluate Button | Quick Presets (Tautology, UNION, etc.)|
+---------------------------------------------------------------------------------------------------+
| 3. DEFENSIVE PIPELINE: Barrier 1 (Pydantic) ---> Barrier 2 (Shapely) ---> Barrier 3 (GeoAlchemy2) |
+----------------------------------------------------+----------------------------------------------+
| 4. CARTOGRAPHIC VIEWER (Leaflet / EPSG:32719)      | 6. ATTACK VECTOR SUITE (V1 to V6)            |
|    - Blue Polygons: Authorized parcels             |    - V1: Spatial Logic Bypass (ST_DWithin)   |
|    - Red Polygons: Exfiltrated/affected parcels    |    - V2: Error-Based Side Channel (Oracle)   |
|                                                    |    - V3: Spatial DoS (Buffer O(N²))          |
+----------------------------------------------------+    - V4: Cadastral Record Tampering (Fraud)  |
| 5. SQL INSPECTOR & REAL-TIME DIAGNOSTICS           |    - V5: Cartographic Purge (WHERE 1=1)      |
|    - Monospace Terminal: Raw vs Parameterized SQL  |    - V6: Auth Bypass (admin' --)             |
|    - Metrics: Latency (ms) | HTTP Status | Barrier +----------------------------------------------+
|    - Pedagogical diagnostic summary of flow        | 7. LADM CADASTRAL INTEGRITY (Live Table)     |
|                                                    |    - Parcel ID | DNI | Owner | Valuation S/  |
+----------------------------------------------------+----------------------------------------------+
```

---

### Component 1: Top Bar and Global Controls (Header)

* **Status Indicator & Record Counters (`Parcels: 487 | Owners: 487`):**
  * Continuously polls the health of the PostgreSQL/PostGIS database service.
  * Displays the active count of parcels in `tg_lote` and taxable persons in `catastro_titulares`.
  * *Key point for defense:* When the cartographic purge attack (V5) executes, this counter drops to `0`, providing immediate visual proof of cadastral base destruction.
* **"Reset DB" Button (`resetDatabase()`):**
  * Calls the administrative endpoint `POST /api/v1/admin/reset`.
  * Truncates the tables and procedurally re-seeds all 487 real Puno parcel polygons and tax owners into memory without needing to restart the Docker container.
* **Mode Toggle (`Vulnerable` vs. `Mitigated - 3 Barriers`):**
  * Switches the frontend routing between backend endpoint trees:
    * Vulnerable Mode: `http://localhost:8020/api/v1/vulnerable/...`
    * Mitigated Mode: `http://localhost:8020/api/v1/mitigated/...`
  * Allows the jury to observe the exact same malicious request processed under both architectural paradigms with a single click.
* **Language Switcher (`ES` / `EN`):**
  * Dynamically toggles all interface labels, tooltips, diagnostic summaries, and table column headers between Spanish and English without reloading the page.

---

### Component 2: Cadastral Search and Manual SQLi Evaluation

Allows arbitrary query inputs to evaluate lexical parsing and SQL compilation behavior:
* **Input Field (`inputCriterio`):**
  * Accepts a legitimate 14-digit cadastral code (e.g., `21010101000000`) or an arbitrary SQL payload.
* **Quick Presets (One-Click Testing Buttons):**
  * **Normal (1 parcel):** Submits a real parcel ID; returns 1 record with nominal baseline latency (~15 ms).
  * **Tautology (`' OR '1'='1`):** In vulnerable mode, nullifies the `WHERE` filter and exfiltrates all 487 parcels across the entire municipality simultaneously. In mitigated mode, searches literally for the string `"' OR '1'='1"` without SQL grammar evaluation, returning 0 records safely.
  * **Comment Truncation (`%' OR 1=1 --`):** Demonstrates query logic truncation using SQL line comments (`--`).
  * **UNION Passwords (`' UNION SELECT username, role, 'EXFILTRATED', password_hash, 0, NULL FROM catastro_usuarios --`):** Executes a classic UNION-based injection bridging the spatial parcel schema with administrative authentication tables, dumping password hashes directly into the results table.

---

### Component 3: Visual Mitigation Pipeline (Defense-in-Depth)

Visualizes request traversal across the three defensive software layers in real time:

1. **Barrier 1 (Web / API Layer - Pydantic & Physical Boundary Clamping):**
   * *Mechanism:* Runtime inspection of inbound HTTP request parameters. Enforces strict numeric typing (`distance: float`), physical parameter range bounding ($0 < distance \le 5000$ meters), and regex validation (`^\d{14}$` for cadastral codes).
   * *Behavior:* If an attacker sends `50) OR (1=1`, Pydantic aborts the request lifecycle immediately and returns **`HTTP 422 Unprocessable Entity`**. The query **never reaches the database engine**, conserving database CPU and memory.
2. **Barrier 2 (Domain / Application Layer - In-Memory Shapely Topology):**
   * *Mechanism:* Parses input geometries (WKT or GeoJSON) in server RAM via the C-based GEOS engine before database interaction.
   * *Behavior:* Evaluates `geom.is_valid`. If the polygon contains self-intersections (figure-eight bowties), unclosed exterior rings, or corrupt coordinates, it is rejected at the application level, preventing PostGIS engine errors.
3. **Barrier 3 (Database / Persistence Layer - GeoAlchemy2 + SQLAlchemy ORM):**
   * *Mechanism:* Compiles the query via SQLAlchemy's Abstract Syntax Tree (**AST**) utilizing native PostGIS spatial types (`Geometry`).
   * *Behavior:* Serializes geometries to Extended Well-Known Binary (**EWKB**) and mandates the use of **Prepared Statements** with typed bind parameters. The PostgreSQL engine receives parameters strictly as data literals over the binary protocol, guaranteeing that SQL quotes and keywords cannot alter the executable query grammar.

---

### Component 4: Interactive Cartographic Viewer (Leaflet + OpenStreetMap)

* **Spatial Reference System:** Projects Puno cadastral parcels in **EPSG:32719** (UTM Zone 19 South, planar meters).
* **Semantic Color Coding:**
  * **Blue:** Authorized cadastral parcels located within the requested distance and sector.
  * **Red:** Anomalous or compromised parcels (unauthorized parcels exfiltrated from restricted sectors in V1, or purged parcels in V5).
* **Interactivity:**
  * Click on any polygon: Displays a popup with LADM metadata (`Parcel ID`, `Sector`, `Zoning`, `Calculated Area m²`).
  * **"Center Map" Button:** Automatically fits the map view to the bounding box of the 487 Puno parcels.

---

### Component 5: SQL Execution Inspector, Metrics, and Diagnostics

The core pedagogical module for the evaluation committee:

* **Monospace Terminal (`boxQuery`):**
  * **Vulnerable Mode:** Prints the exact raw SQL string with concatenated malicious payloads (highlighting broken syntax, escaped parentheses, and tautologies).
  * **Mitigated Mode:** Displays the AST-compiled SQL structure using typed bind parameters (`:distance_1`, `:sector_1`), demonstrating complete separation of data from SQL grammar.
* **Live Performance Metrics:**
  * **LATENCY:** End-to-end execution time in milliseconds (ms), measured from client request dispatch to response reception. Highlights the jump from 10 ms to 1,692 ms under DoS conditions.
  * **HTTP STATUS:** Canonical HTTP response code (`200 OK`, `422 Unprocessable Entity`, `500 Internal Server Error`).
  * **ACTIVE DEFENSE:** Identifies which layer intercepted the attack (`Pydantic (Web Layer)`, `Shapely (App Layer)`, `GeoAlchemy2 (Persistence Layer)`, or `None`).
* **Pedagogical Diagnosis:** Explanatory summary detailing what occurred across server memory, network transport, and database execution.

---

### Component 6: The 6 Attack Vector Presets (Simulations V1 to V6)

Each card runs a preconfigured exploit representing specific CIA Triad violations:

#### 1. `Spatial Logic Bypass` (Confidentiality)
* **Endpoint:** `GET /api/v1/vulnerable/predios/radio?distancia=50) OR (1=1&sector=0101`
* **Mechanism:** A legitimate query should only return parcels within 50 meters in sector `0101`. Injecting the tautology into `ST_DWithin` breaks the spatial predicate and nullifies the sector filter, exfiltrating restricted parcels across the entire municipality in **7.03 ms**.
* **Mitigated Mode:** Pydantic identifies that `'50) OR (1=1'` fails float coercion and returns **HTTP 422**. Zero parcels exposed.

#### 2. `Error-Based Spatial SQLi` (Confidentiality / Side-Channel Oracle)
* **Endpoint:** `GET /api/v1/vulnerable/predios/poligono?wkt=...`
* **Mechanism:** Injects a conditional subquery into `ST_Intersects` that deliberately forces a PostGIS geometry parsing exception whenever a specific bit of the administrative password hash equals `1`.
* **"Simulate Blind Inference" Button:** Runs a live screen loop testing password characters bit by bit, demonstrating how an attacker reconstructs cryptographic credentials in **42 seconds** even when the API never displays query data.

#### 3. `Spatial DoS` (Availability / Algorithmic Complexity $O(N^2)$)
* **Endpoint:** `GET /api/v1/vulnerable/analisis-expansion?buffer_dist=100`
* **Mechanism:** Injects an excessively dense buffer calculation (`quad_segs=100`) combined with an unindexed Cartesian product (`CROSS JOIN`). Forces the underlying C/C++ **GEOS** library to compute complex spatial intersections across thousands of vertices without spatial index support.
* **Impact:** Latency surges to **~1.69 seconds** (a 93.5x computational overhead).
* **Mitigated Mode:** Pydantic clamps the buffer distance to safe upper limits and GeoAlchemy2 decomposes subqueries, maintaining response time at a constant **~15 ms**.

#### 4. `Cadastral Fraud / Tampering` (Integrity)
* **Endpoint:** `POST /api/v1/vulnerable/ficha/modificar`
* **Mechanism:** Injects into an unparameterized `UPDATE catastro_titulares SET ...` statement. Arbitrarily resets property tax valuation to **S/ 0.00** and replaces the registered property owner's name with an attacker alias.
* **Impact:** Direct corruption of public trust and land administration records (ISO 19152 LADM). Immediately visible in the live Cadastral Integrity table below.

#### 5. `Cartographic Destruction` (Integrity & Availability)
* **Endpoint:** `DELETE /api/v1/vulnerable/predios/borrar`
* **Mechanism:** Injects `sector = '0101' OR '1'='1'` into an unparameterized `DELETE FROM tg_lote` query.
* **Impact:** Unconditionally purges all 487 parcels from the cadastral database. The Leaflet map empties completely, and the parcel counter drops to zero. Restoring functionality requires pressing "Reset DB".

#### 6. `Authentication Bypass` (Administrative Privilege Escalation)
* **Endpoint:** `POST /api/v1/vulnerable/auth/login`
* **Mechanism:** Submits payload `admin' --` into the username field. The SQL comment delimiter `--` truncates downstream password hash verification in PostgreSQL.
* **Impact:** Returns an administrative JWT bearer token with the `superadmin_catastro` role, granting full administrative control over the geoportal.

---

### Component 7: Cadastral Integrity (Live LADM Sample Table)

* **Dynamic Table:** Displays a real-time 5-record sample directly querying `tg_lote` (`LA_SpatialUnit` class) and `catastro_titulares` (`LA_Party` class).
* **Columns:** `PARCEL ID`, `DNI / TAX ID`, `PROPERTY OWNER`, and `TAX VALUATION (S/)`.
* **Pedagogical Purpose:**
  * Shows legitimate baseline values to the jury (e.g., property valuation of S/ 85,420.00).
  * Upon executing **V4 (Tampering)**, the table refreshes instantly on screen: the valuation drops to **S/ 0.00** and the owner changes to *"ATACANTE_ILEGITIMO"*.
  * Upon executing **V5 (Purge)**, the table displays *"No cadastral records found"*, demonstrating irrecoverable data loss in unmitigated environments.

---

## 3. Fast-Track Live Demonstration Script (3 Minutes for Thesis Defense)

If the evaluation committee requests a live interactive demonstration, follow this 4-step sequence:

1. **Step 1: Baseline Normal Operation (30 seconds)**
   * Ensure the toggle is set to **Vulnerable Mode**.
   * Click the Quick Preset **"Normal (1 parcel)"**.
   * Highlight that it returns 1 parcel in blue on the map, with nominal latency (~15 ms) and HTTP 200.
2. **Step 2: Demonstrate Spatial Logic Bypass V1 (45 seconds)**
   * Click **"1. Spatial Logic Bypass"**.
   * Show how the map populates with red polygons from unauthorized sectors across the entire municipality.
   * Point to the **SQL Inspector**: highlight the unescaped `50) OR (1=1` payload that broke `ST_DWithin` in 7 ms.
   * Switch the toggle to **Mitigated Mode** and click the attack again: show how **Barrier 1 (Pydantic)** blocks the request at the perimeter with **HTTP 422** in 1 ms without touching the database.
3. **Step 3: Demonstrate Spatial DoS V3 (45 seconds)**
   * Switch back to **Vulnerable Mode** and click **"3. Spatial DoS"**.
   * Show in the metrics panel how latency jumps to **over 1,600 ms** due to the unindexed Cartesian product and dense vertex generation in `ST_Buffer` ($O(N^2)$ complexity).
   * Switch to **Mitigated Mode** and click again: latency drops back to **15 ms flat**.
4. **Step 4: Demonstrate Real-World Legal Impact V4 / V5 (30 seconds)**
   * Point to the bottom **Cadastral Integrity (LADM)** table.
   * Click **"4. Cadastral Fraud"**: demonstrate how the parcel valuation drops to **S/ 0.00** and ownership is reassigned.
   * Conclude verbally: *"This confirms that spatial SQL injection is not merely an abstract web vulnerability; it directly undermines municipal tax collection and the legal integrity of state land administration under ISO 19152."*
   * Click **"Reset DB"** to restore pristine database state.

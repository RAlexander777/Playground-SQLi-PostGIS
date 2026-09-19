# Doctoral Defense Guide and Technical Speaker Notes

**Paper:** *Evaluation of Spatial SQL Injection Vulnerabilities in PostGIS-Based Cadastral Information Systems*  
**Author:** Rodrigo Alexander Becerra Lucano  
**Academic Context:** Research Seminar / Doctoral Defense in Cybersecurity  
**Supporting Slide Deck:** Synchronized 1:1 with the 7 slides of [Evaluation of Spatial SQL Injection in PostGIS.pptx](file:///C:/Users/RODRIGO/Desktop/DOCTORADO/CURSOS/Segundo%20Semestre/CIBERSEGURIDAD/PROYECTO_INVESTIGACI%C3%93N/Evaluation%20of%20Spatial%20SQL%20Injection%20in%20PostGIS.pptx)  
**Estimated Total Presentation Time:** 8 to 10 minutes (approx. 1 to 1.5 minutes per slide)

---

## 1. Conceptual Glossary and Technical Foundations (CRITICAL FOR DEFENSE)

Before delivering your oral defense, ensure complete mastery of these core technical foundations, as the examination committee will probe these to evaluate your conceptual depth:

### A. International Standard ISO 19152 (LADM)
* **What does the acronym stand for?** *Land Administration Domain Model*.
* **Why is it essential in this research?** The testbed does not rely on synthetic, generic toy tables. A cadastre formally defines who owns land, property boundaries, and tax obligations. LADM is the official ISO standard formalizing land administration ontology globally.
* **Core ontological classes applied in the testbed:**
  * **`LA_SpatialUnit`:** Models the geographic cadastral parcel/lot. In our database schema, this corresponds to table **`tg_lote`** (the 487 urban parcel polygons).
  * **`LA_Party`:** Models natural persons, legal entities, or citizens holding rights. In our database, this corresponds to table **`catastro_titulares`** (tax ID, owner identity, tax assessment valuation).
  * **`LA_RRR`:** Models Rights (*Rights*), Restrictions (*Restrictions*, such as municipal zoning), and Responsibilities (*Responsibilities*, such as local tax compliance).
  * **`LA_BAUnit`:** *Basic Administrative Unit*, the administrative binding entity linking owners to their land units.
* **Cybersecurity Implications ("Public Trust" / *Fe Pública*):** In a municipal cadastre, altering a database record transcends an isolated IT compromise; it directly subverts the **public trust of property registries** (*fe pública*). An attacker can reduce property tax assessments to zero (as demonstrated in Simulation 4) or alter ownership records without triggering UI-tier alerts.

---

### B. Evaluated PostGIS Spatial Operators

PostGIS extends PostgreSQL with spatial data types and topological operators compliant with the *OGC Simple Features for SQL* standard. Each operator evaluated in this research exhibits specific computational and mathematical behavior:

#### 1. `ST_DWithin` (Metric Proximity Operator)
* **Definition:** Evaluates whether two geometries lie within a metric threshold distance $d$ of each other:
  $$\text{ST\_DWithin}(geom_1, geom_2, distance)$$
* **Return type:** Boolean (`true` or `false`).
* **Internal engine optimization:** PostGIS expands the Minimum Bounding Box (MBR) of the geometry by $distance$ and performs a rapid index lookup via **GiST** ($O(\log N)$). Only candidate geometries passing this bounding-box test undergo exact Euclidean distance evaluation.
* **Attack Mechanics (V1 - Spatial Logic Bypass):** The vulnerable endpoint concatenates the user-supplied `distance` directly into the dynamic SQL query string:
  ```sql
  WHERE ST_DWithin(geom, ST_MakePoint(x, y), 50) AND cod_sector = '0101'
  ```
  The adversary injects: `50) OR (1=1`. The parsed query mutates into:
  ```sql
  WHERE ST_DWithin(geom, ST_MakePoint(x, y), 50) OR (1=1) AND cod_sector = '0101'
  ```
  Because `OR (1=1)` evaluates as a tautology, it nullifies both the 50-meter metric constraint and the administrative territorial sector filter (`0101`), exfiltrating 50 restricted parcels in **7.03 ms**.

#### 2. `ST_Intersects` (Topological Predicate)
* **Definition:** Determines whether two geometries share at least one common point (interior, boundary, or both), strictly adhering to the **DE-9IM** (*Dimensionally Extended 9-Intersection Model*, Egenhofer, 1994).
* **Return type:** Boolean (`true` or `false`).
* **Attack Mechanics (V2 - Error-Based Spatial Side-Channel / Blind SQLi):** When an API does not expose parcel records directly in HTTP response payloads, an attacker cannot extract text visually. Instead, the attacker crafts a conditional topological oracle:
  * If the $N$-th bit of the administrative password hash is `1`, the query forces an unhandled spatial exception in PostGIS (such as passing invalid WKT to `ST_GeomFromText('ERR')` or topological division by zero).
  * If the bit is `0`, the query executes cleanly and returns an HTTP 200 OK status.
  * Within 128 to 256 automated HTTP binary probes, the adversary reconstructs the complete administrative password hash in **42 seconds** without triggering bulk exfiltration alerts.

#### 3. `ST_Buffer` (Geometric Dilation & Algorithmic DoS)
* **Definition:** A constructive geometric operation that produces a new polygon representing the expanded buffer zone at radius $r$ around the input geometry.
* **The critical `quad_segs` parameter:** Dictates the number of line segments computed per quadrant to approximate circular curvature when buffering polygon vertices (defaults to 8).
* **Attack Mechanics (V3 - Spatial DoS via Algorithmic Complexity $O(N^2)$):**
  * Rooted in the theoretical framework of **Crosby and Wallach (2003)**: rather than overwhelming network bandwidth with volumetric floods (DDoS), a single crafted request triggers worst-case algorithmic branches in the database engine.
  * Real urban parcels in Puno exhibit up to 222 vertices. The adversary injects a spatial `CROSS JOIN` combined with dense buffer expansions (`quad_segs = 100`).
  * This forces the underlying C/C++ **GEOS** library in PostGIS to perform edge-by-edge intersection calculations across hundreds of thousands of vertices, completely bypassing GiST spatial indices.
  * **Empirical Impact:** Latency escalates from 10.8 ms to **1,692.1 ms (a 93.5x or ~9,700% degradation)**. Two concurrent requests exhaust 100% of PostgreSQL worker processes, resulting in full service denial for municipal map visors.

---

### C. Coordinate Reference System EPSG:32719, GiST, and EWKB
* **What is `EPSG:32719`?**
  * Projected Coordinate Reference System (**SRID**): Universal Transverse Mercator (**UTM**), Zone 19 South, datum WGS 84. It encompasses the southern Andean plateau and the city of Puno, Peru.
  * **Crucial distinction over geographic coordinates (`EPSG:4326`):** In angular latitude/longitude (degrees), a distance of `50` represents 50 degrees (~5,500 km). In `EPSG:32719`, $(X, Y)$ coordinates are strictly measured in **planar meters**. Consequently, passing `50` to `ST_DWithin` represents exactly 50 physical meters on the ground.
* **What is a `GiST` Index?**
  * *Generalized Search Tree*. It implements an R-Tree index over geometric Minimum Bounding Boxes (MBR), pruning search complexity from sequential scanning $O(N)$ down to logarithmic depth $O(\log N)$. Injection vector V3 deliberately breaks GiST usage by forcing cross-table cartesian products.
* **What is `EWKB`?**
  * *Extended Well-Known Binary*. PostGIS native binary encoding containing geometry type, vertices, and the SRID header. The defensive pipeline serializes parameters into EWKB bind variables via GeoAlchemy2, making it mathematically impossible for characters like `'` or `OR` to be interpreted as executable SQL code.

---

## 2. Slide-by-Slide Defense Walkthrough

### Slide 1: Title Slide
* **Suggested Time:** 45 seconds.
* **Title:** *Evaluation of Spatial SQL Injection Vulnerabilities in PostGIS-Based Cadastral Information Systems*.
* **Spoken Script:**
  > "Distinguished members of the examination committee, good morning. This research investigates a critical blind spot in geospatial infrastructure security: the susceptibility of cadastral information systems built on PostgreSQL and PostGIS to spatial SQL injection attacks. We will demonstrate that native geometric operators—frequently presumed immune to injection due to their mathematical nature—require a strict software-layer defensive architecture to guarantee municipal public trust and server availability."

---

### Slide 2: Introduction
* **Suggested Time:** 1 minute 15 seconds.
* **Slide Contents:** Client-server web services, PostGIS geometric operators (`ST_DWithin`, `ST_Intersects`, `ST_Buffer`), CIA triad, and defense barriers.
* **Key Talking Points:**
  1. *Modern Cadastre Exposure:* Modern cadastral visors and Spatial Data Infrastructures (SDI) publish REST APIs to handle citizen queries, urban zoning, and municipal property tax collection.
  2. *The Spatial Security Myth:* There is a widespread engineering assumption that spatial operators (`ST_DWithin`, `ST_Intersects`, `ST_Buffer`) are safe from SQL injection because they handle coordinates and geometries. In reality, developers routinely construct spatial queries via dynamic string concatenation.
  3. *Scope of Research:* We conduct a quantitative empirical evaluation of six attack vectors targeting the CIA triad (Confidentiality, Integrity, and Availability) and measure the computational overhead of a multi-barrier software mitigation pipeline.

---

### Slide 3: Test Dataset and Evaluation Environment
* **Suggested Time:** 1 minute 30 seconds.
* **Slide Contents:** 487 urban parcels (ISO 19152 / LADM), 4 to 222 vertices, 3 relational entities without PII, Docker microservices.
* **Key Talking Points:**
  1. *Methodological Rigor (ISO 19152 LADM):* We avoided flat synthetic mockups. The testbed models **487 real-world cadastral parcels from Puno, Peru**, georeferenced in **EPSG:32719** under the international standard class `LA_SpatialUnit`.
  2. *Realistic Vector Complexity:* Polygons range from 4 to 222 vertices (mean: 9.0). This realistic topological density is essential to subject the spatial engine to non-linear intersection math.
  3. *Relational Schema and Ethics:* Organized across three relational tables: `tg_lote` (cartography), `catastro_titulares` (tax assessment and owners), and `catastro_usuarios` (authentication). Fiscal attributes were generated synthetically, ensuring zero Personally Identifiable Information (PII).
  4. *Scientific Reproducibility:* The entire testbed is containerized via Docker (PostgreSQL 15 + PostGIS 3.3 and Python 3.11 FastAPI) and published on GitHub for open replication.

---

### Slide 4: Evaluation of the 6 Attack Vectors (CIA Triad)
* **Suggested Time:** 2 minutes.
* **Slide Contents:** Confidentiality (V1, V2), Integrity (V4, V5, V6), Availability (V3), and embedded chart of **Figure 3** (Spatial DoS Algorithmic Complexity Curve).
* **Key Talking Points per Vector:**
  * **Confidentiality:**
    * **V1 (Spatial Logic Bypass in `ST_DWithin`):** Injected tautology `50) OR (1=1` breaks the distance and territorial sector boundary, exfiltrating 50 restricted parcels in 7.03 ms.
    * **V2 (Error-Based Side-Channel in `ST_Intersects`):** Boolean inference linked to conditional PostGIS exceptions; extracts administrative password hashes bit-by-bit in 42 seconds.
  * **Availability:**
    * **V3 (Spatial DoS via `ST_Buffer`):** Algorithmic Complexity Attack $O(N^2)$ (Crosby & Wallach). Injected Cartesian product saturates GEOS workers, driving query latency to 1,692 ms.
  * **Integrity:**
    * **V4 (Cadastral Record Tampering):** Injected `UPDATE SET` clause reduces fiscal property tax to S/ 0.00 and alters legal ownership in `catastro_titulares`.
    * **V5 (Cartographic Deletion):** Injected `WHERE 1=1` clause wipes all 487 lot geometries from `tg_lote`, crashing the municipal map viewer.
    * **V6 (Authentication Bypass):** SQL comment injection (`admin' --`) yields immediate privilege escalation to `superadmin_catastro`.

* **Live Chart Interpretation (Figure 3: Spatial DoS Algorithmic Complexity Curve):**
  * *Reading the Axes:* The **X-axis** indicates pairwise geometric vertices evaluated in the Cartesian cross-join (scaling up to ~9,600 vertices across 400 evaluated parcel pairs). The **Y-axis** reflects PostGIS/GEOS execution latency in milliseconds (ms).
  * *The Red Curve (Vulnerable API):* Exhibits a classic quadratic ($O(N^2)$) execution spike. As `quad_segs` increases from 1 to 24 in `ST_Buffer`, the underlying C/C++ **GEOS** engine must compare edges pairwise without spatial index (GiST) acceleration, causing latency to surge from 10.8 ms to **1,692.1 ms (a 93.5x or ~9,700% degradation)**.
  * *The Green Line (Mitigated Architecture):* Stays perfectly flat at a constant **~15 ms** (bounded $O(1)$ complexity). This proves that Pydantic input bounds clamping and GeoAlchemy2 subquery decoupling eliminate the algorithmic explosion before consuming database CPU.
  * *Key Takeaway for the Jury:* *"This empirical curve validates the Crosby & Wallach principle: an adversary does not need a massive distributed botnet to take down a municipal geoportal; a single malicious query triggering worst-case algorithmic complexity is sufficient to lock up database workers."*

---

### Slide 5: Attack Mitigation Barriers
* **Suggested Time:** 1 minute 30 seconds.
* **Slide Contents:** Three-tier defense (Pydantic, Shapely, GeoAlchemy2) and the architectural workflow diagram of **Figure 1**.
* **Key Talking Points (Application-Layer Defense-in-Depth):**
  * **Barrier 1 (Web Layer - Pydantic):** Strict runtime scalar type enforcement, physical coordinate bounds checking, and alphanumeric regex guards. Rejects malicious inputs with `HTTP 422 Unprocessable Entity` before invoking the database.
  * **Barrier 2 (Domain Layer - In-Memory Shapely):** Pre-execution topological validation for WKT/GeoJSON payloads. Rejects self-intersecting or degenerated polygons directly in RAM.
  * **Barrier 3 (Persistence Layer - GeoAlchemy2 + SQLAlchemy):** Native geometry compilation into **EWKB** binary bind variables and mandatory **prepared statements**. Ensures absolute mathematical separation between SQL code and user data.

* **Live Diagram Interpretation (Figure 1: Defense-in-Depth Pipeline Architecture):**
  * *Reading the Flow:* Follow the 4-stage sequential pipeline left-to-right: `HTTP Client Request` $\rightarrow$ `Barrier 1 (Pydantic)` $\rightarrow$ `Barrier 2 (Shapely)` $\rightarrow$ `Barrier 3 (GeoAlchemy2)` $\rightarrow$ `PostGIS Engine`.
  * *Architectural Design Principles (Fail-Fast & Least Privilege):*
    1. **Perimeter Guard (Pydantic):** Blocks malicious payloads at the HTTP gateway. If an attacker injects `'50) OR (1=1'`, the 422 validation error terminates the lifecycle in 1 ms without hitting the database, saving CPU and RAM.
    2. **Domain Guard (Shapely):** The database engine should not serve as an in-line geometric validator. Checking polygon validity (`is_valid`) in server RAM prevents low-level GEOS/C exceptions inside PostgreSQL.
    3. **Persistence Guard (GeoAlchemy2):** By compiling queries via SQLAlchemy's Abstract Syntax Tree (AST) and serializing to EWKB binaries with prepared statements, parameters travel over PostgreSQL's binary protocol purely as data, rendering SQL grammar manipulation mathematically impossible.

---

### Slide 6: Results and Performance
* **Suggested Time:** 1 minute 30 seconds.
* **Slide Contents:** Summary metric cards, comparative performance table, and the two-panel empirical chart of **Figure 2**.
* **Key Talking Points:**
  1. *Total Effectiveness:* The pipeline achieved a **100% neutralization rate across all 6 evaluated vectors** (zero CIA triad compromises).
  2. *Negligible Overhead (+2.63 ms):* Mean query latency increased from 17.26 ms to 19.89 ms (+15.24%), sustaining a high throughput of **484 requests/sec**. An added 2.6 ms is completely imperceptible to end users.
  3. *Tail Latency Improvement (-12.59% at p99):* The 99th percentile latency dropped from 43.75 ms to 38.24 ms. This stability gain occurs because PostgreSQL reuses compiled execution plans (*prepared statements*) instead of repeatedly re-parsing raw SQL strings.

* **Live Chart Interpretation (Figure 2: Concurrency & Latency Curves):**
  * **Panel (a) - Throughput (req/s) vs. Concurrency Level (1 to 100 concurrent clients):**
    * *Curve Behavior:* The red curve (vulnerable API) saturates at **556.21 req/s** at 50 clients. The green curve (mitigated API) reaches saturation at **484.36 req/s**.
    * *Demonstrated Trade-off:* The throughput penalty is merely **12.9%**. For a municipal land information system, this minor overhead is fully justified to achieve 100% architectural immunity against data exfiltration and fiscal fraud.
  * **Panel (b) - Latency Percentiles ($p_{50}$ and $p_{99}$) vs. Concurrency Level:**
    * *Median Behavior ($p_{50}$):* Under normal operating conditions (1 to 25 clients), median latency curves are virtually indistinguishable, exhibiting only a **+2.63 ms** difference.
    * *The Key Research Finding (Tail Latency $p_{99}$):* Notice that under heavy concurrency (100 threads), the green dashed line (mitigated $p_{99}$) drops **BELOW** the red dotted line (vulnerable $p_{99}$).
    * *Technical Justification for the Jury:* Worst-case tail latency is reduced by **12.59%** (from 38.4 ms down to 33.6 ms). This occurs because GeoAlchemy2's prepared statements allow PostgreSQL to reuse cached execution plans in session memory. In contrast, the vulnerable API's dynamic string concatenation forces the database query planner to lexically re-parse, re-analyze, and re-optimize every single concurrent query, congesting the engine's main thread.

---

### Slide 7: Study Conclusions
* **Suggested Time:** 1 minute.
* **Slide Contents:** Three core study conclusions.
* **Closing Script:**
  1. *Spatial Rigor Principle:* PostGIS functions require the same parameterization rigor as traditional relational queries; treating them as simple strings jeopardizes municipal tax collection and public trust.
  2. *Defense at the Right Layer:* Generic syntactic filtering fails against spatial predicates. Pre-execution in-memory inspection via Shapely and Pydantic is vital to prevent quadratic $O(N^2)$ algorithmic stalling.
  3. *Production Viability:* The marginal overhead of 2.63 ms confirms that this multi-barrier architecture can be immediately deployed in production municipal SDI services without degrading performance.

---

## 3. Defense Examination Q&A Bank

| Potential Question | Authoritative Technical Response |
| :--- | :--- |
| **"Why evaluate on 487 parcels rather than millions of records?"** | *"Our research evaluates the **logical vulnerability of queries and the algorithmic complexity of topological predicates**, not PostgreSQL disk I/O throughput. 487 real parcels containing up to 222 vertices provide sufficient topological complexity to trigger non-linear GEOS overhead without introducing disk pagination noise."* |
| **"What specifically is ISO 19152 (LADM) and why did you use it?"** | *"It is the Land Administration Domain Model. It standardizes cadastral classes globally: `LA_SpatialUnit` for cartographic parcels and `LA_Party` for taxpayers and valuations. It proves that corrupting a cadastral database destroys legal public trust and property tax legitimacy, rather than isolated data rows."* |
| **"Why does quadratic complexity $O(N^2)$ occur in the Spatial DoS?"** | *"Because injecting a Cartesian product (`CROSS JOIN`) with high buffer densities forces the underlying GEOS engine to compare edge-by-edge intersections between complex polygon pairs sequentially, completely bypassing the GiST spatial index and driving latency from 10.8 ms to 1,692 ms."* |
| **"Why was GeoAlchemy2 required in addition to standard SQLAlchemy?"** | *"Standard SQLAlchemy only handles scalar relational types (integers, strings, dates). GeoAlchemy2 introduces native PostGIS `Geometry` types, enforces SRID management (EPSG:32719), and compiles geometric objects directly into EWKB binary bind variables for the database driver."* |
| **"Why did the 99th percentile (p99) improve by 12.59% in the mitigated API?"** | *"Because the mitigated architecture uses prepared statements. PostgreSQL compiles the execution plan once and caches it in memory, eliminating the continuous overhead of lexical scanning and query plan re-evaluation on every request."* |
| **"Where can your findings and methodology be audited and reproduced?"** | *"The complete testbed, the Puno dataset, and all exploit scripts are fully containerized in Docker and publicly available on GitHub at `RAlexander777/Playground-SQLi-PostGIS`."* |

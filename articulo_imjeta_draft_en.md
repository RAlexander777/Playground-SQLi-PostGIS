# Evaluation of Spatial SQL Injection Vulnerabilities in PostGIS-Based Cadastral Information Systems

**Rodrigo [Affiliation / Author Details]**  
*National University / Doctoral Program in Cybersecurity*  
*investigador.catastro@doctorado.edu.pe*  

---

### Abstract
The integration of spatial databases into web architectures has expanded the attack surface for modern applications; however, the specific risks associated with spatial SQL injections remain largely underexplored. This paper investigates the exploitation and mitigation of spatial SQL injections within cadastral information systems utilizing PostGIS. A containerized testbed was developed using Docker to simulate a critical infrastructure API built with Python (FastAPI) and PostgreSQL/PostGIS. The study demonstrates how attackers can leverage spatial functions (e.g., ST_DWithin, ST_Intersects) to manipulate geospatial logic, exfiltrate unauthorized zoning data, or induce denial-of-service states. Furthermore, the research evaluates the performance impact of implementing robust mitigation strategies, comparing vulnerable dynamic spatial queries with parameterized queries executed via Object-Relational Mapping (ORM) tools such as SQLAlchemy and GeoAlchemy2. Results demonstrate that the proposed pipeline neutralized 100% of the attack vectors with a mean latency overhead of 2.63 ms (+15.24%) and a 12.59% improvement in tail stability (p99). We conclude that effective spatial injection mitigation relies on enforcing in-memory topological validation and rigid ORM parameterization at the application layer rather than perimeter firewalls, securing cadastral integrity with minimal operational overhead.

**Keywords:** Spatial injections; Cadastral systems; Geospatial cybersecurity; Penetration testing; Databases

---

## 1. Introduction

Modern cadastral information systems expose web services and geoportals over client-server architectures to administer land tenure, municipal zoning, and property taxation (Lemmen et al., 2015). Within this operational domain, PostgreSQL along with its PostGIS spatial extension represents the predominant open-source solution for storing and querying official vector cartography (Obe & Hsu, 2021).

However, exposing these spatial data services via REST APIs introduces attack vectors whenever queries are constructed through string concatenation within spatial functions. While classical SQL injection and its risks in web applications have been extensively documented (Clarke, 2012; Halfond et al., 2006; OWASP Foundation, 2021), manipulating PostGIS geometric operators—such as `ST_DWithin`, `ST_Intersects`, or `ST_Buffer`—exhibits distinct mechanics: unsanitized input not only circumvents relational filters or exfiltrates records, but also triggers denial-of-service conditions through topological calculations of high algorithmic complexity.

This article presents an experimental evaluation of spatial SQL injection vulnerabilities in PostGIS-based cadastral systems. The study: (1) documents and evaluates six attack vectors mapped to the CIA triad (Confidentiality, Integrity, and Availability); (2) implements a reproducible testbed over an experimental dataset of 487 urban parcels structured under the ISO 19152 (LADM) standard; and (3) quantifies the latency and throughput impact of a mitigation architecture combining strongly typed ORM compilation (GeoAlchemy2) with pre-execution validation via Shapely and Pydantic.

---

## 2. Related Work

Research converges across four primary foundational domains:

### 2.1. SQL Injection in Spatial Engines and Topological Operators
Fundamental cybersecurity literature has established robust classifications for SQL injection attacks. Halfond et al. (2006) categorized these threats into tautologies, union queries, blind injections, and stored procedure piggybacking. Clarke (2012) formalized abstract syntax tree (AST) manipulation resulting from unsanitized input concatenation. However, these paradigms do not address how spatial algebraic operators (Egenhofer, 1994) alter logical evaluation trees. Unlike scalar values, geometric expressions encompass multiple dimensions, spatial reference systems (SRID), and minimum bounding boxes (MBR), expanding the syntactic escape surface.

### 2.2. Spatial Access Control Models and Inference Risks
Access control in spatial databases was conceptualized by Bertino et al. (2005) through the GEO-RBAC (*Spatially Aware Role-Based Access Control*) model, demonstrating that read/write privileges must adhere to dynamic geographic boundaries. Concurrently, Chun and Atluri (2008) and Atluri and Chun (2004) investigated spatial inference risks in spatial database management systems (SDBMS), where unauthorized actors deduce protected features by correlating sequential spatial queries. Nonetheless, these frameworks presume that the application layer faithfully maps spatial policies to the database engine. In modern web architectures, unsafe parameter concatenation directly invalidates spatial authorization at the persistence layer.

### 2.3. Cadastral Data Integrity and Modeling under the LADM Standard
Cadastral information modeling is governed internationally by ISO 19152:2012, known as the *Land Administration Domain Model* (LADM). Foundational literature (Lemmen et al., 2015; van Oosterom et al., 2006) formalizes core classes including `LA_SpatialUnit` (cadastral parcels) and `LA_Party` (property owners), later extended toward automated mass valuation models (Kara et al., 2021). While LADM prescribes data semantics and interoperability, it omits query-level defensive architectural patterns against injection attacks, leaving land tenure and fiscal records vulnerable to software implementation flaws.

### 2.4. Algorithmic Complexity Attacks and OGC Service Vulnerabilities
The operational relevance of spatial injection was highlighted by CVE-2023-25157 (CVSS score 9.8), where GeoServer permitted unauthenticated remote SQL execution through unsafe evaluation of OGC filter expressions over PostGIS databases (National Vulnerability Database, 2023). In the denial-of-service domain, Crosby and Wallach (2003) formalized algorithmic complexity attacks, demonstrating that crafted inputs can force worst-case ($O(N^2)$) execution. In spatial engines, computational algorithms within the GEOS library demand quadratic overhead when evaluating complex geometries without GiST spatial index pre-filtering (Agarwal & Rajan, 2016). Despite these precedents, empirical latency impacts and integrated defensive pipelines connecting web parsers to spatial engines remain under-researched.

---

## 3. Methodology

### 3.1. Research Design and Testbed Setup
An experimental, quantitative design was adopted to assess spatial endpoint vulnerability to SQL injection and quantify performance trade-offs introduced by multi-barrier mitigations. The evaluation benchmarks three defensive postures: (1) an unmitigated vulnerable service, (2) a perimeter-protected service using a signature-based web application firewall (OWASP CRS v3.3), and (3) an application-layer mitigation pipeline combining typed ORM compilation with in-memory topological pre-validation.

### 3.2. Cadastral Dataset
The experimental dataset comprises 487 contiguous urban cadastral parcels structured under the ISO 19152 standard (LADM, `LA_SpatialUnit` class) and georeferenced in `EPSG:32719`. The geometries exhibit a complexity ranging between 4 and 222 vertices (mean: 9.0 vertices per polygon). To ensure reproducibility and ethical safeguards, base cartography was retrieved from open sources and fiscal attributes were procedurally generated without incorporating personally identifiable information (PII).

### 3.3. Experimental Environment and Architecture
The testbed was implemented in Docker containers using isolated microservices: (1) a database service running PostgreSQL 15 and PostGIS 3.3, and (2) a Python 3.11 API with FastAPI and Uvicorn. Stress testing was executed in a controlled 14-core 5.2 GHz environment with 32 GB DDR5 RAM on Linux kernel 6.6 (WSL2). Source code, dataset, and the interactive playground are publicly available at: https://github.com/RAlexander777/Playground-SQLi-PostGIS.

### 3.4. Test Vectors and Performance Metrics
Six exploitation vectors based on the injection testing guidelines of the Web Security Testing Guide (OWASP Foundation, 2023), targeting the three dimensions of the CIA triad (Confidentiality, Integrity, and Availability, summarized in Appendix 1), were structured. Performance evaluation encompassed a 300-request load test and stepped concurrency curves (1 to 100 clients), recording latency metrics (mean, p50, p95, p99) and throughput (req/s).

---

## 4. Attack Simulations and Exploitation Results (Phase 1)

### 4.1. Simulation 1: Spatial Logic Bypass
* **Operational Scenario:** The API exposes the endpoint `GET /api/v1/vulnerable/predios/radio`, designed to return cadastral lots within a 50-meter radius restricted strictly to sector `'0101'`.
* **Attack Mechanism:** The attack vector leverages the `distance` parameter to prematurely close the parenthesis of `ST_DWithin` and inject a logical tautology negating both the radius and sector constraints:
  $$\text{Payload:} \quad \texttt{50) OR 1=1 --}$$
* **Result:** The resulting query neutralized the territorial clause `cod_sector = '0101'`. While the legitimate query returned 1 authorized parcel, the payload forced a sequential table scan, exfiltrating 50 unauthorized cadastral parcels in 7.03 ms. In the mitigated endpoint, Pydantic and GeoAlchemy2 strictly enforced numerical type boundaries, neutralizing the attack with HTTP 422.

### 4.2. Simulation 2: Data Inference via Geometric Error Channels (Error-Based Spatial SQLi)
* **Operational Scenario:** The endpoint `GET /api/v1/vulnerable/predios/poligono` receives a polygon in WKT format to evaluate spatial intersection (`ST_Intersects`). The API returns cartographic vectors without textual data, precluding standard `UNION SELECT` attacks.
* **Attack Mechanism:** An inferential payload was designed to establish a blind boolean oracle. If the character guess for the administrator password hash is correct, an invalid PostGIS geometry function is called (`ST_GeomFromText` with corrupt topology or illegal type cast), triggering an engine exception and an HTTP 500 error. If false, PostGIS proceeds normally with HTTP 200:
  $$\text{Payload:} \quad \texttt{POLYGON(...)', 32719)) AND 1=(CASE WHEN (SELECT SUBSTR(password\_hash, 1, 1)...)='a' THEN CAST(ST\_GeomFromText('ERR') AS INT) ELSE 1 END) --}$$
* **Result:** Using an automated Python script, the attacker reconstructed the cryptographic hash and administrative username (`admin`) in 42 seconds, proving that the absence of textual output does not prevent data exfiltration when PostGIS error codes are reflected by the web server. In the mitigated version, Shapely evaluated topological validity in application memory, rejecting the malicious syntax with HTTP 422.

### 4.3. Simulation 3: Spatial Denial of Service (Spatial DoS)
* **Operational Scenario:** The endpoint `GET /api/v1/vulnerable/predios/analisis-expansion` performs geometric analysis calculations.
* **Attack Mechanism:** Leveraging the baseline geometric complexity of parcels (averaging 9.0 vertices and up to 222 vertices per polygon), the attacker injects a subquery with an $O(N^2)$ spatial Cartesian product computing buffers with high segment densities per quadrant:
  $$\text{Payload:} \quad \texttt{10 + (SELECT COUNT(*) FROM tg\_lote a CROSS JOIN tg\_lote b WHERE ST\_Intersects(ST\_Buffer(a.geom, 5, seg), ST\_Buffer(b.geom, 5, seg)) ...)}$$
* **Result:** As empirically evidenced in Figure 1, injecting the Cartesian product triggers an $O(N^2)$ algorithmic complexity explosion that escalates latency from 10.8 ms up to 1,665.16 ms as evaluated buffer vertices expand from 14,400 to over 345,600 points, saturating PostgreSQL worker threads on the multi-core workstation. Conversely, the mitigated architecture reliably preserves a bounded latency of ~15 ms by constraining parameters to validated scalar ranges via Pydantic and GeoAlchemy2.

![Figure 1: Quadratic algorithmic degradation curve O(N²) in PostGIS/GEOS under geometric overhead injection vs. bounded mitigation](figures/fig3_spatial_dos_complexity.png)  
*Figure 1. Quadratic algorithmic degradation curve O(N²) in PostGIS/GEOS under geometric overhead injection vs. bounded mitigation*

### 4.4. Simulation 4: Cadastral Record Tampering (Tax Assessment Manipulation)
* **Operational Scenario:** The endpoint `POST /api/v1/vulnerable/ficha/modificar` allows updating parcel records via direct string concatenation in the `SET` clause.
* **Attack Mechanism:** Through concatenation in the `SET` clause, an adversary manipulated the tax assessment setting it to S/ 0.00 and replaced the legitimate property owner with an unauthorized third party:
  $$\text{Payload:} \quad \texttt{id\_lote = '21010101000000', nuevo\_autovaluo = 0, nuevo\_titular = 'HACKER'}$$
* **Result:** The database updated the fiscal record without type or schema validation. In contrast, the mitigated endpoint blocked the fraud via alphabetic regular expressions and positive range constraints in SQLAlchemy (HTTP 422).

### 4.5. Simulation 5: Bulk Deletion of Cadastral Records (Data Destruction)
* **Operational Scenario:** The endpoint `DELETE /api/v1/vulnerable/predios/borrar` receives a sector identifier for layer cleanup.
* **Attack Mechanism:** Through string interpolation, the literal payload `'0101' OR '1'='1'` is injected into the sector filter of the `DELETE` statement:
  $$\text{Payload:} \quad \texttt{filtro\_sector = '0101' OR '1'='1'}$$
* **Result:** The query transformed into an unconditional deletion (`DELETE FROM tg_lote WHERE cod_sector = '0101' OR '1'='1'`), purging all 487 parcels and clearing the web viewer. In contrast, the mitigated endpoint validated the sector parameter using the strict regex pattern `^\d{4}$`, rejecting the injection with HTTP 422 and preserving the cadastral repository intact.

### 4.6. Simulation 6: Authentication Bypass in the Cadastral Web Viewer
* **Operational Scenario:** The endpoint `POST /api/v1/vulnerable/auth/login` validates credentials to access private cadastral layers.
* **Attack Mechanism:** The attacker enters `"admin' --"` in the username field, commenting out password hash verification:
  $$\text{Payload:} \quad \texttt{username = admin' --, password = any\_value}$$
* **Result:** Password verification was bypassed in SQL, granting immediate access and issuing a token with the `superadmin_catastro` role. The mitigated version featuring prepared statements and SHA-256 cryptographic hashing neutralized the bypass by searching literally for the quoted string without evaluating it as SQL syntax.

---

## 5. Mitigation Strategies and Performance Evaluation (Phase 2)

### 5.1. Secure Architectural Redesign
As illustrated in Figure 2, the architectural mitigation integrated a three-barrier defense-in-depth pipeline:
1. **Barrier 1 (Strict Parameter Boundaries in Pydantic):** Strict type and range boundaries (`gt=0, le=2000` for distances; regex `^\d{4}$` for sector identifiers), eliminating injection surface for modifiers such as `quad_segs`.
2. **Barrier 2 (In-Memory Topological Pre-Validation with Shapely):** For endpoints accepting vector geometries (WKT/GeoJSON), an in-memory application validator was integrated via Shapely (`shapely.wkt.loads`). Geometries with self-intersections or corrupt syntax are rejected with HTTP 422 prior to database interaction.
3. **Barrier 3 (Native Parameterization with GeoAlchemy2 and SQLAlchemy):** Native compilation using binary bind variables (EWKB) and execution plan reuse (*prepared statements*), guaranteeing that the database engine interprets input strictly as literal data.

![Figure 2: Architecture of the 3-barrier defense-in-depth pipeline for PostGIS cadastral services](figures/fig1_defense_pipeline.png)  
*Figure 2. Architecture of the 3-barrier defense-in-depth pipeline for PostGIS cadastral services*

### 5.2. Benchmarking and Latency Analysis
A comparative benchmark of 300 requests under 10 concurrent clients was conducted between the vulnerable API and the mitigated API. Results are summarized in Table 1.

**Table 1: Performance and Latency Comparison between Vulnerable API and Mitigated API**

| Performance Metric | Vulnerable API (Dynamic SQL) | Mitigated API (GeoAlchemy2) | Variance (Overhead) |
| :--- | :--- | :--- | :--- |
| **Throughput** | 556.21 req/s | 484.36 req/s | -71.85 req/s (-12.92%) |
| **Mean Latency** | 17.26 ms | 19.89 ms | +2.63 ms (+15.24%) |
| **50th Percentile (Median / p50)** | 15.37 ms | 18.42 ms | +3.05 ms |
| **95th Percentile (p95)** | 31.49 ms | 32.63 ms | +1.14 ms |
| **99th Percentile (p99)** | 43.75 ms | 38.24 ms | -5.51 ms (-12.59%) |
| **Error Rate** | 0.0% | 0.0% | 0.0% |

*Note: Empirical measurements gathered under 300 concurrent requests (concurrency=10) on a multi-core workstation with 32 GB DDR5 RAM in Docker Desktop (PostgreSQL 15 / PostGIS 3.3).*

To characterize resilience under progressive stress, a multi-tier concurrency benchmark spanning 1 to 100 concurrent clients was executed. As evidenced in Figure 3(a), throughput in the mitigated architecture scales smoothly, reaching a stable plateau exceeding 450 req/s without deadlock collapse. Concurrently, Figure 3(b) demonstrates that tail latency at the 99th percentile (p99) remains consistently lower and tighter in the mitigated API due to prepared statement caching in PostgreSQL.

![Figure 3: Empirical throughput and latency percentiles (p50 and p99) comparison under scaled concurrency (1 to 100 clients)](figures/fig2_concurrency_latency.png)  
*Figure 3. Empirical throughput and latency percentiles (p50 and p99) comparison under scaled concurrency (1 to 100 clients)*

---

## 6. Discussion

The empirical results demonstrate that mitigation based on GeoAlchemy2 and pre-execution validation with Shapely introduces a mean latency overhead of merely **2.63 milliseconds per request (+15.24%)**, sustaining a throughput of **484.36 requests per second**. Particularly noteworthy is the reduction in tail latency at the 99th percentile (p99), which dropped from 43.75 ms to 38.24 ms (**-12.59% improvement in service stability**), an optimization directly attributed to efficient reuse of compiled execution plans (*prepared statements*) in PostgreSQL by eliminating continuous re-parsing of dynamic queries. This marginal average latency increase is negligible compared to the substantial security gains achieved, reliably neutralizing bulk cadastral data exfiltration, error-based side-channels, and spatial denial of service. It is concluded that traditional WAFs are ineffective against spatial payloads, necessitating spatially aware syntactic validation mechanisms embedded directly within application code.

Figure 4 summarizes the attack mitigation and blocking rate (%) across the six evaluated vectors, contrasting an unprotected architecture, a traditional signature-based WAF (OWASP ModSecurity Core Rule Set), and the proposed pipeline. Whereas the generic WAF fails to identify spatial attacks (achieving only 0% to 20% blocking on topological vectors such as `ST_DWithin` and `ST_Intersects` due to the lack of geospatial grammar awareness), the three-barrier pipeline achieves a complete **100% blocking rate** across all evaluated vectors of the CIA triad.

![Figure 4: Attack mitigation and blocking rate (%) across unprotected architecture, traditional WAF (OWASP CRS), and the proposed pipeline](figures/fig4_attack_mitigation_matrix.png)  
*Figure 4. Attack mitigation and blocking rate (%) across unprotected architecture, traditional WAF (OWASP CRS), and the proposed pipeline*

**Platform independence and benchmarking validity.** While absolute latency metrics were acquired on a modern multi-core workstation, the methodological validity and generalizability of the findings reside in the relative proportions (+15.24% mean overhead and -12.59% p99 tail improvement) and in computational asymptotic complexities. On municipal servers or cloud instances with restricted hardware resources (common in local government environments), the computational cost of Python preprocessing (GeoAlchemy2/Shapely) remains negligible relative to dominant disk I/O and relational concurrency bottlenecks. Conversely, the absence of defenses against algorithmic complexity attacks ($O(N^2)$) such as Spatial DoS (Simulation 3) proves critical on entry-level processors with lower parallelism, where a small number of malicious queries can immediately incapacitate the entire cadastral service.

**Systemic impact on the integrity of cadastral procedures and records.** The empirical feasibility of Simulation 4 (tampering with property valuation and ownership via direct injection) illustrates how a persistence-level failure transcends single-table corruption and compromises the validity of municipal e-government operations. When cadastral systems interoperate autonomously to issue cryptographic QR-verified cadastral certificates, tax clearance certificates, or property conveyance deeds under ISO 19152 LADM, injecting arbitrary data into `catastro_titulares` and `tg_lote` propagates fiscal and registry inconsistencies without triggering UI-tier alerts, confirming that strongly typed ORM sanitization is an indispensable safeguard for the reliability of digital public services.

---

## 7. Conclusions and Recommendations

This article formalized and empirically demonstrated the viability of six spatial SQL injection vectors targeting the CIA triad (Confidentiality, Integrity, and Availability) in PostGIS-based cadastral information systems, proving that native topological functions offer no data isolation guarantees when constructed via string concatenation. Experimental evaluation over a dataset of 487 cadastral parcels structured under the ISO 19152 (LADM) standard confirmed that unauthenticated adversaries can bypass territorial boundaries, reconstruct credentials through geometric error side-channels, induce denial of service via quadratic algorithmic overhead, tamper with fiscal property records, and execute bulk cartographic deletions. In response, the defense-in-depth architecture based on typed ORM compilation (GeoAlchemy2), rigid typing with Pydantic, and in-memory pre-validation with Shapely successfully mitigated 100% of the evaluated exploitation scenarios. Transactional benchmarking demonstrated that this scheme introduces a mean latency overhead of only 2.63 ms (+15.24%), while simultaneously enhancing 99th-percentile stability by 12.59% through execution plan reuse in PostgreSQL. In conclusion, securing cadastral infrastructures requires abandoning traditional scalar sanitization paradigms in favor of ORM parameterization and spatially aware syntactic controls integrated from the foundational software architecture design.

---

## 8. References

* Agarwal, S., & Rajan, K. S. (2016). Performance analysis of MongoDB versus PostGIS/PostgreSQL databases for line intersection and point containment spatial queries. *Spatial Information Research*, 24(6), 669–677. https://doi.org/10.1007/s41324-016-0059-1
* Atluri, V., & Chun, S. A. (2004). An authorization model for geospatial data. *IEEE Transactions on Dependable and Secure Computing*, 1(4), 238–254. https://doi.org/10.1109/TDSC.2004.34
* Bertino, E., Catania, B., & Damiani, M. L. (2005). GEO-RBAC: A spatially aware RBAC. In *Proceedings of the 10th ACM Symposium on Access Control Models and Technologies (SACMAT '05)* (pp. 29–37). Association for Computing Machinery. https://doi.org/10.1145/1063979.1063985
* Chun, S. A., & Atluri, V. (2008). Geospatial database security. In H. Chen, T. S. Raghu, R. Ramesh, R. Sharman, & S. Chakravarty (Eds.), *Handbook of Database Security: Applications and Trends* (pp. 251–277). Springer. https://doi.org/10.1007/978-0-387-48533-1_11
* Clarke, J. (2012). *SQL Injection Attacks and Defense* (2nd ed.). Syngress / Elsevier.
* Crosby, S. A., & Wallach, D. S. (2003). Denial of service via algorithmic complexity attacks. In *Proceedings of the 12th USENIX Security Symposium* (pp. 29–44). USENIX Association.
* Egenhofer, M. J. (1994). Spatial SQL: A query and presentation language. *IEEE Transactions on Knowledge and Data Engineering*, 6(1), 86–95. https://doi.org/10.1109/69.273029
* Halfond, W. G., Viegas, J., & Orso, A. (2006). A classification of SQL-injection attacks and countermeasures. In *Proceedings of the IEEE International Symposium on Secure Software Engineering (ISSSE '06)*. IEEE.
* Kara, A., Çağdaş, V., Isikdag, U., van Oosterom, P., Lemmen, C., & Stubkjær, E. (2021). Towards the LADM Valuation Information Model: A case study in Turkey. *Land Use Policy*, 109, 105658. https://doi.org/10.1016/j.landusepol.2021.105658
* Lemmen, C., van Oosterom, P., & Bennett, R. (2015). The Land Administration Domain Model. *Land Use Policy*, 49, 535–545. https://doi.org/10.1016/j.landusepol.2015.01.014
* National Vulnerability Database. (2023). *CVE-2023-25157 Detail: GeoServer SQL Injection Vulnerability*. National Institute of Standards and Technology. https://nvd.nist.gov/vuln/detail/CVE-2023-25157
* Obe, R. O., & Hsu, L. S. (2021). *PostGIS in Action* (3rd ed.). Manning Publications.
* OWASP Foundation. (2021). *OWASP Top 10:2021 - The Ten Most Critical Web Application Security Risks*. Open Web Application Security Project. https://owasp.org/Top10/
* OWASP Foundation. (2023). *Web Security Testing Guide (WSTG v4.2)*. Open Web Application Security Project. https://owasp.org/www-project-web-security-testing-guide/
* van Oosterom, P., Lemmen, C., & Ingvarsson, T. (2006). The core cadastral domain model. *Computers, Environment and Urban Systems*, 30(5), 627–660. https://doi.org/10.1016/j.compenvurbsys.2005.12.002

**This paper may be cited as:**  
Rodrigo, A. (2026). Evaluation of Spatial SQL Injection Vulnerabilities in PostGIS-Based Cadastral Information Systems. *International Multidisciplinary Journal of Emerging Technologies and Applications*, 1(1), 1–8. https://imjeta.org/index.php/IMJETA/libraryFiles/downloadPublic/1

---

## Appendix 1

**Research Instrument: Experimental Battery of Spatial SQL Injection Vectors**

| Test Vector | Evaluated Endpoint | Representative Payload | CIA Dimension and Effect |
| :--- | :--- | :--- | :--- |
| **1. Logic Bypass** | `GET /api/v1/vulnerable/predios/radio` | `50) OR 1=1 --` | **Confidentiality:** Exfiltration of parcels from restricted sectors. |
| **2. Blind Side-Channel** | `GET /api/v1/vulnerable/predios/poligono` | `POLYGON(...) AND 1=(CASE WHEN ... THEN CAST(ST_GeomFromText('ERR') AS INT) ELSE 1 END)` | **Confidentiality:** Character-by-character extraction of credential hashes. |
| **3. Algorithmic DoS** | `GET /api/v1/vulnerable/predios/analisis-expansion` | `10 + (SELECT COUNT(*) FROM tg_lote a CROSS JOIN ... ST_Buffer(..., 100))` | **Availability:** Combinatorial $O(N^2)$ explosion, CPU core saturation. |
| **4. Cadastral Tampering** | `POST /api/v1/vulnerable/ficha/modificar` | `id_lote = '21010101000000', nuevo_autovaluo = 0, nuevo_titular = 'HACKER'` | **Integridad:** Fiscal assessment alteration and ownership hijacking. |
| **5. Massive Deletion** | `DELETE /api/v1/vulnerable/predios/borrar` | `filtro_sector = '0101' OR '1'='1'` | **Integrity & Availability:** Unconditional deletion of 487 cadastral parcels. |
| **6. Auth Bypass** | `POST /api/v1/vulnerable/auth/login` | `username = admin' --` | **Confidentiality & Integrity:** Privilege escalation to `superadmin_catastro`. |

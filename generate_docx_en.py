import docx
from docx import Document
from docx.shared import Pt, Inches, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement, parse_xml
from docx.oxml.ns import nsdecls, qn

def create_imjeta_doc_en():
    template_path = "Template_IMJETA_2026-OTH.docx"
    doc = Document(template_path)

    # Clean template paragraphs starting from paragraph 4 (keep journal headers p0 to p3)
    # p[0]: Journal Name
    # p[1]: Vol, No, pp
    # p[2]: Received, Revised, Accepted
    # p[3]: Published
    total_p = len(doc.paragraphs)
    for i in range(total_p - 1, 3, -1):
        p = doc.paragraphs[i]
        p._p.getparent().remove(p._p)

    # Remove example tables
    for t in doc.tables:
        t._tbl.getparent().remove(t._tbl)

    def set_font(run, name="Book Antiqua", size=11, bold=False, italic=False, color=RGBColor(0,0,0)):
        run.font.name = name
        run.font.size = Pt(size)
        run.bold = bold
        run.italic = italic
        run.font.color.rgb = color

    # 1. ARTICLE TITLE (Size 18 Bold)
    p_title = doc.add_paragraph()
    p_title.alignment = WD_ALIGN_PARAGRAPH.LEFT
    p_title.paragraph_format.space_before = Pt(12)
    p_title.paragraph_format.space_after = Pt(12)
    r_title = p_title.add_run("Evaluation of Spatial SQL Injection Vulnerabilities in PostGIS-Based Cadastral Information Systems")
    set_font(r_title, size=18, bold=True)

    # 2. AUTHORS AND AFFILIATION
    p_author = doc.add_paragraph()
    p_author.paragraph_format.space_after = Pt(4)
    r_author = p_author.add_run("Rodrigo Surname1[0000-0002-XXXX-XXXX]")
    set_font(r_author, size=11, bold=True)

    p_affil = doc.add_paragraph()
    p_affil.paragraph_format.space_after = Pt(2)
    r_affil = p_affil.add_run("1National University / Doctoral Program in Cybersecurity")
    set_font(r_affil, size=10, italic=True)

    p_email = doc.add_paragraph()
    p_email.paragraph_format.space_after = Pt(12)
    r_email = p_email.add_run("investigador.catastro@doctorado.edu.pe")
    set_font(r_email, size=10)

    # 3. ABSTRACT (Size 10, Book Antiqua, 0.5 inches margin indent)
    p_abs = doc.add_paragraph()
    p_abs.paragraph_format.left_indent = Inches(0.5)
    p_abs.paragraph_format.right_indent = Inches(0.5)
    p_abs.paragraph_format.space_after = Pt(6)
    p_abs.paragraph_format.line_spacing = 1.0
    
    r_abs_bold = p_abs.add_run("Abstract. ")
    set_font(r_abs_bold, size=10, bold=True)

    abstract_text = (
        "The integration of spatial databases into web architectures has expanded the attack surface for modern "
        "applications; however, the specific risks associated with spatial SQL injections remain largely underexplored. "
        "This paper investigates the exploitation and mitigation of spatial SQL injections within cadastral information "
        "systems utilizing PostGIS. A containerized testbed was developed using Docker to simulate a critical infrastructure "
        "API built with Python (FastAPI) and PostgreSQL/PostGIS. The study demonstrates how attackers can leverage spatial "
        "functions (e.g., ST_DWithin, ST_Intersects) to manipulate geospatial logic, exfiltrate unauthorized zoning data, or "
        "induce denial-of-service states. Furthermore, the research evaluates the performance impact of implementing robust "
        "mitigation strategies, comparing vulnerable dynamic spatial queries with parameterized queries executed via "
        "Object-Relational Mapping (ORM) tools such as SQLAlchemy and GeoAlchemy2. Results demonstrate that the proposed "
        "pipeline neutralized 100% of the attack vectors with a mean latency overhead of 2.63 ms (+15.24%) and a "
        "12.59% improvement in tail stability (p99). We conclude that effective spatial injection mitigation relies on enforcing "
        "in-memory topological validation and rigid ORM parameterization at the application layer, "
        "securing cadastral integrity with minimal operational overhead."
    )
    r_abs_body = p_abs.add_run(abstract_text)
    set_font(r_abs_body, size=10)

    # 4. KEYWORDS
    p_kw = doc.add_paragraph()
    p_kw.paragraph_format.left_indent = Inches(0.5)
    p_kw.paragraph_format.right_indent = Inches(0.5)
    p_kw.paragraph_format.space_after = Pt(14)
    r_kw_bold = p_kw.add_run("Keywords: ")
    set_font(r_kw_bold, size=10, bold=True)
    r_kw_body = p_kw.add_run("Spatial injections; Cadastral systems; Geospatial cybersecurity; Penetration testing; Databases")
    set_font(r_kw_body, size=10)

    # Helper functions
    def add_heading_1(text):
        p = doc.add_paragraph()
        p.paragraph_format.space_before = Pt(12)
        p.paragraph_format.space_after = Pt(4)
        p.paragraph_format.keep_with_next = True
        r = p.add_run(text)
        set_font(r, size=12, bold=True)
        return p

    def add_heading_2(text):
        p = doc.add_paragraph()
        p.paragraph_format.space_before = Pt(8)
        p.paragraph_format.space_after = Pt(3)
        p.paragraph_format.keep_with_next = True
        r = p.add_run(text)
        set_font(r, size=11, bold=True)
        return p

    def add_run_in(bold_title, text, indent=False):
        p = doc.add_paragraph()
        p.paragraph_format.space_after = Pt(4)
        p.paragraph_format.line_spacing = 1.0
        if indent:
            p.paragraph_format.first_line_indent = Inches(0.3)
        r_bold = p.add_run(bold_title + " ")
        set_font(r_bold, size=11, bold=True)
        r_text = p.add_run(text)
        set_font(r_text, size=11)
        return p

    def add_p(text, indent=False):
        p = doc.add_paragraph()
        p.paragraph_format.space_after = Pt(4)
        p.paragraph_format.line_spacing = 1.0
        if indent:
            p.paragraph_format.first_line_indent = Inches(0.3)
        r = p.add_run(text)
        set_font(r, size=11)
        return p

    def add_figure(image_path, caption_text, width_inches=5.8):
        p_img = doc.add_paragraph()
        p_img.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p_img.paragraph_format.space_before = Pt(8)
        p_img.paragraph_format.space_after = Pt(2)
        p_img.paragraph_format.keep_with_next = True
        r_img = p_img.add_run()
        r_img.add_picture(image_path, width=Inches(width_inches))

        p_cap = doc.add_paragraph()
        p_cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p_cap.paragraph_format.space_before = Pt(6)
        p_cap.paragraph_format.space_after = Pt(8)
        r_cap = p_cap.add_run(caption_text)
        set_font(r_cap, size=10, bold=True)
        return p_cap

    # SECTION 1: INTRODUCTION
    add_heading_1("1. Introduction")
    add_p(
        "Modern cadastral information systems expose web services and spatial geoportals over client-server architectures "
        "to administer land tenure, municipal zoning, and property taxation (Lemmen et al., 2015). Within this operational domain, "
        "PostgreSQL along with its PostGIS spatial extension represents the predominant open-source solution for storing and querying "
        "official vector cartography (Obe & Hsu, 2021)."
    )
    add_p(
        "However, exposing these spatial data services via REST APIs introduces attack vectors whenever queries are constructed through "
        "string concatenation within spatial functions. While classical SQL injection and its risks in web applications have been "
        "extensively documented (Clarke, 2012; Halfond et al., 2006; OWASP Foundation, 2021), manipulating PostGIS geometric operators—such as "
        "ST_DWithin, ST_Intersects, or ST_Buffer—exhibits distinct mechanics: unsanitized input not only circumvents relational filters or "
        "exfiltrates records, but also triggers denial-of-service conditions through topological calculations of high algorithmic complexity.",
        indent=True
    )
    add_p(
        "This article presents an experimental evaluation of spatial SQL injection vulnerabilities in PostGIS-based cadastral "
        "systems. The study: (1) documents and evaluates six attack vectors mapped to the CIA triad (Confidentiality, Integrity, "
        "and Availability); (2) implements a reproducible testbed over an experimental dataset of 1,500 urban parcels structured under "
        "the ISO 19152 (LADM) standard; and (3) quantifies the latency and throughput impact of a mitigation architecture combining "
        "strongly typed ORM compilation (GeoAlchemy2) with pre-execution validation via Shapely and Pydantic.",
        indent=True
    )

    # SECTION 2: RELATED WORK
    add_heading_1("2. Related Work")
    add_heading_2("2.1. Spatial SQL Injections and Topological Operators")
    add_p(
        "Seminal literature in computer security has established robust taxonomies for SQLi attacks. Halfond et al. (2006) "
        "categorized these threats into tautologies, union queries, blind injections, and stored procedure piggybacking. Clarke (2012) "
        "expanded upon this by examining the abstract syntax trees (AST) generated by database parsers when unsanitized parameters are "
        "concatenated. However, these classical frameworks fail to account for how spatial algebraic operators (Egenhofer, 1994) "
        "redefine logical evaluation conditions. Unlike scalar values, a geometric expression processes multiple dimensions, "
        "spatial reference system identifiers (SRID), and minimum bounding boxes, significantly expanding the syntactic escape surface. "
        "This theoretical gap in classical injection models leaves topological predicate manipulation in spatial relational engines unaddressed."
    )

    add_heading_2("2.2. Geospatial Access Control Models and Spatial Inference Breaches")
    add_p(
        "Access control in spatial databases was formally conceptualized by Bertino et al. (2005) through the GEO-RBAC (Spatially Aware "
        "Role-Based Access Control) model, demonstrating that read and write privileges must be dynamically subordinated to geographic boundaries. "
        "Complementarily, Chun and Atluri (2008) and Atluri and Chun (2004) investigated spatial inference risks in SDBMS, where unauthorized "
        "actors deduce the presence or attributes of protected spatial entities by correlating successive queries. Nevertheless, these approaches "
        "assume that the application layer faithfully projects spatial policies to persistence; in modern web architectures, unsafe concatenation "
        "directly nullifies persistence-tier access controls without detection by application-tier authorization mechanisms."
    )

    add_heading_2("2.3. Cadastral Integrity and Data Modeling under ISO 19152 (LADM)")
    add_p(
        "The technical modeling of cadastral information systems is governed internationally by the ISO 19152:2012 standard, known as the "
        "Land Administration Domain Model (LADM). Foundational works by Lemmen et al. (2015) and van Oosterom et al. (2006) formalized core "
        "cadastral entities, prominently LA_SpatialUnit (parcels and lots) and LA_Party (property owners), subsequently extended toward "
        "automated mass valuation models (Kara et al., 2021). While the standard prescribes the semantics and interoperability of territorial "
        "and registry data, it omits query-level architectural safeguards against SQL injection attacks, leaving fiscal revenue and title tenure "
        "integrity exposed to software implementation flaws."
    )

    add_heading_2("2.4. Algorithmic Complexity Attacks and Vulnerabilities in OGC Services")
    add_p(
        "The contemporary relevance of this threat was acutely illustrated in the software industry by critical vulnerability "
        "CVE-2023-25157 (CVSS score 9.8), wherein the reference software GeoServer allowed unauthenticated remote SQL injection via flawed "
        "evaluation of OGC filters and CQL expressions over PostGIS backends (National Vulnerability Database, 2023). In parallel, regarding "
        "denial of service, Crosby and Wallach (2003) established the paradigm of Algorithmic Complexity Attacks, demonstrating how engineered "
        "inputs can force worst-case execution paths (O(N^2)) to monopolize CPU resources. In spatial engines, as documented by Agarwal and Rajan "
        "(2016), computational geometry algorithms in PostGIS's underlying GEOS library exhibit quadratic computational overhead when evaluating "
        "complex polygons devoid of preliminary GiST spatial index filtering. Despite these precedents, the literature has neither quantified "
        "the resulting latency profiles nor formalized multi-tier defense schemes integrating API parsers with geometric engines."
    )

    # SECTION 3: METHODOLOGY
    add_heading_1("3. Methodology")
    add_heading_2("3.1. Research Approach and Experimental Framework")
    add_p(
        "A quantitative, experimental design was adopted to evaluate the susceptibility of geospatial endpoints to SQL injections "
        "and measure the performance impact introduced by a multi-tier mitigation scheme. The evaluation compares two conditions: "
        "unprotected dynamic SQL queries versus ORM-compiled queries with prior geometric validation."
    )

    add_heading_2("3.2. Cadastral Dataset")
    add_p(
        "The experimental dataset comprises 1,500 contiguous urban cadastral parcels structured under the ISO 19152 standard "
        "(LADM, LA_SpatialUnit class) and georeferenced in EPSG:32719. The geometries exhibit a complexity ranging between 4 and 222 "
        "vertices (mean: 9.0 vertices per polygon). To ensure reproducibility and ethical safeguards, base cartography was retrieved "
        "from open sources and fiscal attributes were procedurally generated without incorporating personally identifiable information (PII)."
    )

    add_heading_2("3.3. Experimental Environment and Architecture")
    add_p(
        "The testbed was implemented in Docker containers using isolated microservices: (1) a database service running PostgreSQL 15 and "
        "PostGIS 3.3, and (2) a Python 3.11 API with FastAPI and Uvicorn. Stress testing was executed in a controlled 14-core 5.2 GHz "
        "environment with 32 GB DDR5 RAM on Linux kernel 6.6 (WSL2)."
    )

    add_heading_2("3.4. Test Vectors and Performance Metrics")
    add_p(
        "Six exploitation vectors based on the injection testing guidelines of the Web Security Testing Guide (OWASP Foundation, 2023), "
        "targeting the three dimensions of the CIA triad (Confidentiality, Integrity, and Availability, summarized in Appendix 1), "
        "were structured. Performance evaluation encompassed a 300-request load test and stepped concurrency curves (1 to 100 clients), "
        "recording latency metrics (mean, p50, p95, p99) and throughput (req/s)."
    )

    # SECTION 4: ATTACK SIMULATIONS
    add_heading_1("4. Attack Simulations and Exploitation Results")
    add_heading_2("4.1. Simulation 1: Spatial Logic Bypass")
    add_p(
        "The endpoint GET /api/v1/vulnerable/predios/radio is designed to return cadastral lots within a 50-meter radius restricted strictly "
        "to sector 0101. By injecting the payload '50) OR (1=1' into the distance parameter, the lexical parser of PostgreSQL prematurely "
        "closes the ST_DWithin operator and introduces a tautology that nullifies both the spatial radius and territorial sector filters. "
        "As a result, the query transitioned from returning 1 authorized parcel to exfiltrating 50 unauthorized cadastral parcels in 7.03 ms. "
        "In the mitigated endpoint, Pydantic and GeoAlchemy2 strictly enforced numerical type boundaries, neutralizing the attack with HTTP 422."
    )

    add_heading_2("4.2. Simulation 2: Data Inference via Geometric Error Channels (Error-Based Spatial SQLi)")
    add_p(
        "In the endpoint GET /api/v1/vulnerable/predios/poligono, the application renders cartographic polygons without exposing textual data. "
        "The attacker structured an inferential side-channel coupled to the ST_Intersects operator, injecting a conditional division by zero "
        "dependent on character guesses against the administrative table: if the guessed character matches, PostGIS raises a runtime exception "
        "triggering an HTTP 500 error; if false, the engine responds with HTTP 200. Through this mechanism, the full administrative credential "
        "'admin' was exfiltrated in 42 seconds. In the mitigated version, Shapely evaluated topological validity in application memory, "
        "rejecting the malicious syntax with HTTP 422."
    )

    add_heading_2("4.3. Simulation 3: Spatial Denial of Service (Spatial DoS)")
    add_p(
        "Leveraging the baseline geometric complexity of cadastral parcels (averaging 9.0 vertices and up to 222 vertices per polygon), "
        "the attacker injected a subquery with an O(N^2) spatial Cartesian product into the endpoint GET /api/v1/vulnerable/predios/analisis-expansion, "
        "computing buffers with high segment densities per quadrant. As empirically evidenced in Figure 1, injecting the Cartesian product "
        "triggers an O(N^2) algorithmic complexity explosion that escalates latency from 10.8 ms up to 1,665.16 ms as evaluated buffer vertices "
        "expand from 14,400 to over 345,600 points, saturating PostgreSQL worker threads on the multi-core workstation. Conversely, the "
        "mitigated architecture reliably preserves a bounded latency of ~15 ms by constraining parameters to validated scalar ranges via "
        "Pydantic and GeoAlchemy2."
    )
    add_figure("figures/fig3_spatial_dos_complexity.png", "Figure 1. Quadratic algorithmic degradation curve O(N²) in PostGIS/GEOS under geometric overhead injection vs. bounded mitigation", width_inches=5.4)

    add_heading_2("4.4. Simulation 4: Cadastral Record Tampering (Tax Assessment Manipulation)")
    add_p(
        "In the endpoint POST /api/v1/vulnerable/ficha/modificar, an attack against fiscal integrity was simulated. Through concatenation "
        "in the SET clause, the attacker manipulated the tax assessment setting it to S/ 0.00 and replaced the legitimate property owner "
        "with an unauthorized third party, proving the vulnerability of fiscal databases to direct update injections. The mitigated endpoint "
        "blocked the fraud via alphabetic regular expressions and positive range constraints in SQLAlchemy (HTTP 422)."
    )

    add_heading_2("4.5. Simulation 5: Bulk Deletion of Cadastral Records (Data Destruction)")
    add_p(
        "In the endpoint DELETE /api/v1/vulnerable/predios/borrar, injecting the literal payload '0101' OR '1'='1' into the sector filter "
        "transformed the command into an unconditional record deletion (DELETE FROM tg_lote WHERE cod_sector = '0101' OR '1'='1'), purging "
        "all 1,500 parcels and leaving the web viewer devoid of cartography. In contrast, the mitigated endpoint validated the sector parameter "
        "using the strict regex pattern ^\\d{4}$, rejecting the injection with HTTP 422 and preserving the cadastral repository intact."
    )

    add_heading_2("4.6. Simulation 6: Authentication Bypass in the Cadastral Web Viewer")
    add_p(
        "In the endpoint POST /api/v1/vulnerable/auth/login, the attacker entered \"admin' --\" in the username field, commenting out password "
        "hash verification. The API granted immediate access and issued a token with the superadmin_catastro role. The mitigated version "
        "featuring prepared statements and SHA-256 cryptographic hashing neutralized the bypass by searching literally for the quoted string "
        "without evaluating it as SQL syntax."
    )

    # SECTION 5: MITIGATION AND EVALUATION
    add_heading_1("5. Mitigation Strategies and Performance Evaluation")
    add_p(
        "As illustrated in Figure 2, the architectural mitigation integrated a three-barrier defense-in-depth pipeline: "
        "(1) Barrier 1 with Pydantic for strict typing and physical boundary constraints; (2) Barrier 2 with Shapely for topological "
        "validation and early rejection of degenerate geometries in application memory (returning HTTP 422 prior to database interaction); "
        "and (3) Barrier 3 with GeoAlchemy2 and SQLAlchemy for native compilation using binary bind variables (EWKB) and execution plan reuse "
        "(prepared statements)."
    )
    add_figure("figures/fig1_defense_pipeline.png", "Figure 2. Architecture of the 3-barrier defense-in-depth pipeline for PostGIS cadastral services", width_inches=5.8)

    add_p(
        "A comparative benchmark of 300 requests under 10 concurrent clients was conducted between the vulnerable API and the mitigated API. "
        "Results are summarized in Table 1.",
        indent=True
    )

    # TABLE 1 (IMJETA Format: Centered bold label above table, size 10)
    p_tlabel = doc.add_paragraph()
    p_tlabel.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_tlabel.paragraph_format.space_before = Pt(8)
    p_tlabel.paragraph_format.space_after = Pt(4)
    r_tl = p_tlabel.add_run("Table 1: Performance and Latency Comparison between Vulnerable API and Mitigated API")
    set_font(r_tl, size=10, bold=True)

    table_data = [
        ["Performance Metric", "Vulnerable API (Dynamic SQL)", "Mitigated API (GeoAlchemy2)", "Variance (Overhead)"],
        ["Throughput", "556.21 req/s", "484.36 req/s", "-71.85 req/s (-12.92%)"],
        ["Mean Latency", "17.26 ms", "19.89 ms", "+2.63 ms (+15.24%)"],
        ["50th Percentile (Median / p50)", "15.37 ms", "18.42 ms", "+3.05 ms"],
        ["95th Percentile (p95)", "31.49 ms", "32.63 ms", "+1.14 ms"],
        ["99th Percentile (p99)", "43.75 ms", "38.24 ms", "-5.51 ms (-12.59%)"],
        ["Error Rate", "0.0%", "0.0%", "0.0%"]
    ]

    tbl = doc.add_table(rows=len(table_data), cols=4)
    tbl.alignment = docx.enum.table.WD_TABLE_ALIGNMENT.CENTER
    for r_idx, row in enumerate(table_data):
        for c_idx, val in enumerate(row):
            cell = tbl.cell(r_idx, c_idx)
            cell.text = val
            p_cell = cell.paragraphs[0]
            p_cell.paragraph_format.space_before = Pt(2)
            p_cell.paragraph_format.space_after = Pt(2)
            p_cell.alignment = WD_ALIGN_PARAGRAPH.LEFT if c_idx == 0 else WD_ALIGN_PARAGRAPH.CENTER
            run_c = p_cell.runs[0]
            set_font(run_c, size=10, bold=(r_idx == 0))

    p_tnote = doc.add_paragraph()
    p_tnote.paragraph_format.space_before = Pt(4)
    p_tnote.paragraph_format.space_after = Pt(8)
    r_tnote = p_tnote.add_run("Note: Empirical measurements gathered under 300 concurrent requests (concurrency=10) on a multi-core workstation with 32 GB DDR5 RAM in Docker Desktop (PostgreSQL 15 / PostGIS 3.3).")
    set_font(r_tnote, size=9, italic=True)

    add_p(
        "To characterize resilience under progressive stress, a multi-tier concurrency benchmark spanning 1 to 100 concurrent clients "
        "was executed. As evidenced in Figure 3(a), throughput in the mitigated architecture scales smoothly, reaching a stable plateau exceeding "
        "450 req/s without deadlock collapse. Concurrently, Figure 3(b) demonstrates that tail latency at the 99th percentile (p99) remains "
        "consistently lower and tighter in the mitigated API due to prepared statement caching in PostgreSQL.",
        indent=True
    )
    add_figure("figures/fig2_concurrency_latency.png", "Figure 3. Empirical throughput and latency percentiles (p50 and p99) comparison under scaled concurrency (1 to 100 clients)", width_inches=5.8)

    # SECTION 6: DISCUSSION
    add_heading_1("6. Discussion")
    add_p(
        "The empirical results demonstrate that mitigation based on GeoAlchemy2 and pre-execution validation with Shapely introduces a mean "
        "latency overhead of merely 2.63 milliseconds per request (+15.24%), sustaining a throughput of 484.36 requests per second. "
        "Particularly noteworthy is the reduction in tail latency at the 99th percentile (p99), which dropped from 43.75 ms to 38.24 ms "
        "(-12.59%), an optimization directly attributed to efficient reuse of compiled execution plans (prepared statements) in PostgreSQL by "
        "eliminating continuous re-parsing of dynamic queries. This marginal average latency increase is negligible compared to the substantial "
        "security gains achieved, reliably neutralizing bulk cadastral data exfiltration, error-based side-channels, and spatial denial of "
        "service. It is concluded that mitigating spatial payloads requires spatially aware syntactic and topological "
        "validation mechanisms embedded directly within application code."
    )
    add_p(
        "In contrast to the unprotected vulnerable architecture (where 100% of the attacks succeed), the three-barrier pipeline achieves "
        "a complete 100% blocking rate across all evaluated vectors of the CIA triad.",
        indent=True
    )
    add_run_in(
        "Platform independence and benchmarking validity.",
        "While absolute latency metrics were acquired on a modern multi-core workstation, the methodological validity and generalizability "
        "of the findings reside in the relative proportions (+15.24% mean overhead and -12.59% p99 tail improvement) and in computational "
        "asymptotic complexities. On municipal servers or cloud instances with restricted hardware resources (common in local government "
        "environments), the computational cost of Python preprocessing (GeoAlchemy2/Shapely) remains negligible relative to dominant disk I/O "
        "and relational concurrency bottlenecks. Conversely, the absence of defenses against algorithmic complexity attacks (O(N^2)) such as "
        "Spatial DoS (Simulation 3) proves critical on entry-level processors with lower parallelism, where a small number of malicious queries "
        "can immediately incapacitate the entire cadastral service.",
        indent=True
    )
    add_run_in(
        "Systemic impact on the integrity of cadastral procedures and records.",
        "The empirical feasibility of Simulation 4 (tampering with property valuation and ownership via direct injection) illustrates how a "
        "persistence-level failure transcends single-table corruption and compromises the validity of municipal e-government operations. "
        "When cadastral systems interoperate autonomously to issue cryptographic QR-verified cadastral certificates, tax clearance "
        "certificates, or property conveyance deeds under ISO 19152 LADM, injecting arbitrary data into catastro_titulares and tg_lote "
        "propagates fiscal and registry inconsistencies without triggering UI-tier alerts, confirming that strongly typed ORM sanitization "
        "is an indispensable safeguard for the reliability of digital public services.",
        indent=True
    )

    # SECTION 7: CONCLUSIONS (IMJETA: Single paragraph between 175 and 300 words)
    add_heading_1("7. Conclusions and Recommendations")
    add_p(
        "This article formalized and empirically demonstrated the viability of six spatial SQL injection vectors targeting the CIA triad "
        "(Confidentiality, Integrity, and Availability) in PostGIS-based cadastral information systems, proving that native topological "
        "functions offer no data isolation guarantees when constructed via string concatenation. Experimental evaluation over a dataset of "
        "1,500 cadastral parcels structured under the ISO 19152 (LADM) standard confirmed that unauthenticated adversaries can bypass "
        "territorial boundaries, reconstruct credentials through geometric error side-channels, induce denial of service via quadratic "
        "algorithmic overhead, tamper with fiscal property records, and execute bulk cartographic deletions. In response, the defense-in-depth "
        "architecture based on typed ORM compilation (GeoAlchemy2), rigid typing with Pydantic, and in-memory pre-validation with Shapely "
        "successfully mitigated 100% of the evaluated exploitation scenarios. Transactional benchmarking demonstrated that this scheme introduces "
        "a mean latency overhead of only 2.63 ms (+15.24%), while simultaneously enhancing 99th-percentile stability by 12.59% through execution "
        "plan reuse in PostgreSQL. In conclusion, securing cadastral infrastructures requires abandoning traditional scalar sanitization "
        "paradigms in favor of ORM parameterization and spatially aware syntactic controls integrated from the foundational software "
        "architecture design."
    )

    # SECTION 8: REFERENCES (APA 7th, 0.5 inches hanging indent)
    add_heading_1("8. References")
    
    references = [
        "Agarwal, S., & Rajan, K. S. (2016). Performance analysis of MongoDB versus PostGIS/PostgreSQL databases for line intersection and point containment spatial queries. Spatial Information Research, 24(6), 669–677. https://doi.org/10.1007/s41324-016-0059-1",
        "Atluri, V., & Chun, S. A. (2004). An authorization model for geospatial data. IEEE Transactions on Dependable and Secure Computing, 1(4), 238–254. https://doi.org/10.1109/TDSC.2004.34",
        "Bertino, E., Catania, B., & Damiani, M. L. (2005). GEO-RBAC: A spatially aware RBAC. In Proceedings of the 10th ACM Symposium on Access Control Models and Technologies (SACMAT '05) (pp. 29–37). Association for Computing Machinery. https://doi.org/10.1145/1063979.1063985",
        "Chun, S. A., & Atluri, V. (2008). Geospatial database security. In H. Chen, T. S. Raghu, R. Ramesh, R. Sharman, & S. Chakravarty (Eds.), Handbook of Database Security: Applications and Trends (pp. 251–277). Springer. https://doi.org/10.1007/978-0-387-48533-1_11",
        "Clarke, J. (2012). SQL Injection Attacks and Defense (2nd ed.). Syngress / Elsevier.",
        "Crosby, S. A., & Wallach, D. S. (2003). Denial of service via algorithmic complexity attacks. In Proceedings of the 12th USENIX Security Symposium (pp. 29–44). USENIX Association.",
        "Egenhofer, M. J. (1994). Spatial SQL: A query and presentation language. IEEE Transactions on Knowledge and Data Engineering, 6(1), 86–95. https://doi.org/10.1109/69.273029",
        "Halfond, W. G., Viegas, J., & Orso, A. (2006). A classification of SQL-injection attacks and countermeasures. In Proceedings of the IEEE International Symposium on Secure Software Engineering (ISSSE '06). IEEE.",
        "Kara, A., Çağdaş, V., Isikdag, U., van Oosterom, P., Lemmen, C., & Stubkjær, E. (2021). Towards the LADM Valuation Information Model: A case study in Turkey. Land Use Policy, 109, 105658. https://doi.org/10.1016/j.landusepol.2021.105658",
        "Lemmen, C., van Oosterom, P., & Bennett, R. (2015). The Land Administration Domain Model. Land Use Policy, 49, 535–545. https://doi.org/10.1016/j.landusepol.2015.01.014",
        "National Vulnerability Database. (2023). CVE-2023-25157 Detail: GeoServer SQL Injection Vulnerability. National Institute of Standards and Technology. https://nvd.nist.gov/vuln/detail/CVE-2023-25157",
        "Obe, R. O., & Hsu, L. S. (2021). PostGIS in Action (3rd ed.). Manning Publications.",
        "OWASP Foundation. (2021). OWASP Top 10:2021 - The Ten Most Critical Web Application Security Risks. Open Web Application Security Project. https://owasp.org/Top10/",
        "OWASP Foundation. (2023). Web Security Testing Guide (WSTG v4.2). Open Web Application Security Project. https://owasp.org/www-project-web-security-testing-guide/",
        "van Oosterom, P., Lemmen, C., & Ingvarsson, T. (2006). The core cadastral domain model. Computers, Environment and Urban Systems, 30(5), 627–660. https://doi.org/10.1016/j.compenvurbsys.2005.12.002"
    ]

    for ref in sorted(references, key=str.casefold):
        p_ref = doc.add_paragraph()
        p_ref.paragraph_format.left_indent = Inches(0.5)
        p_ref.paragraph_format.first_line_indent = Inches(-0.5)
        p_ref.paragraph_format.space_after = Pt(4)
        p_ref.paragraph_format.line_spacing = 1.0
        r_ref = p_ref.add_run(ref)
        set_font(r_ref, size=11)

    # Mandatory IMJETA clause: Citation of the article itself
    p_cite_intro = doc.add_paragraph()
    p_cite_intro.paragraph_format.space_before = Pt(12)
    p_cite_intro.paragraph_format.space_after = Pt(4)
    r_ci = p_cite_intro.add_run("This paper may be cited as:")
    set_font(r_ci, size=11, bold=True)

    p_cite = doc.add_paragraph()
    p_cite.paragraph_format.left_indent = Inches(0.5)
    p_cite.paragraph_format.first_line_indent = Inches(-0.5)
    p_cite.paragraph_format.space_after = Pt(12)
    r_cbody = p_cite.add_run("Rodrigo, A. (2026). Evaluation of Spatial SQL Injection Vulnerabilities in PostGIS-Based Cadastral Information Systems. International Multidisciplinary Journal of Emerging Technologies and Applications, 1(1), 1-8. https://imjeta.org/index.php/IMJETA/libraryFiles/downloadPublic/1")
    set_font(r_cbody, size=11)

    # APPENDIX 1 (New page as required by IMJETA template)
    doc.add_page_break()
    add_heading_1("Appendix 1")
    add_p(
        "Research Instrument: Experimental Battery of Spatial SQL Injection Vectors. "
        "The following table details the six exploitation vectors designed and executed to evaluate the security of the cadastral API:"
    )

    app_data = [
        ["Test Vector", "Evaluated Endpoint", "Representative Payload", "CIA Dimension and Effect"],
        ["1. Logic Bypass", "GET /api/v1/vulnerable/predios/radio", "50) OR 1=1 --", "Confidentiality: Exfiltration of parcels from restricted sectors."],
        ["2. Blind Side-Channel", "GET /api/v1/vulnerable/predios/poligono", "POLYGON(...) AND 1=(CASE WHEN ... THEN CAST(ST_GeomFromText('ERR') AS INT) ELSE 1 END)", "Confidentiality: Character-by-character extraction of credential hashes."],
        ["3. Algorithmic DoS", "GET /api/v1/vulnerable/predios/analisis-expansion", "10 + (SELECT COUNT(*) FROM tg_lote a CROSS JOIN ... ST_Buffer(..., 100))", "Availability: Combinatorial O(N^2) explosion, CPU core saturation."],
        ["4. Cadastral Tampering", "POST /api/v1/vulnerable/ficha/modificar", "id_lote = '21010101000000', nuevo_autovaluo = 0, nuevo_titular = 'HACKER'", "Integrity: Fiscal assessment alteration and ownership hijacking."],
        ["5. Massive Deletion", "DELETE /api/v1/vulnerable/predios/borrar", "filtro_sector = '0101' OR '1'='1'", "Integrity & Availability: Unconditional deletion of 1,500 cadastral parcels."],
        ["6. Auth Bypass", "POST /api/v1/vulnerable/auth/login", "username = admin' --", "Confidentiality & Integrity: Privilege escalation to superadmin_catastro."]
    ]

    tbl_app = doc.add_table(rows=len(app_data), cols=4)
    tbl_app.alignment = docx.enum.table.WD_TABLE_ALIGNMENT.CENTER
    for r_idx, row in enumerate(app_data):
        for c_idx, val in enumerate(row):
            cell = tbl_app.cell(r_idx, c_idx)
            cell.text = val
            p_cell = cell.paragraphs[0]
            p_cell.paragraph_format.space_before = Pt(2)
            p_cell.paragraph_format.space_after = Pt(2)
            p_cell.alignment = WD_ALIGN_PARAGRAPH.LEFT
            run_c = p_cell.runs[0]
            set_font(run_c, size=9, bold=(r_idx == 0))

    out_path = "Articulo_Cientifico_IMJETA_FINAL_EN.docx"
    auto_path = "Articulo_Cientifico_IMJETA_FINAL_EN_Generado_Auto.docx"
    doc.save(auto_path)
    print(f"English document generated safely at: {auto_path}")
    try:
        doc.save(out_path)
        print(f"Final English document generated successfully at: {out_path}")
    except PermissionError:
        print(f"[AVISO] {out_path} está abierto en Word; se generó copia en {auto_path}")

if __name__ == "__main__":
    create_imjeta_doc_en()

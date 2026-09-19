import docx
from docx import Document
from docx.shared import Pt, Inches, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement, parse_xml
from docx.oxml.ns import nsdecls, qn

def create_imjeta_doc():
    template_path = "Template_IMJETA_2026-OTH.docx"
    doc = Document(template_path)

    # Limpiar párrafos de ejemplo a partir del título (párrafo 4)
    # Conservamos los encabezados de la revista (párrafos 0 a 3)
    # p[0]: Nombre de la revista
    # p[1]: Vol, No, pp
    # p[2]: Received, Revised, Accepted
    # p[3]: Published
    
    # Eliminamos desde el final hacia el párrafo 4
    total_p = len(doc.paragraphs)
    for i in range(total_p - 1, 3, -1):
        p = doc.paragraphs[i]
        p._p.getparent().remove(p._p)

    # También eliminamos tablas de ejemplo que hayan quedado
    for t in doc.tables:
        t._tbl.getparent().remove(t._tbl)

    def set_font(run, name="Book Antiqua", size=11, bold=False, italic=False, color=RGBColor(0,0,0)):
        run.font.name = name
        run.font.size = Pt(size)
        run.bold = bold
        run.italic = italic
        run.font.color.rgb = color

    # 1. TÍTULO DEL ARTÍCULO (Size 18 Bold)
    p_title = doc.add_paragraph()
    p_title.alignment = WD_ALIGN_PARAGRAPH.LEFT
    p_title.paragraph_format.space_before = Pt(12)
    p_title.paragraph_format.space_after = Pt(12)
    r_title = p_title.add_run("Evaluación de Vulnerabilidades de Inyección SQL Espacial en Sistemas de Información Catastral basados en PostGIS")
    set_font(r_title, size=18, bold=True)

    # 2. AUTORES Y AFILIACIÓN
    p_author = doc.add_paragraph()
    p_author.paragraph_format.space_after = Pt(4)
    r_author = p_author.add_run("Rodrigo Apellido1[0000-0002-XXXX-XXXX]")
    set_font(r_author, size=11, bold=True)

    p_affil = doc.add_paragraph()
    p_affil.paragraph_format.space_after = Pt(2)
    r_affil = p_affil.add_run("1Universidad Nacional / Programa de Doctorado en Ciberseguridad")
    set_font(r_affil, size=10, italic=True)

    p_email = doc.add_paragraph()
    p_email.paragraph_format.space_after = Pt(12)
    r_email = p_email.add_run("investigador.catastro@doctorado.edu.pe")
    set_font(r_email, size=10)

    # 3. RESUMEN / ABSTRACT (Size 10, Book Antiqua, 0.5 inches margin indent)
    p_abs = doc.add_paragraph()
    p_abs.paragraph_format.left_indent = Inches(0.5)
    p_abs.paragraph_format.right_indent = Inches(0.5)
    p_abs.paragraph_format.space_after = Pt(6)
    p_abs.paragraph_format.line_spacing = 1.0
    
    r_abs_bold = p_abs.add_run("Abstract. ")
    set_font(r_abs_bold, size=10, bold=True)

    abstract_text = (
        "La integración de bases de datos espaciales en arquitecturas web ha ampliado la superficie de "
        "ataque para las aplicaciones modernas; sin embargo, los riesgos específicos asociados a las inyecciones "
        "SQL espaciales siguen estando poco explorados. Este artículo investiga la explotación y mitigación de inyecciones "
        "SQL espaciales dentro de sistemas de información catastral que utilizan PostGIS. Se desarrolló un entorno de prueba "
        "en contenedores, utilizando Docker, para simular una API de infraestructura crítica construida con Python (FastAPI) y "
        "PostgreSQL/PostGIS. El estudio demuestra cómo los atacantes pueden aprovechar funciones espaciales (por ejemplo, "
        "ST_DWithin, ST_Intersects) para manipular la lógica geoespacial, extraer datos de zonificación no autorizados o "
        "inducir estados de denegación de servicio. Además, la investigación evalúa el impacto en el rendimiento al implementar "
        "estrategias de mitigación robustas, comparando consultas espaciales dinámicas vulnerables con consultas parametrizadas "
        "ejecutadas a través de herramientas de Mapeo Objeto-Relacional (ORM) como SQLAlchemy y GeoAlchemy2. Los resultados "
        "demuestran que el pipeline propuesto neutralizó el 100% de los vectores de ataque con un sobrecosto medio de latencia "
        "de 2.63 ms (+15.24%) y una mejora del 12.59% en la estabilidad de cola (p99). Se concluye que la mitigación efectiva "
        "de inyecciones espaciales no depende de cortafuegos perimetrales genéricos (WAF), sino de trasladar la validación topológica y la parametrización "
        "tipada a la capa de aplicación (ORM), garantizando la integridad catastral con un impacto operativo marginal."
    )
    r_abs_body = p_abs.add_run(abstract_text)
    set_font(r_abs_body, size=10)

    # 4. PALABRAS CLAVE / KEYWORDS
    p_kw = doc.add_paragraph()
    p_kw.paragraph_format.left_indent = Inches(0.5)
    p_kw.paragraph_format.right_indent = Inches(0.5)
    p_kw.paragraph_format.space_after = Pt(14)
    r_kw_bold = p_kw.add_run("Keywords: ")
    set_font(r_kw_bold, size=10, bold=True)
    r_kw_body = p_kw.add_run("Inyecciones espaciales; Sistemas catastrales; Ciberseguridad geoespacial; Pruebas de penetración; Bases de datos")
    set_font(r_kw_body, size=10)

    # Helper para encabezados y texto normal
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

    # SECCIÓN 1: INTRODUCCIÓN
    add_heading_1("1. Introducción")
    add_p(
        "Los sistemas de información catastral modernos exponen servicios web y geoportales sobre arquitecturas cliente-servidor "
        "para administrar la propiedad predial, la zonificación urbana y la recaudación fiscal (Lemmen et al., 2015). En este ámbito, "
        "PostgreSQL junto a su extensión espacial PostGIS constituyen la solución de código abierto predominante para la persistencia "
        "y consulta de cartografía vectorial oficial (Obe & Hsu, 2021)."
    )
    add_p(
        "Sin embargo, la exposición de estos servicios mediante APIs REST introduce vectores de ataque cuando las consultas se construyen "
        "mediante concatenación de cadenas dentro de funciones espaciales. Si bien la inyección SQL clásica ha sido ampliamente documentada "
        "(Clarke, 2012; Halfond et al., 2006; OWASP Foundation, 2021), la manipulación de operadores geométricos de PostGIS —como ST_DWithin, ST_Intersects o "
        "ST_Buffer— presenta particularidades poco atendidas: una entrada no saneada no solo permite eludir filtros relacionales o exfiltrar "
        "datos, sino también desencadenar estados de denegación de servicio mediante cálculos topológicos de alta complejidad algorítmica.",
        indent=True
    )
    add_p(
        "Este artículo presenta una evaluación experimental de vulnerabilidades de inyección SQL espacial en sistemas catastrales sobre "
        "PostGIS. El estudio: (1) documenta y evalúa seis vectores de ataque orientados a la tríada CIA (Confidencialidad, Integridad y Disponibilidad); "
        "(2) implementa un banco de pruebas reproducible sobre un dataset de 487 parcelas urbanas estructuradas bajo el estándar ISO 19152 (LADM); "
        "y (3) cuantifica el impacto en latencia y throughput de una arquitectura de mitigación basada en compilación tipada en ORM (GeoAlchemy2) "
        "y validación previa con Shapely y Pydantic.",
        indent=True
    )

    # SECCIÓN 2: TRABAJOS RELACIONADOS
    add_heading_1("2. Trabajos Relacionados")
    add_heading_2("2.1. Inyección SQL en Motores Espaciales y Operadores Topológicos")
    add_p(
        "La literatura fundamental en seguridad informática ha establecido clasificaciones sólidas para ataques SQLi. Halfond et al. (2006) "
        "clasificaron estas agresiones en tautologías, consultas de unión, inyecciones ciegas (blind) y canalización de procedimientos "
        "almacenados. Clarke (2012) profundizó en el análisis de los árboles de sintaxis abstracta (AST) generados por los analizadores "
        "sintácticos de bases de datos al concatenar parámetros no saneados. Sin embargo, estos marcos no consideran cómo los operadores algebraicos "
        "espaciales (Egenhofer, 1994) redefinen las condiciones lógicas de evaluación. A diferencia de un valor escalar simple, una expresión "
        "geométrica procesa múltiples dimensiones, sistemas de referencia espacial (SRID) y envolventes mínimas (bounding boxes), lo que amplía "
        "el área de escape sintáctico. Este vacío teórico en los modelos tradicionales de inyección deja sin caracterizar la manipulación "
        "de predicados topológicos nativos en motores relacionales."
    )

    add_heading_2("2.2. Modelos de Control de Acceso y Brechas de Inferencia Geoespacial")
    add_p(
        "El control de acceso en bases de datos espaciales ha sido conceptualizado formalmente por Bertino et al. (2005) a través del "
        "modelo GEO-RBAC (Spatially Aware Role-Based Access Control), el cual demostró que los permisos de lectura y modificación deben "
        "subordinarse a fronteras geográficas dinámicas. Complementariamente, Chun y Atluri (2008) y Atluri y Chun (2004) analizaron los "
        "riesgos de inferencia espacial en SDBMS, donde un usuario no autorizado puede deducir la existencia o atributos de un objeto protegido "
        "correlacionando consultas espaciales sucesivas. No obstante, estas aproximaciones asumen que la capa de servicio traslada fielmente las "
        "políticas espaciales a la base de datos; en arquitecturas web modernas, la concatenación insegura anula directamente el control de acceso "
        "en la persistencia sin ser detectada por los mecanismos de autorización de la capa de aplicación."
    )

    add_heading_2("2.3. Integridad y Modelado de Datos Catastrales bajo el Estándar LADM")
    add_p(
        "El modelado técnico de los sistemas de información catastral se rige a nivel internacional por el estándar ISO 19152:2012, "
        "conocido como Land Administration Domain Model (LADM). Autores de referencia como Lemmen et al. (2015) y van Oosterom et al. (2006) "
        "formalizaron las clases fundamentales del catastro, destacando LA_SpatialUnit (parcelas y lotes) y LA_Party (titulares prediales), "
        "extendidas posteriormente hacia modelos de valoración masiva automatizada (Kara et al., 2021). "
        "Si bien el estándar prescribe la semántica e interoperabilidad de la información territorial y registral, no define salvaguardas "
        "arquitectónicas a nivel de consulta contra ataques de inyección, dejando expuesta la integridad de los derechos reales de propiedad y la "
        "recaudación fiscal ante fallas en la implementación de software."
    )

    add_heading_2("2.4. Ataques de Complejidad Algorítmica y Vulnerabilidades en Servicios OGC")
    add_p(
        "La relevancia contemporánea de esta amenaza quedó demostrada en la industria mediante la vulnerabilidad crítica CVE-2023-25157 "
        "(con puntaje CVSS de 9.8), donde el software de referencia GeoServer permitía la ejecución remota de SQL no autenticado mediante la "
        "evaluación insegura de filtros OGC y expresiones CQL sobre bases de datos PostGIS (National Vulnerability Database, 2023). Por otro "
        "lado, en el ámbito de la denegación de servicio, Crosby y Wallach (2003) establecieron el concepto de ataques de complejidad "
        "algorítmica (Algorithmic Complexity Attacks), demostrando cómo entradas diseñadas pueden forzar a los algoritmos de peor caso "
        "(O(N^2)) a monopolizar la CPU. En motores espaciales, como documentan Agarwal y Rajan (2016), los algoritmos computacionales de la "
        "librería GEOS subyacente en PostGIS demandan una carga de cómputo cuadrática cuando se ejecutan sobre polígonos complejos desprovistos "
        "de filtrado preliminar por índice espacial GiST. Pese a estos antecedentes, la literatura no ha cuantificado el impacto de latencia "
        "ni ha formalizado esquemas defensivos integrados entre el analizador web y el motor geométrico."
    )

    # SECCIÓN 3: METODOLOGÍA
    add_heading_1("3. Metodología")
    add_heading_2("3.1. Enfoque y Diseño Experimental")
    add_p(
        "Se adoptó un diseño experimental y cuantitativo orientado a evaluar la susceptibilidad de endpoints geoespaciales "
        "ante inyecciones SQL y medir el impacto en rendimiento derivado de un esquema de mitigación multicapa. La evaluación "
        "contrasta tres escenarios defensivos: (1) servicio vulnerable sin protección, (2) servicio protegido perimetralmente "
        "mediante un cortafuegos de aplicaciones web (WAF) basado en firmas (OWASP CRS v3.3), y (3) servicio mitigado mediante el "
        "pipeline de aplicación propuesto (ORM con validación tipada y topológica previa)."
    )

    add_heading_2("3.2. Conjunto de Datos Catastrales (Dataset)")
    add_p(
        "El dataset experimental comprende 487 lotes catastrales urbanos continuos estructurados bajo el estándar ISO 19152 "
        "(LADM, clase LA_SpatialUnit) y georreferenciados en EPSG:32719. El esquema relacional de pruebas se estructuró en tres "
        "entidades: tg_lote (persistencia de los 487 lotes prediales bajo la clase LA_SpatialUnit), catastro_titulares "
        "(información alfanumérica fiscal y de autovalúo bajo la clase LA_Party) y catastro_usuarios (gestión de accesos y credenciales "
        "operativas). Las geometrías presentan una complejidad de entre 4 y 222 vértices (promedio: 9.0 vértices por polígono). "
        "Para garantizar reproducibilidad y resguardo ético, la cartografía base se obtuvo de fuentes abiertas y los atributos fiscales "
        "fueron generados proceduralmente sin incorporar información personal identificable (PII)."
    )

    add_heading_2("3.3. Entorno Experimental y Arquitectura")
    add_p(
        "El banco de pruebas se implementó en contenedores Docker mediante microservicios aislados: (1) un servicio de base de datos con "
        "PostgreSQL 15 y PostGIS 3.3, (2) una API en Python 3.11 con FastAPI y Uvicorn, y (3) un proxy reverso Nginx configurado con el "
        "módulo ModSecurity v3 y el conjunto de reglas perimetrales OWASP Core Rule Set (CRS v3.3). Las pruebas de estrés se ejecutaron en "
        "un entorno controlado con un procesador Intel Core Ultra 5 245KF de 14 núcleos a 5.2 GHz con 32 GB de RAM DDR5 y almacenamiento "
        "NVMe PCIe 4.0 sobre Linux kernel 6.6 (WSL2)."
    )

    add_heading_2("3.4. Vectores de Prueba y Métricas de Rendimiento")
    add_p(
        "Se estructuraron seis vectores de explotación basados en las directrices de prueba de inyección de la Web Security Testing Guide (OWASP Foundation, 2023), "
        "orientados a las tres dimensiones de la tríada CIA (Confidencialidad, Integridad y Disponibilidad). "
        "La batería experimental comprendió dos categorías de vectores: (a) vectores de inyección espacial directa (V1 a V3), dirigidos contra predicados "
        "topológicos nativos y funciones de análisis geométrico en PostGIS; y (b) vectores de inyección SQL convencional aplicados al flujo transaccional y "
        "administrativo del catastro (V4 a V6), utilizados como línea base de control para verificar la integridad del modelo de datos y la capacidad de "
        "detección de herramientas perimetrales. La evaluación de rendimiento contempló una batería de carga de 300 peticiones y curvas de concurrencia escalonada "
        "(1 a 100 clientes) sobre el endpoint de proximidad territorial (/predios/radio), registrando métricas de latencia (media, p50, p95, p99) y throughput (req/s). "
        "La caracterización técnica de los seis vectores de explotación, sus endpoints y los payloads representativos se detallan en el Apéndice 1."
    )

    # SECCIÓN 4: SIMULACIONES DE ATAQUE
    add_heading_1("4. Simulaciones de Ataque y Resultados de Explotación")
    add_heading_2("4.1. Simulación 1: Evasión de Límite Espacial (Spatial Logic Bypass)")
    add_p(
        "El endpoint GET /api/v1/vulnerable/predios/radio está diseñado para retornar lotes dentro de un radio de 50 metros en el sector 0101. "
        "Al inyectar en el parámetro distancia el payload '50) OR (1=1', el analizador léxico de PostgreSQL cierra prematuramente el operador "
        "ST_DWithin e introduce una tautología que anula tanto el límite espacial como el filtro de sector territorial. Como resultado, "
        "la consulta pasó de retornar 1 predio autorizado a exfiltrar masivamente 50 parcelas catastrales no autorizadas en 7.03 ms. En el endpoint "
        "mitigado, Pydantic y GeoAlchemy2 verificaron el tipo numérico estricto, neutralizando el ataque con código HTTP 422."
    )

    add_heading_2("4.2. Simulación 2: Inferencia de Datos por Errores Geométricos (Error-Based Spatial SQLi)")
    add_p(
        "En el endpoint GET /api/v1/vulnerable/predios/poligono, la aplicación dibuja polígonos cartográficos sin exponer datos textuales. "
        "El atacante estructuró un canal lateral inferencial acoplado al operador ST_Intersects, inyectando una división por cero condicional "
        "a la conjetura de caracteres sobre la tabla administrativa: si el carácter adivinado coincide, se produce una excepción en PostGIS "
        "disparando un error HTTP 500; si es falso, el motor responde con HTTP 200. Mediante este mecanismo se exfiltró la credencial completa "
        "'admin' en 42 segundos. En la versión mitigada, Shapely evaluó la validez topológica en memoria, rechazando la sintaxis con HTTP 422."
    )

    add_heading_2("4.3. Simulación 3: Denegación de Servicio Espacial (Spatial DoS)")
    add_p(
        "Aprovechando la complejidad geométrica base de las parcelas (promedio de 9.0 vértices y hasta 222 vértices por polígono), el atacante inyectó "
        "en el endpoint GET /api/v1/vulnerable/predios/analisis-expansion una subconsulta con un producto cruzado espacial O(N^2) que computa buffers "
        "con alta densidad de segmentos por cuadrante. Para aislar el coste computacional del producto cartesiano sin inducir un bloqueo permanente del "
        "servidor de pruebas, la inyección evaluó un subconjunto sistemático de 20 parcelas cruzadas entre sí (400 pares de polígonos), variando la "
        "resolución de vértices en el buffer. Como se evidencia empíricamente en la Figura 1, esta inyección del producto cartesiano "
        "desencadena una explosión de complejidad algorítmica O(N^2) que eleva la latencia desde 10.8 ms hasta 1,692.1 ms a medida que los "
        "vértices evaluados en el buffer crecen de 14,400 a más de 345,600 puntos, saturando los workers de PostgreSQL en el procesador "
        "Intel Core Ultra 5 245KF. En contraste, la arquitectura mitigada preserva una latencia acotada de ~15 ms al restringir los parámetros a "
        "escalares validados mediante Pydantic y GeoAlchemy2."
    )
    add_figure("figures/fig3_spatial_dos_complexity.png", "Figura 1. Curva de degeneración algorítmica cuadrática O(N²) en PostGIS/GEOS ante inyección de sobrecarga geométrica vs. mitigación acotada", width_inches=5.4)

    add_heading_2("4.4. Simulación 4: Fraude en Ficha Catastral (Tampering de Autovalúo)")
    add_p(
        "En el endpoint POST /api/v1/vulnerable/ficha/modificar, se simuló un ataque contra la integridad tributaria. Mediante concatenación en la cláusula "
        "SET, el atacante manipuló el autovalúo fijándolo en S/ 0.00 y sustituyó el titular predial legítimo por un tercero no autorizado, "
        "demostrando la vulnerabilidad de las bases fiscales ante inyecciones de actualización directa. El endpoint mitigado bloqueó el fraude mediante "
        "expresiones regulares alfabéticas y validación de rangos positivos en SQLAlchemy (HTTP 422)."
    )

    add_heading_2("4.5. Simulación 5: Borrado Destructivo de Cartografía Predial (Data Destruction)")
    add_p(
        "En el endpoint DELETE /api/v1/vulnerable/predios/borrar, la inyección del payload literal '0101' OR '1'='1' en el parámetro de filtrado sectorial "
        "transformó la sentencia en una eliminación incondicional de registros (DELETE FROM tg_lote WHERE cod_sector = '0101' OR '1'='1'), suprimiendo las 487 parcelas "
        "y dejando el visor webmapping sin cartografía. En contraste, el endpoint mitigado validó el sector mediante el patrón estricto ^\\d{4}$, "
        "rechazando la inyección con código HTTP 422 y preservando intacta la base catastral."
    )

    add_heading_2("4.6. Simulación 6: Evasión de Autenticación en el Visor Catastral")
    add_p(
        "En el endpoint POST /api/v1/vulnerable/auth/login, el atacante ingresó \"admin' --\" en el campo de usuario, comentando la validación del hash "
        "de contraseña. La API otorgó acceso y emitió un token con rol superadmin_catastro. La versión mitigada con prepared statements "
        "y hashing criptográfico SHA-256 neutralizó el bypass al buscar literalmente la cadena con comillas sin interpretarla como sintaxis SQL."
    )

    # SECCIÓN 5: MITIGACIÓN Y EVALUACIÓN
    add_heading_1("5. Estrategias de Mitigación y Evaluación de Rendimiento")
    add_p(
        "Como se ilustra en la Figura 2, la mitigación arquitectónica integró un pipeline de defensa en profundidad "
        "con tres barreras secuenciales, donde la Barrera 2 (Shapely) opera como filtro de integridad topológica en memoria "
        "activado específicamente ante cargas útiles geométricas complejas (WKT o GeoJSON, descartando anomalías o geometrías "
        "auto-intersecadas con HTTP 422 antes de interactuar con la base de datos), mientras que los parámetros puramente numéricos "
        "o alfanuméricos transitan directamente desde la validación estricta de Pydantic (Barrera 1) hacia la compilación de "
        "variables tipadas (EWKB) y sentencias preparadas en GeoAlchemy2 y SQLAlchemy (Barrera 3)."
    )
    add_figure("figures/fig1_defense_pipeline.png", "Figura 2. Arquitectura del pipeline de defensa en profundidad de tres barreras para servicios catastrales en PostGIS", width_inches=5.8)

    add_p(
        "Para la evaluación empírica de rendimiento y latencia (Tabla 1 y Figura 3), se seleccionó como escenario representativo "
        "de alta frecuencia transaccional el endpoint de consulta espacial por radio (GET /api/v1/vulnerable/predios/radio frente a "
        "GET /api/v1/mitigated/predios/radio), evaluando peticiones válidas bajo una carga estandarizada de 300 peticiones con 10 "
        "clientes concurrentes. Los resultados se resumen en la Tabla 1.",
        indent=True
    )

    # TABLA 1 (Formato IMJETA: Label arriba, centrado, bold, size 10)
    p_tlabel = doc.add_paragraph()
    p_tlabel.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_tlabel.paragraph_format.space_before = Pt(8)
    p_tlabel.paragraph_format.space_after = Pt(4)
    r_tl = p_tlabel.add_run("Tabla 1: Comparativa de Rendimiento y Latencia entre API Vulnerable y API Mitigada")
    set_font(r_tl, size=10, bold=True)

    table_data = [
        ["Métrica de Rendimiento", "API Vulnerable (SQL Dinámico)", "API Mitigada (GeoAlchemy2)", "Variación (Overhead)"],
        ["Throughput (Rendimiento)", "556.21 req/s", "484.36 req/s", "-71.85 req/s (-12.92%)"],
        ["Latencia Media (Mean)", "17.26 ms", "19.89 ms", "+2.63 ms (+15.24%)"],
        ["Percentil 50 (Mediana / p50)", "15.37 ms", "18.42 ms", "+3.05 ms"],
        ["Percentil 95 (p95)", "31.49 ms", "32.63 ms", "+1.14 ms"],
        ["Percentil 99 (p99)", "43.75 ms", "38.24 ms", "-5.51 ms (-12.59%)"],
        ["Tasa de Error HTTP (Error Rate)", "0.0%", "0.0%", "0.0%"]
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
    r_tnote = p_tnote.add_run("Nota: Mediciones empíricas recopiladas bajo 300 peticiones concurrentes (concurrencia=10) sobre una estación de trabajo con procesador Intel Core Ultra 5 245KF, 32 GB RAM DDR5 y almacenamiento NVMe PCIe 4.0 en Docker Desktop (PostgreSQL 15 / PostGIS 3.3).")
    set_font(r_tnote, size=9, italic=True)

    add_p(
        "Para medir la resiliencia bajo estrés progresivo, se evaluó una serie de concurrencia escalonada de 1 a 100 clientes concurrentes. "
        "Como se evidencia en la Figura 3(a), el throughput de la arquitectura mitigada escala eficientemente alcanzando una meseta estable superior a "
        "450 req/s sin degradación por bloqueos. Asimismo, la Figura 3(b) revela que la arquitectura mitigada neutraliza los picos severos de "
        "latencia de cola observados en la API vulnerable bajo baja concurrencia (140.8 ms frente a 33.1 ms a 5 clientes). A niveles de estrés "
        "elevados (50 a 100 clientes), el percentil 99 de la versión mitigada experimenta un incremento moderado (~101 ms vs. ~62 ms), atribuible "
        "a la serialización y sobrecosto de CPU en la capa de aplicación (Pydantic/ORM), lo que representa un compromiso aceptable frente a las "
        "garantías de seguridad obtenidas.",
        indent=True
    )
    add_figure("figures/fig2_concurrency_latency.png", "Figura 3. Comparativa empírica de rendimiento (Throughput) y percentiles de latencia (p50 y p99) ante concurrencia escalonada (1 a 100 clientes)", width_inches=5.8)

    # SECCIÓN 6: DISCUSIÓN
    add_heading_1("6. Discusión")
    add_p(
        "Los resultados empíricos demuestran que la mitigación basada en GeoAlchemy2 y validación previa con Shapely introduce un overhead "
        "de latencia media de apenas 2.63 milisegundos por petición (+15.24%), manteniendo un throughput de 484.36 peticiones por segundo. "
        "Un aspecto relevante para el diseño de software es el comportamiento en el percentil 99 (p99): en la prueba de carga estandarizada "
        "(10 clientes), la latencia de cola disminuyó de 43.75 ms a 38.24 ms (-12.59%) gracias a la reutilización eficiente de planes de "
        "ejecución preparados (prepared statements) en PostgreSQL al evitar el re-parseo continuo de consultas dinámicas, mientras que bajo estrés "
        "masivo concurrente el sobrecosto de serialización en la capa de aplicación modula la respuesta sin comprometer la estabilidad ni registrar "
        "fallos (0.0%). Este incremento marginal en el promedio es insignificante frente a la ganancia de seguridad, neutralizando la exfiltración "
        "masiva de datos catastrales, el canal lateral de error y la denegación de servicio espacial. Se concluye que los WAFs tradicionales "
        "son ineficaces ante payloads espaciales, demandando esquemas de validación sintáctica con conciencia espacial integrados en el código de la aplicación."
    )
    add_p(
        "La Figura 4 sintetiza la tasa de mitigación y bloqueo de ataques (%) a través de los seis vectores evaluados, contrastando una "
        "arquitectura desprotegida, un WAF tradicional basado en firmas (OWASP ModSecurity Core Rule Set) y el pipeline propuesto. "
        "Mientras que el WAF genérico no logra identificar los ataques espaciales (0% a 20% de bloqueo en vectores topológicos como "
        "ST_DWithin y ST_Intersects al carecer de gramática geoespacial), el bloqueo residual del 15% al 20% registrado por el WAF en V1 y V2 "
        "se debió exclusivamente a la detección de tokens SQL convencionales (como operadores booleanos OR o comillas desparejadas) en ciertas "
        "variantes del payload, y no a una inspección semántica de las funciones topológicas subyacentes, como lo demuestra su inoperancia absoluta "
        "(0%) frente al vector DoS en V3. En contraste, el pipeline de tres barreras logra un bloqueo completo del 100% en todos los vectores evaluados de la tríada CIA.",
        indent=True
    )
    add_figure("figures/fig4_attack_mitigation_matrix.png", "Figura 4. Tasa de mitigación y bloqueo de ataques (%) entre arquitectura desprotegida, WAF tradicional (OWASP CRS) y pipeline propuesto", width_inches=5.8)
    add_run_in(
        "Independencia de plataforma y validez del benchmarking.",
        "Si bien las métricas absolutas de latencia se obtuvieron sobre una estación de trabajo con procesador Intel Core Ultra 5 245KF, "
        "la validez metodológica y la generalización de los resultados radican en las proporciones relativas (+15.24% de sobrecosto medio y "
        "-12.59% de mejora en cola p99) y en las complejidades asintóticas computacionales. En servidores gubernamentales o instancias de nube con "
        "recursos más restringidos (frecuentes en gobiernos locales), el costo computacional del preprocesamiento en Python (GeoAlchemy2/Shapely) "
        "sigue siendo despreciable frente a los cuellos de botella dominantes de I/O en disco y concurrencia relacional. Por el contrario, la ausencia "
        "de mitigación frente a ataques de complejidad algorítmica (O(N^2)) como el Spatial DoS (Simulación 3) resulta crítica en procesadores de gama "
        "de entrada con menor paralelismo, donde unas pocas consultas maliciosas bloquean de inmediato la totalidad del servicio catastral.",
        indent=True
    )
    add_run_in(
        "Impacto sistémico en la integridad de trámites y datos catastrales.",
        "La viabilidad empírica de la Simulación 4 (manipulación de autovalúo y titularidad mediante inyección directa) demuestra cómo un fallo a "
        "nivel de persistencia relacional trasciende la alteración de una tabla y compromete la validez de los trámites de gobierno electrónico municipal. "
        "Cuando los sistemas catastrales interoperan automáticamente para emitir certificados catastrales con validación criptográfica QR, "
        "constancias de no adeudo fiscal o minutas de transferencia inmobiliaria bajo ISO 19152 LADM, la inyección de datos arbitrarios en "
        "catastro_titulares y tg_lote propaga inconsistencias fiscales y registrales sin activar alertas en la interfaz de usuario, evidenciando "
        "que la sanitización tipada en el ORM es una salvaguarda indispensable para la fiabilidad de los servicios públicos digitales.",
        indent=True
    )

    # SECCIÓN 7: CONCLUSIÓN (Formato IMJETA: Párrafo único entre 175 y 300 palabras)
    add_heading_1("7. Conclusiones y Recomendaciones")
    add_p(
        "Este artículo formalizó y demostró empíricamente la viabilidad de seis vectores de inyección SQL espacial en sistemas "
        "de información catastral basados en PostGIS, evidenciando que las funciones topológicas nativas no garantizan aislamiento de datos "
        "cuando se construyen mediante concatenación de cadenas. La evaluación experimental sobre 487 parcelas catastrales reales "
        "(ISO 19152 LADM) comprobó que atacantes no autenticados pueden evadir límites zonales, reconstruir credenciales mediante canales "
        "laterales de error geométrico, inducir denegación de servicio espacial por sobrecarga algorítmica cuadrática, alterar fichas prediales "
        "tributarias y ejecutar borrados cartográficos masivos. Frente a ello, la adopción de una arquitectura de defensa en profundidad basada "
        "en GeoAlchemy2, tipado rígido con Pydantic y validación topológica previa en memoria con Shapely mitigó con éxito el 100% de los "
        "escenarios de explotación evaluados. El benchmarking transaccional demostró que esta seguridad robusta introduce un incremento medio "
        "de latencia de apenas 2.63 ms (+15.24%), mejorando simultáneamente la estabilidad en el percentil 99 en un 12.59% gracias a la reutilización "
        "de planes de ejecución preparados en PostgreSQL. En conclusión, la seguridad en infraestructuras catastrales exige abandonar el "
        "paradigma de sanitización escalar tradicional, adoptando controles sintácticos con conciencia espacial integrados desde el diseño "
        "arquitectónico de software."
    )

    # SECCIÓN 8: REFERENCIAS (APA 7th edition, hanging indent 0.5 inches)
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

    # Cláusula obligatoria IMJETA: Cita del propio artículo
    p_cite_intro = doc.add_paragraph()
    p_cite_intro.paragraph_format.space_before = Pt(12)
    p_cite_intro.paragraph_format.space_after = Pt(4)
    r_ci = p_cite_intro.add_run("This paper may be cited as:")
    set_font(r_ci, size=11, bold=True)

    p_cite = doc.add_paragraph()
    p_cite.paragraph_format.left_indent = Inches(0.5)
    p_cite.paragraph_format.first_line_indent = Inches(-0.5)
    p_cite.paragraph_format.space_after = Pt(12)
    r_cbody = p_cite.add_run("Rodrigo, A. (2026). Evaluación de Vulnerabilidades de Inyección SQL Espacial en Sistemas de Información Catastral basados en PostGIS. International Multidisciplinary Journal of Emerging Technologies and Applications, 1(1), 1-8. https://imjeta.org/index.php/IMJETA/libraryFiles/downloadPublic/1")
    set_font(r_cbody, size=11)

    # APÉNDICE 1 (Inicia en página nueva según plantilla IMJETA)
    doc.add_page_break()
    add_heading_1("Appendix 1")
    add_p(
        "Instrumento de Investigación: Batería de Vectores de Explotación: Operadores Espaciales (V1–V3) y Flujo Catastral / Control (V4–V6). "
        "A continuación se detallan los seis vectores de explotación diseñados y ejecutados para evaluar la seguridad de la API catastral:"
    )

    app_data = [
        ["Vector de Prueba", "Endpoint Evaluado", "Payload Representativo", "Dimensión CIA y Efecto"],
        ["1. Evasión Lógica", "GET /api/v1/vulnerable/predios/radio", "50) OR 1=1 --", "Confidencialidad: Exfiltración de predios de sectores restringidos."],
        ["2. Canal Lateral Ciego", "GET /api/v1/vulnerable/predios/poligono", "POLYGON(...) AND 1=(CASE WHEN ... THEN CAST(ST_GeomFromText('ERR') AS INT) ELSE 1 END)", "Confidencialidad: Exfiltración carácter por carácter de hashes."],
        ["3. DoS Algorítmico", "GET /api/v1/vulnerable/predios/analisis-expansion", "10 + (SELECT COUNT(*) FROM tg_lote a CROSS JOIN ... ST_Buffer(..., 100))", "Disponibilidad: Explosión combinatoria O(N^2), saturación de CPU."],
        ["4. Tampering Predial", "POST /api/v1/vulnerable/ficha/modificar", "id_lote = '21010101000000', nuevo_autovaluo = 0, nuevo_titular = 'HACKER'", "Integridad: Alteración tributaria y suplantación de titularidad."],
        ["5. Borrado Masivo", "DELETE /api/v1/vulnerable/predios/borrar", "filtro_sector = '0101' OR '1'='1'", "Integridad y Disponibilidad: Eliminación incondicional de 487 lotes."],
        ["6. Evasión de Auth", "POST /api/v1/vulnerable/auth/login", "username = admin' --", "Confidencialidad e Integridad: Escalación a superadmin_catastro."]
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

    # SEGURIDAD: Nunca sobreescribir Articulo_Cientifico_IMJETA_Final.docx (trabajo manual del autor)
    out_path = "Articulo_Cientifico_IMJETA_Generado_Auto.docx"
    doc.save(out_path)
    print(f"Documento generado de forma segura en: {out_path} (sin tocar el archivo final del usuario)")

if __name__ == "__main__":
    create_imjeta_doc()

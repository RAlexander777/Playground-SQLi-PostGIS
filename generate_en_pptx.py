from pptx import Presentation

# Script to translate 'Evaluación de Inyección SQL Espacial en PostGIS.pptx' into 1:1 English
# Output: 'Evaluation of Spatial SQL Injection in PostGIS.pptx'

prs = Presentation('Evaluación de Inyección SQL Espacial en PostGIS.pptx')

# Mapping of exact Spanish text to English text
translations = {
    # Slide 1
    "Evaluación de Vulnerabilidades de Inyección SQL Espacial en Sistemas de Información Catastral basados en PostGIS":
        "Evaluation of Spatial SQL Injection Vulnerabilities in PostGIS-Based Cadastral Information Systems",
    "Evaluación de riesgos, pruebas y mitigación":
        "Risk Assessment, Testing, and Mitigation",
    "Rodrigo Alexander Becerra Lucano":
        "Rodrigo Alexander Becerra Lucano",

    # Slide 2
    "INTRODUCCIÓN":
        "INTRODUCTION",
    "Los sistemas de información catastral modernos exponen servicios web sobre arquitecturas cliente-servidor, sin embargo, esto hace que se expongan a vectores de ataque SQLi.":
        "Modern cadastral information systems expose web services over client-server architectures; however, this exposes them to SQLi attack vectors.",
    "PostGIS presenta operadores geométricos (ST_DWithin, ST_Intersectes, ST_Buffer) , cuyo mal manejo puede permitir el pase a amenazas o filtración de datos, además de desencadenar un ataque DoS.":
        "PostGIS features geometric operators (ST_DWithin, ST_Intersects, ST_Buffer) whose improper handling can allow threats, data leakage, and trigger DoS attacks.",
    "En este artículo se presenta la evaluación de 6 vectores de ataque orientados a la triada CIA (Confidencialidad, Integridad y Disponibilidad), así como las barreras de mitigación de dichos ataques.":
        "This paper presents the evaluation of 6 attack vectors targeting the CIA triad (Confidentiality, Integrity, and Availability), alongside mitigation barriers for these attacks.",

    # Slide 3
    "DATASET DE PRUEBA Y ENTORNO DE EVALUACIÓN":
        "TEST DATASET AND EVALUATION ENVIRONMENT",
    "ESTÁNDAR INTERNACIONAL":
        "INTERNATIONAL STANDARD",
    "487 Lotes Urbanos (ISO 19152 / LADM)":
        "487 Urban Parcels (ISO 19152 / LADM)",
    "Cartografía estructurada bajo la clase LA_SpatialUnit y georreferenciada en el sistema de coordenadas oficial EPSG:32719.":
        "Cartography structured under the LA_SpatialUnit class and georeferenced in the official coordinate reference system EPSG:32719.",
    "COMPLEJIDAD VECTORIAL":
        "VECTOR COMPLEXITY",
    "Geometrías de 4 a 222 Vértices":
        "Geometries from 4 to 222 Vertices",
    "Promedio de 9.0 vértices por polígono, permitiendo evaluar el sobrecoste algorítmico y la dispersión topológica en parcelas reales.":
        "Average of 9.0 vertices per polygon, enabling assessment of algorithmic overhead and topological dispersion on real-world parcels.",
    "ESQUEMA RELACIONAL Y ÉTICA":
        "RELATIONAL SCHEMA AND ETHICS",
    "3 Entidades sin Información PII":
        "3 Entities with No PII Data",
    "Tablas tg_lote, catastro_titulares (LA_Party/autovalúo) y catastro_usuarios; atributos fiscales sintéticos reproducibles.":
        "Tables tg_lote, catastro_titulares (LA_Party/tax assessment), and catastro_usuarios; reproducible synthetic fiscal attributes.",
    "ARQUITECTURA DE PRUEBAS":
        "TESTING ARCHITECTURE",
    "Microservicios Aislados en Docker":
        "Isolated Docker Microservices",
    "PostgreSQL 15 con PostGIS 3.3 y API en Python 3.11 (FastAPI/Uvicorn) ejecutados sobre procesador Intel Core Ultra 5 con 32 GB RAM DDR5.":
        "PostgreSQL 15 with PostGIS 3.3 and Python 3.11 API (FastAPI/Uvicorn) executed on an Intel Core Ultra 5 processor with 32 GB DDR5 RAM.",
    "Playground: https://github.com/RAlexander777/Playground-SQLi-PostGIS.git":
        "Playground: https://github.com/RAlexander777/Playground-SQLi-PostGIS.git",

    # Slide 4
    "EVALUACIÓN DE LOS 6 VECTORES DE ATAQUE":
        "EVALUATION OF THE 6 ATTACK VECTORS",
    "DIMENSIÓN":
        "DIMENSION",
    "Disponibilidad":
        "Availability",
    "Integridad":
        "Integrity",
    "Confidencialidad":
        "Confidentiality",
    "V1. Evasión Lógica Espacial":
        "V1. Spatial Logic Bypass",
    "Tautología en ST_DWithin, filtrado de geometrías.":
        "Tautology in ST_DWithin, geographic boundary bypass.",
    "V2. Canal Lateral por Error":
        "V2. Error-Based Side Channel",
    "Excepciones condicionales en ST_Intersects.":
        "Conditional geometric exceptions in ST_Intersects.",
    "V3. Denegación de Servicio (DoS)":
        "V3. Denial of Service (DoS)",
    "Inyección de producto cartesiano espacial con ST_Buffer y alta densidad de vértices.":
        "Spatial Cartesian product injection via ST_Buffer and high vertex density.",
    "V4. Tampering de Ficha Predial":
        "V4. Cadastral Record Tampering",
    "Modificación de datos.":
        "Unauthorized data modification.",
    "V5. Borrado Cartográfico":
        "V5. Cartographic Deletion",
    "Eliminación de geometrías del sector.":
        "Deletion of sector geometries.",
    "V6. Bypass de Autenticación":
        "V6. Authentication Bypass",
    "Acceso al sistema con rol administrativo.":
        "Unauthorized system access with administrative role.",

    # Slide 5
    "BARRERAS DE MITIGACIÓN DE ATAQUES":
        "ATTACK MITIGATION BARRIERS",
    "Barrera 1: Validación Estricta con Pydantic":
        "Barrier 1: Strict Validation with Pydantic",
    "Tipado numérico estricto, límites físicos en coordenadas y expresiones regulares en parámetros alfanuméricos.":
        "Strict numeric typing, physical coordinate bounding, and regular expression guards on alphanumeric parameters.",
    "Barrera 2: Filtro Topológico en Memoria con Shapely":
        "Barrier 2: In-Memory Topological Filtering with Shapely",
    "Inspección geométrica de cargas WKT/GeoJSON antes de consultar la BD; rechazo de auto-intersecciones o geometrías corruptas con HTTP 422.":
        "Geometric inspection of WKT/GeoJSON payloads before querying the DB; rejection of self-intersections or corrupted geometries via HTTP 422.",
    "Barrera 3: Parametrización en ORM con GeoAlchemy2 y SQLAlchemy":
        "Barrier 3: ORM Parameterization with GeoAlchemy2 and SQLAlchemy",
    "Compilación tipada en el árbol sintáctico (AST) con variables binarias EWKB y sentencias preparadas; elimina la concatenación textual.":
        "Typed AST compilation with EWKB binary bind variables and prepared statements; completely eliminates textual concatenation.",

    # Slide 6
    "RESULTADOS  Y RENDIMIENTO":
        "RESULTS AND PERFORMANCE",
    "EFECTIVIDAD DE SEGURIDAD":
        "SECURITY EFFECTIVENESS",
    "Bloqueo de los 6 vectores evaluados":
        "Block rate across all 6 evaluated vectors",
    "SOBRECOSTO OPERATIVO":
        "OPERATIONAL OVERHEAD",
    "19.89 ms mitigado vs. 17.26 ms vulnerable":
        "19.89 ms mitigated vs. 17.26 ms vulnerable",
    "ESTABILIDAD DE COLA (P99)":
        "TAIL STABILITY (P99)",
    "Reducción gracias a planes preparados":
        "Tail latency reduction via prepared execution plans",

    # Slide 7
    "CONCLUSIONES DEL ESTUDIO":
        "STUDY CONCLUSIONS",
    "Los operadores geométricos de PostGIS requieren el mismo rigor de parametrización que las consultas relacionales clásicas; su concatenación textual compromete la fe pública catastral y el cálculo tributario.":
        "PostGIS geometric operators require the same parameterization rigor as traditional relational queries; textual concatenation directly jeopardizes cadastral public trust and tax assessment calculations.",
    "La validación sintáctica escalar tradicional resulta insuficiente ante predicados topológicos; la inspección en memoria con Shapely y Pydantic previene sobrecargas algorítmicas O(N²) antes de consultar la base de datos.":
        "Traditional scalar syntactic validation is insufficient for topological predicates; in-memory inspection with Shapely and Pydantic prevents O(N²) algorithmic overload before reaching the database.",
    "La compilación tipada en ORM (GeoAlchemy2/SQLAlchemy) neutraliza el 100% de los vectores con un sobrecosto medio marginal de apenas 2.63 ms, mejorando la latencia de cola p99 en un 12.59% gracias a sentencias preparadas.":
        "Typed ORM compilation (GeoAlchemy2/SQLAlchemy) neutralizes 100% of attack vectors with a marginal average overhead of merely 2.63 ms, improving p99 tail latency by 12.59% via prepared execution plans."
}

def translate_paragraph(p):
    original_text = p.text.strip()
    if not original_text:
        return
    
    if original_text in translations:
        target = translations[original_text]
        # Preserve single run or multiple runs
        if len(p.runs) == 1:
            p.runs[0].text = target
        elif len(p.runs) > 1:
            # First run gets the text, subsequent runs are cleared to preserve primary style
            p.runs[0].text = target
            for r in p.runs[1:]:
                r.text = ""
        else:
            p.text = target
    else:
        # Check partial replacements
        for es, en in translations.items():
            if es in p.text:
                p.text = p.text.replace(es, en)

for s_idx, slide in enumerate(prs.slides):
    for shape in slide.shapes:
        if shape.has_text_frame:
            for p in shape.text_frame.paragraphs:
                translate_paragraph(p)
        if shape.has_table:
            for row in shape.table.rows:
                for cell in row.cells:
                    for p in cell.text_frame.paragraphs:
                        translate_paragraph(p)

out_file = "Evaluation of Spatial SQL Injection in PostGIS.pptx"
prs.save(out_file)
print(f"Presentation successfully generated: {out_file}")

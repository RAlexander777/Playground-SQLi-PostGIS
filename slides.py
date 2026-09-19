from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN
from pptx.enum.shapes import MSO_SHAPE

# 1. Configuración de lienzo (16:9 Panorámico)
prs = Presentation()
prs.slide_width = Inches(13.333)
prs.slide_height = Inches(7.5)

blank_layout = prs.slide_layouts[6]

# Paleta de colores minimalista técnica
COLOR_BG = RGBColor(248, 250, 252)         # Slate 50
COLOR_TEXT_MAIN = RGBColor(15, 23, 42)     # Slate 900
COLOR_TEXT_MUTED = RGBColor(100, 116, 139) # Slate 500
COLOR_ACCENT = RGBColor(14, 116, 144)      # Cyan 700
COLOR_CARD_BG = RGBColor(255, 255, 255)    # Blanco puro
COLOR_BORDER = RGBColor(226, 232, 240)     # Slate 200
COLOR_RED = RGBColor(220, 38, 38)          # Red 600
COLOR_GREEN = RGBColor(22, 163, 74)        # Green 600

def set_slide_background(slide):
    bg_shape = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, prs.slide_width, prs.slide_height)
    bg_shape.fill.solid()
    bg_shape.fill.fore_color.rgb = COLOR_BG
    bg_shape.line.fill.background()

def add_header(slide, tag, title):
    header_box = slide.shapes.add_textbox(Inches(0.8), Inches(0.5), Inches(11.7), Inches(1.1))
    tf = header_box.text_frame
    tf.word_wrap = True
    tf.margin_left = tf.margin_top = tf.margin_right = tf.margin_bottom = 0
    
    p_tag = tf.paragraphs[0]
    p_tag.text = tag.upper()
    p_tag.font.name = "Segoe UI"
    p_tag.font.size = Pt(10)
    p_tag.font.bold = True
    p_tag.font.color.rgb = COLOR_ACCENT
    p_tag.space_after = Pt(4)
    
    p_title = tf.add_paragraph()
    p_title.text = title
    p_title.font.name = "Segoe UI"
    p_title.font.size = Pt(22)
    p_title.font.bold = True
    p_title.font.color.rgb = COLOR_TEXT_MAIN

def add_card(slide, x, y, width, height):
    shape = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, x, y, width, height)
    shape.fill.solid()
    shape.fill.fore_color.rgb = COLOR_CARD_BG
    shape.line.color.rgb = COLOR_BORDER
    shape.line.width = Pt(1)
    return shape

# ==============================================================================
# SLIDE 1: PORTADA Y PLANTEAMIENTO
# ==============================================================================
s1 = prs.slides.add_slide(blank_layout)
set_slide_background(s1)

tb1 = s1.shapes.add_textbox(Inches(1.2), Inches(1.8), Inches(11.0), Inches(2.5))
tf1 = tb1.text_frame
tf1.word_wrap = True

p_sub = tf1.paragraphs[0]
p_sub.text = "INVESTIGACIÓN EXPERIMENTAL DE CIBERSEGURIDAD GEOESPACIAL"
p_sub.font.name = "Segoe UI"
p_sub.font.size = Pt(11)
p_sub.font.bold = True
p_sub.font.color.rgb = COLOR_ACCENT
p_sub.space_after = Pt(12)

p_title = tf1.add_paragraph()
p_title.text = "Evaluación de Vulnerabilidades de Inyección SQL Espacial en Sistemas de Información Catastral basados en PostGIS"
p_title.font.name = "Segoe UI"
p_title.font.size = Pt(28)
p_title.font.bold = True
p_title.font.color.rgb = COLOR_TEXT_MAIN
p_title.space_after = Pt(14)

p_meta = tf1.add_paragraph()
p_meta.text = "Riesgos en Operadores Topológicos · Mitigación en Capa de Aplicación · ISO 19152 LADM"
p_meta.font.name = "Segoe UI"
p_meta.font.size = Pt(13)
p_meta.font.color.rgb = COLOR_TEXT_MUTED

# Tarjetas clave inferiores
col_w = Inches(3.45)
gap = Inches(0.3)
cards_data = [
    ("Contexto Crítico", "Geoportales municipales y visores catastrales exponen APIs REST sobre PostgreSQL/PostGIS para recaudación e interoperabilidad."),
    ("Falsa Sensación de Seguridad", "Existe la presunción de que operadores topológicos (ST_DWithin, ST_Intersects) son inmunes por su naturaleza geométrica."),
    ("Brecha Técnica", "La interpolación de texto en funciones espaciales permite romper filtros de sector, exfiltrar registros e inducir denegación de servicio.")
]

for i, (head, desc) in enumerate(cards_data):
    x = Inches(1.2) + i * (col_w + gap)
    card = add_card(s1, x, Inches(4.7), col_w, Inches(1.8))
    tf = card.text_frame
    tf.word_wrap = True
    tf.margin_top = Inches(0.2)
    tf.margin_left = Inches(0.25)
    tf.margin_right = Inches(0.25)
    
    p1 = tf.paragraphs[0]
    p1.text = head
    p1.font.name = "Segoe UI"
    p1.font.size = Pt(13)
    p1.font.bold = True
    p1.font.color.rgb = COLOR_TEXT_MAIN
    p1.space_after = Pt(6)
    
    p2 = tf.add_paragraph()
    p2.text = desc
    p2.font.name = "Segoe UI"
    p2.font.size = Pt(10.5)
    p2.font.color.rgb = COLOR_TEXT_MUTED

# ==============================================================================
# SLIDE 2: TAXONOMÍA DE ATAQUE (TRÍADA CIA)
# ==============================================================================
s2 = prs.slides.add_slide(blank_layout)
set_slide_background(s2)
add_header(s2, "Taxonomía Experimental", "Evaluación de Vectores sobre el Flujo Catastral (Tríada CIA)")

card_l = add_card(s2, Inches(0.8), Inches(1.8), Inches(5.7), Inches(5.0))
tf_l = card_l.text_frame
tf_l.word_wrap = True
tf_l.margin_top = Inches(0.25)
tf_l.margin_left = Inches(0.3)
tf_l.margin_right = Inches(0.3)

p_l_head = tf_l.paragraphs[0]
p_l_head.text = "Vectores de Inyección Espacial Directa (V1 - V3)"
p_l_head.font.size = Pt(14)
p_l_head.font.bold = True
p_l_head.font.color.rgb = COLOR_RED
p_l_head.space_after = Pt(12)

v_spatial = [
    ("V1. Evasión Lógica (ST_DWithin)", "Tautología que anula radio métrico y filtro de sector; exfiltración masiva de 50 lotes restringidos en 7.03 ms."),
    ("V2. Canal Lateral Ciego (ST_Intersects)", "Inferencia booleana vinculada a división por cero topológica; extracción de hashes administrativos en 42 segundos."),
    ("V3. DoS Espacial Algorítmico (ST_Buffer)", "Inyección de subconsulta con producto cruzado O(N²); sobrecarga crítica de CPU en motor GEOS.")
]

for title, desc in v_spatial:
    p = tf_l.add_paragraph()
    p.text = "• " + title
    p.font.size = Pt(11.5)
    p.font.bold = True
    p.font.color.rgb = COLOR_TEXT_MAIN
    
    p_desc = tf_l.add_paragraph()
    p_desc.text = desc
    p_desc.font.size = Pt(10)
    p_desc.font.color.rgb = COLOR_TEXT_MUTED
    p_desc.space_after = Pt(10)

card_r = add_card(s2, Inches(6.8), Inches(1.8), Inches(5.7), Inches(5.0))
tf_r = card_r.text_frame
tf_r.word_wrap = True
tf_r.margin_top = Inches(0.25)
tf_r.margin_left = Inches(0.3)
tf_r.margin_right = Inches(0.3)

p_r_head = tf_r.paragraphs[0]
p_r_head.text = "Vectores Convencionales de Control Catastral (V4 - V6)"
p_r_head.font.size = Pt(14)
p_r_head.font.bold = True
p_r_head.font.color.rgb = COLOR_ACCENT
p_r_head.space_after = Pt(12)

v_control = [
    ("V4. Fraude Predial (Tampering)", "Manipulación de cláusula SET; reducción fiscal del autovalúo a S/ 0.00 y suplantación del titular predial."),
    ("V5. Destrucción Cartográfica", "Inyección de cláusula WHERE 1=1; purga incondicional de los 487 lotes en tabla tg_lote (pérdida total del visor)."),
    ("V6. Evasión de Autenticación", "Comentario SQL en interfaz de acceso; escalación ilegítima al rol administrativo superadmin_catastro.")
]

for title, desc in v_control:
    p = tf_r.add_paragraph()
    p.text = "• " + title
    p.font.size = Pt(11.5)
    p.font.bold = True
    p.font.color.rgb = COLOR_TEXT_MAIN
    
    p_desc = tf_r.add_paragraph()
    p_desc.text = desc
    p_desc.font.size = Pt(10)
    p_desc.font.color.rgb = COLOR_TEXT_MUTED
    p_desc.space_after = Pt(10)

# ==============================================================================
# SLIDE 3: SPATIAL DOS ALGORÍTMICO
# ==============================================================================
s3 = prs.slides.add_slide(blank_layout)
set_slide_background(s3)
add_header(s3, "Disponibilidad Crítica", "Spatial DoS: Explosión de Complejidad Algorítmica O(N²)")

card_dos1 = add_card(s3, Inches(0.8), Inches(1.8), Inches(4.5), Inches(5.0))
tf_dos1 = card_dos1.text_frame
tf_dos1.word_wrap = True
tf_dos1.margin_top = Inches(0.3)
tf_dos1.margin_left = Inches(0.3)

p = tf_dos1.paragraphs[0]
p.text = "Mecanismo del Ataque"
p.font.size = Pt(14)
p.font.bold = True
p.font.color.rgb = COLOR_TEXT_MAIN
p.space_after = Pt(8)

p2 = tf_dos1.add_paragraph()
p2.text = "Aprovecha la densidad topológica nativa de los predios urbanos (hasta 222 vértices por polígono). El payload inyecta un CROSS JOIN que fuerza al motor GEOS a calcular buffers densos sin indexación GiST previa."
p2.font.size = Pt(10.5)
p2.font.color.rgb = COLOR_TEXT_MUTED
p2.space_after = Pt(14)

p3 = tf_dos1.add_paragraph()
p3.text = "Consecuencia Operativa"
p3.font.size = Pt(14)
p3.font.bold = True
p3.font.color.rgb = COLOR_RED
p3.space_after = Pt(8)

p4 = tf_dos1.add_paragraph()
p4.text = "Monopolización absoluta de workers en PostgreSQL. En instancias locales y nubes municipales de recursos reducidos, dos peticiones concurrentes inducen denegación de servicio total."
p4.font.size = Pt(10.5)
p4.font.color.rgb = COLOR_TEXT_MUTED

# Comparativa métrica en tarjetas derecha
card_metric1 = add_card(s3, Inches(5.6), Inches(1.8), Inches(6.9), Inches(2.35))
tf_m1 = card_metric1.text_frame
tf_m1.word_wrap = True
tf_m1.margin_top = Inches(0.25)
tf_m1.margin_left = Inches(0.3)

pm1 = tf_m1.paragraphs[0]
pm1.text = "API VULNERABLE (SQL DINÁMICO)"
pm1.font.size = Pt(11)
pm1.font.bold = True
pm1.font.color.rgb = COLOR_RED

pm2 = tf_m1.add_paragraph()
pm2.text = "10.8 ms  →  1,692.1 ms  (Degradación 93.5x)"
pm2.font.size = Pt(20)
pm2.font.bold = True
pm2.font.color.rgb = COLOR_TEXT_MAIN
pm2.space_after = Pt(4)

pm3 = tf_m1.add_paragraph()
pm3.text = "La latencia explota cuadráticamente al evaluar de 14,400 a 345,600 vértices en pares de polígonos."
pm3.font.size = Pt(10.5)
pm3.font.color.rgb = COLOR_TEXT_MUTED

card_metric2 = add_card(s3, Inches(5.6), Inches(4.45), Inches(6.9), Inches(2.35))
tf_m2 = card_metric2.text_frame
tf_m2.word_wrap = True
tf_m2.margin_top = Inches(0.25)
tf_m2.margin_left = Inches(0.3)

pm4 = tf_m2.paragraphs[0]
pm4.text = "ARQUITECTURA MITIGADA (PYDANTIC + GEOALCHEMY2)"
pm4.font.size = Pt(11)
pm4.font.bold = True
pm4.font.color.rgb = COLOR_GREEN

pm5 = tf_m2.add_paragraph()
pm5.text = "Latencia Acotada O(1): ~15 ms Constante"
pm5.font.size = Pt(20)
pm5.font.bold = True
pm5.font.color.rgb = COLOR_TEXT_MAIN
pm5.space_after = Pt(4)

pm6 = tf_m2.add_paragraph()
pm6.text = "El esquema neutraliza la inyección de subconsultas restringiendo los parámetros a escalares estrictos."
pm6.font.size = Pt(10.5)
pm6.font.color.rgb = COLOR_TEXT_MUTED

# ==============================================================================
# SLIDE 4: ARQUITECTURA DE MITIGACIÓN
# ==============================================================================
s4 = prs.slides.add_slide(blank_layout)
set_slide_background(s4)
add_header(s4, "Arquitectura Defensiva", "Pipeline de Defensa en Profundidad de Tres Barreras")

col_w4 = Inches(3.7)
gap4 = Inches(0.3)
barriers = [
    ("BARRERA 1", "Pydantic (Capa Web)", [
        "Tipado escalar estricto en runtime.",
        "Acotamiento de rangos físicos y coordenadas.",
        "Guardas regex contra payloads (ej. ^\\d{4}$).",
        "Retorna HTTP 422 sin tocar el motor de base de datos."
    ]),
    ("BARRERA 2", "Shapely (Memoria)", [
        "Validación topológica anticipada.",
        "Detección y descarte de geometrías auto-intersecadas.",
        "AST Spatial Sanitation sobre WKT y GeoJSON.",
        "Aislamiento preventivo ante anomalías topológicas."
    ]),
    ("BARRERA 3", "GeoAlchemy2 (Persistencia)", [
        "Compilación nativa de variables en formato binario (EWKB).",
        "Uso estricto de consultas preparadas (Prepared Statements).",
        "Separación categórica entre datos y código SQL.",
        "Reutilización de planes de ejecución en PostgreSQL."
    ])
]

for i, (tag, title, items) in enumerate(barriers):
    x = Inches(0.8) + i * (col_w4 + gap4)
    card = add_card(s4, x, Inches(1.8), col_w4, Inches(5.0))
    tf = card.text_frame
    tf.word_wrap = True
    tf.margin_top = Inches(0.3)
    tf.margin_left = Inches(0.3)
    tf.margin_right = Inches(0.3)
    
    ptag = tf.paragraphs[0]
    ptag.text = tag
    ptag.font.size = Pt(11)
    ptag.font.bold = True
    ptag.font.color.rgb = COLOR_ACCENT
    
    ptit = tf.add_paragraph()
    ptit.text = title
    ptit.font.size = Pt(15)
    ptit.font.bold = True
    ptit.font.color.rgb = COLOR_TEXT_MAIN
    ptit.space_after = Pt(14)
    
    for item in items:
        pi = tf.add_paragraph()
        pi.text = "• " + item
        pi.font.size = Pt(10.5)
        pi.font.color.rgb = COLOR_TEXT_MUTED
        pi.space_after = Pt(6)

# ==============================================================================
# SLIDE 5: BENCHMARKING DE RENDIMIENTO
# ==============================================================================
s5 = prs.slides.add_slide(blank_layout)
set_slide_background(s5)
add_header(s5, "Validación Experimental", "Benchmarking y Sobrecosto en Endpoint de Proximidad (/predios/radio)")

# Crear Tabla
rows, cols = 6, 4
left, top, width, height = Inches(0.8), Inches(1.8), Inches(7.5), Inches(3.8)
table_shape = s5.shapes.add_table(rows, cols, left, top, width, height)
table = table_shape.table

headers = ["Métrica Evaluada", "API Vulnerable", "API Mitigada", "Variación"]
data = [
    ["Throughput (Rendimiento)", "556.21 req/s", "484.36 req/s", "-12.92%"],
    ["Latencia Media (Mean)", "17.26 ms", "19.89 ms", "+2.63 ms (+15.24%)"],
    ["Percentil 50 (p50)", "15.37 ms", "18.42 ms", "+3.05 ms"],
    ["Percentil 99 (p99)", "43.75 ms", "38.24 ms", "-12.59% (Mejora)"],
    ["Tasa de Error HTTP", "0.0%", "0.0%", "0.0%"]
]

for col_idx, h in enumerate(headers):
    cell = table.cell(0, col_idx)
    cell.fill.solid()
    cell.fill.fore_color.rgb = RGBColor(241, 245, 249)
    p = cell.text_frame.paragraphs[0]
    p.text = h
    p.font.name = "Segoe UI"
    p.font.size = Pt(10.5)
    p.font.bold = True
    p.font.color.rgb = COLOR_TEXT_MAIN

for row_idx, row_data in enumerate(data):
    for col_idx, val in enumerate(row_data):
        cell = table.cell(row_idx + 1, col_idx)
        cell.fill.solid()
        cell.fill.fore_color.rgb = COLOR_CARD_BG
        p = cell.text_frame.paragraphs[0]
        p.text = val
        p.font.name = "Segoe UI"
        p.font.size = Pt(10)
        p.font.color.rgb = COLOR_TEXT_MAIN if col_idx == 0 else COLOR_TEXT_MUTED
        if col_idx == 3 and "-" in val and "Throughput" not in row_data[0]:
            p.font.bold = True
            p.font.color.rgb = COLOR_GREEN

# Panel lateral con conclusiones del benchmark
card_b_notes = add_card(s5, Inches(8.6), Inches(1.8), Inches(3.9), Inches(5.0))
tf_bn = card_b_notes.text_frame
tf_bn.word_wrap = True
tf_bn.margin_top = Inches(0.3)
tf_bn.margin_left = Inches(0.3)
tf_bn.margin_right = Inches(0.3)

pbn1 = tf_bn.paragraphs[0]
pbn1.text = "Hallazgos de Rendimiento"
pbn1.font.size = Pt(14)
pbn1.font.bold = True
pbn1.font.color.rgb = COLOR_TEXT_MAIN
pbn1.space_after = Pt(10)

b_points = [
    "Sobrecosto Asumible: El incremento medio de 2.63 ms resulta marginal frente al valor de la protección.",
    "Ganancia por Planes Compilados: La reutilización de prepared statements en PostgreSQL mejora la estabilidad en la cola inicial (-12.59% en p99).",
    "Estrés Masivo (100 clientes): La mitigada escala de forma controlada (~101 ms en p99) por el procesamiento en Python sin registrar fallos de conexión."
]

for pt in b_points:
    head, body = pt.split(": ")
    p = tf_bn.add_paragraph()
    p.text = "• " + head + ":"
    p.font.size = Pt(11)
    p.font.bold = True
    p.font.color.rgb = COLOR_TEXT_MAIN
    
    p2 = tf_bn.add_paragraph()
    p2.text = body
    p2.font.size = Pt(10)
    p2.font.color.rgb = COLOR_TEXT_MUTED
    p2.space_after = Pt(8)

# ==============================================================================
# SLIDE 6: EFICACIA DEFENSIVA Y CONCLUSIONES
# ==============================================================================
s6 = prs.slides.add_slide(blank_layout)
set_slide_background(s6)
add_header(s6, "Validación Global y Conclusiones", "Eficacia Defensiva Frente a la Tríada CIA y Cierre de la Investigación")

card_efic = add_card(s6, Inches(0.8), Inches(1.8), Inches(5.7), Inches(5.0))
tf_e = card_efic.text_frame
tf_e.word_wrap = True
tf_e.margin_top = Inches(0.3)
tf_e.margin_left = Inches(0.3)
tf_e.margin_right = Inches(0.3)

pe1 = tf_e.paragraphs[0]
pe1.text = "Eficacia de Mitigación (100% de Neutralización)"
pe1.font.size = Pt(14)
pe1.font.bold = True
pe1.font.color.rgb = COLOR_GREEN
pe1.space_after = Pt(10)

mitig_stats = [
    ("Vectores Espaciales (V1 - V3)", "100% de neutralización. Se previenen tautologías en ST_DWithin, oráculos booleanos en ST_Intersects y sobrecarga cuadrática O(N²) en ST_Buffer."),
    ("Vectores Convencionales (V4 - V6)", "100% de protección. Se blinda la integridad fiscal del autovalúo, se anulan purgas cartográficas en tg_lote y se impide la escalación administrativa."),
    ("Aislamiento Arquitectónico", "Pydantic y Shapely interceptan entradas anómalas en la aplicación, garantizando que ninguna consulta maliciosa alcance el motor PostgreSQL/PostGIS.")
]

for t, d in mitig_stats:
    p = tf_e.add_paragraph()
    p.text = "• " + t
    p.font.size = Pt(11)
    p.font.bold = True
    p.font.color.rgb = COLOR_TEXT_MAIN
    
    pd = tf_e.add_paragraph()
    pd.text = d
    pd.font.size = Pt(10)
    pd.font.color.rgb = COLOR_TEXT_MUTED
    pd.space_after = Pt(8)

card_concl = add_card(s6, Inches(6.8), Inches(1.8), Inches(5.7), Inches(5.0))
tf_c = card_concl.text_frame
tf_c.word_wrap = True
tf_c.margin_top = Inches(0.3)
tf_c.margin_left = Inches(0.3)
tf_c.margin_right = Inches(0.3)

pc1 = tf_c.paragraphs[0]
pc1.text = "Conclusiones Principales"
pc1.font.size = Pt(14)
pc1.font.bold = True
pc1.font.color.rgb = COLOR_TEXT_MAIN
pc1.space_after = Pt(10)

concl_points = [
    ("Paradigma de Seguridad", "Las funciones espaciales exigen abandonar la sanitización escalar genérica e incorporar parametrización tipada y validación topológica nativa."),
    ("Integridad del Catastro", "Neutralizar las inyecciones previene alteraciones no autorizadas en autovalúos y planos digitales vinculados a fe pública (ISO 19152 LADM)."),
    ("Compromiso Operativo", "El sobrecosto de 2.63 ms certifica la viabilidad técnica para geoportales municipales en entornos de producción.")
]

for t, d in concl_points:
    p = tf_c.add_paragraph()
    p.text = "• " + t
    p.font.size = Pt(11)
    p.font.bold = True
    p.font.color.rgb = COLOR_TEXT_MAIN
    
    pd = tf_c.add_paragraph()
    pd.text = d
    pd.font.size = Pt(10)
    pd.font.color.rgb = COLOR_TEXT_MUTED
    pd.space_after = Pt(8)

prs.save("Presentacion_Catastro_PostGIS.pptx")
print("Presentación generada exitosamente: Presentacion_Catastro_PostGIS.pptx")
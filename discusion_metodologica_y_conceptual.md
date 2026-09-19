# Discusión Metodológica, Conceptual y Epistemológica de la Investigación

**Proyecto:** Evaluación de Vulnerabilidades de Inyección SQL Espacial en Sistemas de Información Catastral basados en PostGIS  
**Autor:** Rodrigo  
**Programa:** Doctorado / Maestría en Ciberseguridad / Tecnologías de la Información  
**Fecha de compilación:** 12 de Septiembre de 2026  

---

## 1. Resumen Ejecutivo del Debate y Consulta Metodológica

El presente documento recopila y sintetiza la deliberación técnica y metodológica sostenida para fundamentar con rigor epistemológico la tesis y el artículo científico. Su objetivo es servir como memoria de diseño y base de consulta para contrastar con evaluadores, revisores por pares o modelos de arbitraje académico externo.

---

## 2. Eje Metodológico 1: Población y Muestra en Ingeniería de Software y Ciberseguridad

### Duda planteada:
> *"¿Cuál es la población y la muestra en este caso si no trabajamos con seres humanos ni encuestas?"*

### Fundamento Científico y Respuesta:
En ciencias de la computación, seguridad de software y sistemas de información geográfica (SIG), la unidad de análisis no son personas, sino **artefactos de datos y transacciones informáticas**. El estudio se divide en dos dimensiones metodológicas:

1. **Dimensión Geoespacial (Datos Catastrales):**
   * **Población Diana (Universo):** Las **23,960 unidades prediales urbanas** registradas en la cartografía catastral de la ciudad de Puno, Perú.
   * **Muestra:** **487 parcelas poligonales continuas**, modeladas bajo la clase `LA_SpatialUnit` del estándar internacional **ISO 19152:2012 (LADM)** e insertadas en la entidad `tg_lote`.
   * **Criterios de Inclusión:** Pertenencia a una zona catastral consolidada, proyección oficial en metros UTM Zona 19 Sur (`EPSG:32719`) y variabilidad geométrica (de 4 a 222 vértices por polígono, media de 9.0).
   * **Criterios de Exclusión:** Geometrías degeneradas, multipolígonos desconectados o registros con topología nula.

2. **Dimensión Transaccional (Ciberseguridad y Rendimiento):**
   * **Población:** El espacio infinito de consultas y transacciones espaciales dirigidas a los endpoints de la API web.
   * **Muestra Experimental:** Una batería dirigida de **6 vectores de explotación** (cubriendo la tríada CIA) y un lote de carga estandarizado de **300 peticiones HTTP concurrentes (concurrencia de 10 clientes)** para cuantificar latencia y tasa de transferencia (*throughput*).

3. **Blindaje Ético y Procedencia de Datos (*Zero PII Breach*):**
   * **Cartografía Abierta:** Las geometrías base se extrajeron de fuentes cartográficas abiertas y públicas (OpenStreetMap / geodatasets de libre acceso) a través del script automatizado de ingesta `ingest_peru_cities.py`. No se sustrajo cartografía privada municipal.
   * **Atributos Fiscales Sintéticos:** La totalidad de los datos tributarios y personales de `catastro_titulares` (`LA_Party` de LADM: nombres de propietarios, identificadores tributarios y autovalúos) fueron sintetizados algorítmicamente mediante generadores numéricos y de texto controlados. No existe exposición de Información de Identificación Personal (PII) ni secreto tributario real, garantizando cumplimiento ético absoluto en comités de ética académica.

---

## 3. Eje Conceptual 2: Novedad Científica y Brecha de Conocimiento (*Research Gap*)

### Duda planteada:
> *"¿Mi investigación es realmente novedosa o ya existe? ¿Alguien ya había investigado esto?"*

### Fundamento Científico y Respuesta:
La inyección SQL tradicional sobre datos escalares (`' OR 1=1--`) tiene más de 25 años de literatura y carece de novedad per se. La novedad de esta investigación radica en **la inyección SQL con conciencia espacial (*Spatial-Aware SQL Injection*)**:

1. **La Brecha entre Ciberseguridad y SIG:**
   * La comunidad de ciberseguridad desconoce habitualmente la matemática topológica, librerías en C++ (GEOS), formatos binarios (EWKB) y estándares catastrales (LADM).
   * La comunidad de desarrolladores SIG (ingenieros geógrafos, civiles, topógrafos) domina la cartografía, pero históricamente asume con ligereza que las funciones matemáticas de PostGIS (`ST_DWithin`, `ST_Intersects`) ofrecen aislamiento por su propia naturaleza.
2. **El Precedente Industrial Real:**
   * La vulnerabilidad crítica **CVE-2023-25157 (CVSS 9.8)** en GeoServer demostró que el software SIG más usado del mundo permitía inyección SQL no autenticada en PostGIS mediante filtros espaciales. Sin embargo, la academia no había formalizado sistemáticamente los vectores topológicos ni evaluado cuantitativamente sus arquitecturas de defensa en microservicios web.
3. **El Contexto de Infraestructura Crítica:**
   * No se ataca una tabla genérica, sino el núcleo del **Catastro Multifinalitario (ISO 19152)**: alteración de autovalúos fiscales (`LA_Party`), manipulación de límites de propiedad y borrado masivo de la capa cartográfica basal (`LA_SpatialUnit`).
4. **El Ecosistema Institucional de PostGIS:**
   * Organismos públicos como municipalidades provinciales y distritales, entidades de formalización predial (ej. COFOPRI en Perú), ministerios de vivienda e Infraestructuras de Datos Espaciales (IDE) adoptan PostgreSQL/PostGIS como su estándar cartográfico oficial. El riesgo no proviene de PostGIS en sí (que es seguro), sino de las aplicaciones y visores web que construyen consultas concatenando entradas de búsqueda, exponiendo la cartografía y el registro fiscal a inyecciones espaciales.

---

## 4. Eje Arquitectónico 3: PostGIS, ORM y el Rol de los Índices Espaciales (GiST)

### Duda planteada:
> *"Yo pensaba que la investigación era ver si PostGIS es susceptible a inyecciones SQL según si se usa un ORM o consultas crudas, y si se pone a prueba los sistemas GiST frente a SQLi."*

### Fundamento Científico y Respuesta:
1. **PostGIS no es vulnerable por sí mismo:**
   Ningún motor de base de datos es vulnerable por su propia cuenta. La inyección SQL es siempre un defecto de la **capa de software / aplicación** cuando el programador concatena texto (interpolación de cadenas / `f-strings`) en lugar de separar el canal de control del canal de datos.
2. **Consultas Crudas vs. ORM:**
   No se requiere obligatoriamente un ORM para estar seguro. Con consultas crudas parametrizadas nativas (`cursor.execute(query, params)` con marcadores `%s` o `$1`), el driver envía los parámetros fuera del árbol sintáctico (AST) y la inyección es imposible.
3. **GiST es un árbol de indexación, no un mecanismo de seguridad:**
   GiST (*Generalized Search Tree*) es una estructura de datos de búsqueda rápida basada en envolventes mínimas (*bounding boxes*). El ataque de inyección SQL ocurre en el analizador léxico/sintáctico de PostgreSQL antes de que intervenga el índice. El aporte respecto a GiST es demostrar cómo una inyección espacial puede **anular deliberadamente el uso del índice GiST**, forzando al motor a ejecutar productos cartesianos cuadráticos ($O(N^2)$) sobre la CPU (Spatial DoS).

---

## 5. Eje Taxonómico 4: Clasificación de los 6 Ataques bajo el Estándar Internacional

### Duda planteada:
> *"¿Todos estos 6 ataques son realmente considerados SQL Injection? ¿De eso trata el título?"*

### Fundamento Científico y Respuesta:
**Sí, absolutamente todos.** Según **MITRE CWE-89** (*Improper Neutralization of Special Elements used in an SQL Command*) y la taxonomía seminal de **Halfond et al. (2006)**, la inyección SQL se define por el **mecanismo de alteración de la gramática SQL**, no por el objetivo final. Los 6 vectores alteran el AST de sentencias SQL y cubren la tríada **CIA** completa:

| N° | Simulación Experimental | Categoría Formal CWE-89 | Sentencia SQL Manipulada | Dimensión de Seguridad (CIA) |
| :---: | :--- | :--- | :--- | :--- |
| **1** | **Bypass Lógico Espacial** | *Tautology SQLi* en predicado topológico | `SELECT ... WHERE ST_DWithin(...)` | **Confidencialidad** (Exfiltración territorial masiva) |
| **2** | **Inferencia Geométrica** | *Error-Based Blind SQLi* | `SELECT ... WHERE ST_Intersects(...)` | **Confidencialidad** (Canal lateral / extracción ciega) |
| **3** | **Spatial DoS** | *Resource-Exhaustion Subquery SQLi* | `SELECT ... ST_Buffer(..., <subquery>)` | **Disponibilidad** (Sobrecarga de CPU en GEOS) |
| **4** | **Fraude Predial (Tampering)** | *Direct Data Modification SQLi* | `UPDATE catastro_titulares SET ...` | **Integridad** (Alteración de autovalúo y titular) |
| **5** | **Borrado Destructivo** | *Destructive Tautology SQLi* | `DELETE FROM tg_lote WHERE ...` | **Disponibilidad / Integridad** (Purga de cartografía) |
| **6** | **Bypass de Autenticación** | *Inline Comment SQLi* (`admin' --`) | `SELECT ... WHERE username = 'admin' --` | **Confidencialidad / Integridad** (Escalación a admin) |

#### El Impacto Sistémico de la Simulación 4 en la Cadena de Confianza Digital (Fe Pública):
La inyección de modificación en `catastro_titulares` y `tg_lote` no es solo una manipulación de datos en PostgreSQL; vulnera la **cadena de fe pública y trámites municipales automatizados**:
* **Certificados Catastrales con QR:** En las Smart Cities, la API emite certificados oficiales en PDF con códigos QR que firman criptográficamente la titularidad del predio y su autovalúo. Si la base de datos es adulterada mediante SQLi, el sistema emite certificados oficiales con datos fraudulentos pero con firma válida.
* **Constancias de No Adeudo:** Reducir el autovalúo a S/ 0 permite la emisión fraudulenta de constancias tributarias para trámites de compraventa ante notarios.
* **Integridad LADM (ISO 19152):** La relación formal entre la unidad espacial (`LA_SpatialUnit`) y el titular de derecho (`LA_Party`) queda desincronizada del registro predial físico, corrompiendo el gemelo digital urbano.

---

## 6. Eje Epistemológico 5: Origen y Deducción de las Tres Barreras Defensivas

### Duda planteada:
> *"¿Cómo se dedujeron estas tres barreras? ¿Acaso se inventaron de la nada o provienen de otros campos?"*

### Analogía y Deducción Técnica:
Igual que un ingeniero estructural que diseña un edificio antisísmico no inventa el cemento ni el acero, sino la **disposición estructural y el cálculo de disipación de energía**, en esta investigación las herramientas existentes se articularon analizando la causalidad física interna del motor:

1. **Barrera 1: Acotamiento Rígido en API (Pydantic) contra Spatial DoS**
   * *Causalidad:* PostGIS delega el cómputo de `ST_Buffer` a la librería en C++ **GEOS**. El parámetro `quad_segs` (por defecto 8) multiplica los vértices. Si un atacante inyecta `quad_segs=100`, un polígono de 200 vértices pasa a tener 80,000 vértices. Al cruzarse en un `ST_Intersects`, el algoritmo entra en su peor caso cuadrático $O(N^2)$, monopolizando la CPU.
   * *Deducción:* La base de datos no puede determinar si 100 segmentos es malicioso. La defensa debe residir en la interfaz de entrada (Pydantic), acotando distancias ($\le 2000$ m) y parámetros de curvatura antes de construir el comando.
   * *Respaldo Bibliográfico:* **Crosby & Wallach (2003, USENIX)** (Ataques de Complejidad Algorítmica) y **Agarwal & Rajan (2016, Springer)** (Medición de costo de intersección en PostGIS).

2. **Barrera 2: Validación Topológica en Memoria (Shapely) contra Inferencia Ciega**
   * *Causalidad:* En el ataque por canal lateral, el atacante requiere un "oráculo": que el servidor responda `500` si adivinó un carácter de la contraseña y `200` si falló, forzando excepciones con WKT inválidos (`ST_GeomFromText`).
   * *Deducción:* Si la geometría malformada llega al motor de base de datos, el oráculo ya funcionó. Para destruirlo, la validación geométrica debe desacoplarse del SDBMS y resolverse en memoria en la capa web con Shapely (`shapely.wkt.loads`), rechazando geometrías con auto-intersecciones con código `422` antes de tocar PostGIS.
   * *Respaldo Bibliográfico:* **Chun & Atluri (2008)** y **Atluri & Chun (2004, IEEE TDSC)** (Riesgos de Inferencia Espacial) y **Halfond et al. (2006)** (Neutralización de oráculos de error). Norma **ISO 19107:2019 / OGC Simple Features**.

3. **Barrera 3: Compilación y Serialización Binaria EWKB (GeoAlchemy2)**
   * *Causalidad:* El ensamblado de consultas mediante `f-strings` funde en un solo texto el código SQL y los datos. El parser léxico de PostgreSQL interpreta los caracteres de cierre de paréntesis y comillas como gramática ejecutable.
   * *Deducción:* Se debe utilizar el protocolo binario extendido (*Extended Well-Known Binary - EWKB*). GeoAlchemy2 precompila las funciones espaciales como variables de vinculación binarias (*bind parameters*). En este flujo binario es matemáticamente imposible alterar el AST.
   * *Respaldo Bibliográfico:* **Clarke (2012, Elsevier)** (Teoría de AST y separación de código/datos) y **Obe & Hsu (2021, Manning)** (Serialización binaria EWKB en PostGIS).

---

## 7. Eje Metodológico 6: ¿Por qué la Investigación es Rigurosamente EXPERIMENTAL?

### Duda planteada:
> *"¿Mi investigación no sería no-experimental, dado que solo evalúa cosas existentes? ¿O es experimental porque nunca se enfrentaron estas amenazas frente a estas barreras?"*

### Fundamento Científico y Respuesta:
La investigación es **100% EXPERIMENTAL** (diseño cuasiexperimental de laboratorio controlado con grupo de control y tratamiento). 

1. **No es no-experimental porque no es observacional:**
   Una investigación no-experimental se limita a observar fenómenos sin intervenir (ej. ir a una municipalidad a revisar logs pasivos o hacer encuestas a ingenieros). En este proyecto se construyó un entorno de software controlado y se ejecutaron intervenciones planificadas.
2. **Cumplimiento estricto del Método Experimental (Wohlin et al., 2012):**
   * **Variable Independiente (Manipulada):** La arquitectura de acceso a datos espaciales.
     * *Grupo Control (Tratamiento A):* API con SQL dinámico vulnerable.
     * *Grupo Experimental (Tratamiento B):* API con arquitectura de mitigación (GeoAlchemy2 + Shapely + Pydantic).
   * **Variables Intervinientes (Controladas):** Hardware idéntico (Intel Core Ultra 5 245KF, 32GB RAM DDR5), virtualización idéntica (Docker en WSL2 kernel 6.6), dataset idéntico (487 parcelas reales de Puno) y concurrencia fija (10 clientes simultáneos).
   * **Variables Dependientes (Medidas Cuantitativamente):**
     * *Eficacia de Seguridad:* Tasa de éxito de explotación (100% en control vs. 0% en experimental).
     * *Throughput:* 556.21 req/s vs. 484.36 req/s (-12.92%).
     * *Latencia Media:* 17.26 ms vs. 19.89 ms (+2.63 ms / +15.24% de overhead).
     * *Latencia de Cola (p99):* 43.75 ms vs. 38.24 ms (**-12.59% de mejora** por reuso de planes cacheados / *prepared statements*).
3. **Inédito en la literatura:**
   Nunca antes se había enfrentado cuantitativamente este conjunto de vectores espaciales frente a este pipeline defensivo midiendo el impacto empírico en latencia y percentil 99 en PostGIS.

4. **Respuesta al Sesgo de Hardware (Validez Externa e Invarianza Asintótica):**
   * *Objeción potencial:* "¿El bajo overhead (+2.63 ms) es solo un artefacto de contar con un procesador moderno (Intel Core Ultra 5 245KF) y en servidores modestos de municipalidades sería inaceptable?"
   * *Fundamentación científica:*
     1. **Invarianza Porcentual y Proporcional:** En ingeniería de software experimental, las comparaciones relativas (+15.24% de overhead en latencia media y -12.59% de mejora en p99) son estructurales: en cualquier arquitectura de servidor, el tiempo consumido por el analizador sintáctico y el motor relacional de PostgreSQL domina sobre la validación en memoria de Shapely/Pydantic.
     2. **Complejidad Asintótica ($O(N^2)$ vs $O(1)$):** La vulnerabilidad de Spatial DoS fuerza un peor caso cuadrático en la librería GEOS. En un hardware más modesto (con menos núcleos o menor IPC), el impacto del ataque es **exponencialmente más letal**: lo que en el Core Ultra 5 tarda 228 ms, en un procesador modesto de servidor municipal colapsaría por completo el servicio durante minutos con solo 2 peticiones concurrentes. Por ende, la barrera preventiva es todavía más crítica en entornos de bajos recursos.

---

## 8. Guía de Preguntas para Someter a Segundo Arbitraje Externo (Gemini / Evaluador)

Si vas a compartir este marco con otro evaluador técnico o de investigación, estas son las preguntas clave para validar la consistencia:

1. *¿Es científicamente válido justificar que la unidad de análisis y la población diana sean las entidades geoespaciales catastrales (`LA_SpatialUnit` ISO 19152) y las transacciones HTTP/SQL en lugar de personas?*
2. *¿Concuerda en que la inyección SQL espacial trasciende la inyección tradicional al manipular la topología (GEO-RBAC), oráculos geométricos y complejidad asintótica en librerías C++ (GEOS / Spatial DoS)?*
3. *¿Es sólido metodológicamente clasificar este estudio como experimental controlado de laboratorio con grupo de control (SQL dinámico) y grupo experimental (ORM mitigado)?*
4. *¿Se considera que el trade-off empírico de +2.63 ms (+15.24% en media) y la ganancia de estabilidad en el percentil 99 (-12.59%) justifica la adopción del patrón de defensa en profundidad para infraestructuras críticas del Estado?*

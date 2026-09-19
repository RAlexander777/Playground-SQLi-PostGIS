# Evaluación de Vulnerabilidades de Inyección SQL Espacial en Sistemas de Información Catastral basados en PostGIS

**Rodrigo [Filiación / Datos del Autor]**  
*Universidad / Programa de Doctorado*  
*Correo electrónico institucional*  

---

### Resumen
La integración de bases de datos espaciales en arquitecturas web ha ampliado la superficie de ataque para las aplicaciones modernas; sin embargo, los riesgos específicos asociados a las inyecciones SQL espaciales siguen estando poco explorados. Este artículo investiga la explotación y mitigación de inyecciones SQL espaciales dentro de sistemas de información catastral que utilizan PostGIS. Se desarrolló un entorno de prueba en contenedores, utilizando Docker, para simular una API de infraestructura crítica construida con Python (FastAPI) y PostgreSQL/PostGIS. El estudio demuestra cómo los atacantes pueden aprovechar funciones espaciales (por ejemplo, ST_DWithin, ST_Intersects) para manipular la lógica geoespacial, extraer datos de zonificación no autorizados o inducir estados de denegación de servicio. Además, la investigación evalúa el impacto en el rendimiento al implementar estrategias de mitigación robustas, comparando consultas espaciales dinámicas vulnerables con consultas parametrizadas ejecutadas a través de herramientas de Mapeo Objeto-Relacional (ORM) como SQLAlchemy y GeoAlchemy2. Los resultados demuestran que el pipeline propuesto neutralizó el 100% de los vectores de ataque con un sobrecosto medio de latencia de 2.63 ms (+15.24%) y una mejora del 12.59% en la estabilidad de cola (p99). Se concluye que la mitigación efectiva de inyecciones espaciales no depende de cortafuegos perimetrales genéricos (WAF), sino de trasladar la validación topológica y la parametrización tipada a la capa de aplicación (ORM), garantizando la integridad catastral con un impacto operativo marginal.

**Keywords:** Inyecciones espaciales; Sistemas catastrales; Ciberseguridad geoespacial; Pruebas de penetración; Bases de datos

---

## 1. Introducción

Los sistemas de información catastral modernos exponen servicios web y geoportales sobre arquitecturas cliente-servidor para administrar la propiedad predial, la zonificación urbana y la recaudación fiscal (Lemmen et al., 2015). En este ámbito, PostgreSQL junto a su extensión espacial PostGIS constituyen la solución de código abierto predominante para la persistencia y consulta de cartografía vectorial oficial (Obe & Hsu, 2021).

Sin embargo, la exposición de estos servicios mediante APIs REST introduce vectores de ataque cuando las consultas se construyen mediante concatenación de cadenas dentro de funciones espaciales. Si bien la inyección SQL clásica ha sido ampliamente documentada (Clarke, 2012; Halfond et al., 2006; OWASP Foundation, 2021), la manipulación de operadores geométricos de PostGIS —como `ST_DWithin`, `ST_Intersects` o `ST_Buffer`— presenta particularidades poco atendidas: una entrada no saneada no solo permite eludir filtros relacionales o exfiltrar datos, sino también desencadenar estados de denegación de servicio mediante cálculos topológicos de alta complejidad algorítmica.

Este artículo presenta una evaluación experimental de vulnerabilidades de inyección SQL espacial en sistemas catastrales sobre PostGIS. El estudio: (1) documenta y evalúa seis vectores de ataque orientados a la tríada CIA (Confidencialidad, Integridad y Disponibilidad); (2) implementa un banco de pruebas reproducible sobre un dataset de 487 parcelas urbanas estructuradas bajo el estándar ISO 19152 (LADM); y (3) cuantifica el impacto en latencia y throughput de una arquitectura de mitigación basada en compilación tipada en ORM (GeoAlchemy2) y validación previa con Shapely y Pydantic.

---

## 2. Trabajos Relacionados

La investigación converge en cuatro líneas temáticas fundamentales:

### 2.1. Inyección SQL en Motores Espaciales y Operadores Topológicos
La literatura fundamental en seguridad informática ha establecido clasificaciones sólidas para ataques SQLi. Halfond et al. (2006) clasificaron estas agresiones en tautologías, consultas de unión, inyecciones ciegas (blind) y canalización de procedimientos almacenados. Clarke (2012) profundizó en el análisis de los árboles de sintaxis abstracta (AST) generados por los analizadores sintácticos de bases de datos al concatenar parámetros no saneados. Sin embargo, estos marcos no consideran cómo los operadores algebraicos espaciales (Egenhofer, 1994) redefinen las condiciones lógicas de evaluación. A diferencia de un valor escalar simple, una expresión geométrica procesa múltiples dimensiones, sistemas de referencia espacial (SRID) y envolventes mínimas (bounding boxes), lo que amplía el área de escape sintáctico. Este vacío teórico en los modelos tradicionales de inyección deja sin caracterizar la manipulación de predicados topológicos nativos en motores relacionales.

### 2.2. Modelos de Control de Acceso y Brechas de Inferencia Geoespacial
El control de acceso en bases de datos espaciales ha sido conceptualizado formalmente por Bertino et al. (2005) a través del modelo GEO-RBAC (*Spatially Aware Role-Based Access Control*), el cual demostró que los permisos de lectura y modificación deben subordinarse a fronteras geográficas dinámicas. Complementariamente, Chun y Atluri (2008) y Atluri y Chun (2004) analizaron los riesgos de inferencia espacial en SDBMS, donde un usuario no autorizado puede deducir la existencia o atributos de un objeto protegido correlacionando consultas espaciales sucesivas. No obstante, estas aproximaciones asumen que la capa de servicio traslada fielmente las políticas espaciales a la base de datos; en arquitecturas web modernas, la concatenación insegura anula directamente el control de acceso en la persistencia sin ser detectada por los mecanismos de autorización de la capa de aplicación.

### 2.3. Integridad y Modelado de Datos Catastrales bajo el Estándar LADM
El modelado técnico de los sistemas de información catastral se rige a nivel internacional por el estándar ISO 19152:2012, conocido como *Land Administration Domain Model* (LADM). Autores de referencia como Lemmen et al. (2015) y van Oosterom et al. (2006) formalizaron las clases fundamentales del catastro, destacando `LA_SpatialUnit` (parcelas y lotes) y `LA_Party` (titulares prediales), extendidas posteriormente hacia modelos de valoración masiva automatizada (Kara et al., 2021). Si bien el estándar prescribe la semántica e interoperabilidad de la información territorial y registral, no define salvaguardas arquitectónicas a nivel de consulta contra ataques de inyección, dejando expuesta la integridad de los derechos reales de propiedad y la recaudación fiscal ante fallas en la implementación de software.

### 2.4. Ataques de Complejidad Algorítmica y Vulnerabilidades en Servicios OGC
La relevancia contemporánea de esta amenaza quedó demostrada en la industria mediante la vulnerabilidad crítica CVE-2023-25157 (con puntaje CVSS de 9.8), donde el software de referencia GeoServer permitía la ejecución remota de SQL no autenticado mediante la evaluación insegura de filtros OGC y expresiones CQL sobre bases de datos PostGIS (National Vulnerability Database, 2023). Por otro lado, en el ámbito de la denegación de servicio, Crosby y Wallach (2003) establecieron el concepto de ataques de complejidad algorítmica (*Algorithmic Complexity Attacks*), demostrando cómo entradas diseñadas pueden forzar a los algoritmos de peor caso ($O(N^2)$) a monopolizar la CPU. En motores espaciales, como documentan Agarwal y Rajan (2016), los algoritmos computacionales de la librería GEOS subyacente en PostGIS demandan una carga de cómputo cuadrática cuando se ejecutan sobre polígonos complejos desprovistos de filtrado preliminar por índice espacial GiST. Pese a estos antecedentes, la literatura no ha cuantificado el impacto de latencia ni ha formalizado esquemas defensivos integrados entre el analizador web y el motor geométrico.

---

## 3. Metodología

### 3.1. Enfoque y Diseño Experimental
Se adoptó un diseño experimental y cuantitativo orientado a evaluar la susceptibilidad de endpoints geoespaciales ante inyecciones SQL y medir el impacto en rendimiento derivado de un esquema de mitigación multicapa. La evaluación contrasta tres escenarios defensivos: (1) servicio vulnerable sin protección, (2) servicio protegido perimetralmente mediante un cortafuegos de aplicaciones web (WAF) basado en firmas (OWASP CRS v3.3), y (3) servicio mitigado mediante el pipeline de aplicación propuesto (ORM con validación tipada y topológica previa).

### 3.2. Conjunto de Datos Catastrales (Dataset)
El dataset experimental comprende 487 lotes catastrales urbanos continuos estructurados bajo el estándar ISO 19152 (LADM, clase `LA_SpatialUnit`) y georreferenciados en `EPSG:32719`. El esquema relacional de pruebas se estructuró en tres entidades: `tg_lote` (persistencia de los 487 lotes prediales bajo la clase `LA_SpatialUnit`), `catastro_titulares` (información alfanumérica fiscal y de autovalúo bajo la clase `LA_Party`) y `catastro_usuarios` (gestión de accesos y credenciales operativas). Las geometrías presentan una complejidad de entre 4 y 222 vértices (promedio: 9.0 vértices por polígono). Para garantizar reproducibilidad y resguardo ético, la cartografía base se obtuvo de fuentes abiertas y los atributos fiscales fueron generados proceduralmente sin incorporar información personal identificable (PII).

### 3.3. Entorno Experimental y Arquitectura
El banco de pruebas se implementó en contenedores Docker mediante microservicios aislados: (1) un servicio de base de datos con PostgreSQL 15 y PostGIS 3.3, (2) una API en Python 3.11 con FastAPI y Uvicorn, y (3) un proxy reverso Nginx configurado con el módulo ModSecurity v3 y el conjunto de reglas perimetrales OWASP Core Rule Set (CRS v3.3). Las pruebas de estrés se ejecutaron en un entorno controlado de 14 núcleos a 5.2 GHz con 32 GB de RAM DDR5 sobre Linux kernel 6.6 (WSL2). El código fuente, dataset y playground interactivo están disponibles en: https://github.com/RAlexander777/Playground-SQLi-PostGIS.

### 3.4. Vectores de Prueba y Métricas de Rendimiento
Se estructuraron seis vectores de explotación basados en las directrices de prueba de inyección de la Web Security Testing Guide (OWASP Foundation, 2023), orientados a las tres dimensiones de la tríada CIA (Confidencialidad, Integridad y Disponibilidad). La batería experimental comprendió dos categorías de vectores: (a) vectores de inyección espacial directa (V1 a V3), dirigidos contra predicados topológicos nativos y funciones de análisis geométrico en PostGIS; y (b) vectores de inyección SQL convencional aplicados al flujo transaccional y administrativo del catastro (V4 a V6), utilizados como línea base de control para verificar la integridad del modelo de datos y la capacidad de detección de herramientas perimetrales. La evaluación de rendimiento contempló una batería de carga de 300 peticiones y curvas de concurrencia escalonada (1 a 100 clientes) sobre el endpoint de proximidad territorial (`/predios/radio`), registrando métricas de latencia (media, p50, p95, p99) y throughput (req/s). La caracterización técnica de los seis vectores de explotación, sus endpoints y los payloads representativos se detallan en el Apéndice 1.

---

## 4. Simulaciones de Ataque y Resultados de Explotación (Fase 1)

### 4.1. Simulación 1: Evasión de Límite Espacial (Spatial Logic Bypass)
* **Escenario Operativo:** La API expone el endpoint `GET /api/v1/vulnerable/predios/radio`, destinado a retornar lotes catastrales dentro de un radio de 50 metros restringido exclusivamente al sector `'0101'`.
* **Mecanismo del Ataque:** El vector de ataque aprovecha el parámetro `distancia` para cerrar prematuramente el paréntesis de la función `ST_DWithin` e insertar una tautología lógica que anula tanto el radio como el filtro de sectorización:
  $$\text{Payload:} \quad \texttt{50) OR 1=1 --}$$
* **Resultado:** La consulta resultante neutraliza la restricción territorial `cod_sector = '0101'`. Mientras la consulta legítima retornó 8 parcelas locales, el payload forzó a la base de datos a realizar un escaneo secuencial completo, exfiltrando la totalidad de los predios catastrales, incluyendo zonas protegidas y sectores comerciales de acceso restringido.

### 4.2. Simulación 2: Inferencia de Datos por Errores Geométricos (Error-Based Spatial SQLi)
* **Escenario Operativo:** El endpoint `GET /api/v1/vulnerable/predios/poligono` recibe un polígono en formato WKT (*Well-Known Text*) para verificar intersección espacial (`ST_Intersects`). La API no retorna datos alfanuméricos de texto, sino únicamente vectores geométricos para visualización cartográfica, impidiendo ataques directos mediante `UNION SELECT`.
* **Mecanismo del Ataque:** Se diseñó un payload inferencial que fuerza una condición booleana ciega. Si la conjetura sobre un carácter de la contraseña del administrador es correcta, se invoca una función con geometría inválida en PostGIS (`ST_GeomFromText` con topología corrupta o un casteo de tipo ilegal), desencadenando una excepción de motor y un código de estado HTTP 500. Si la conjetura es falsa, PostGIS evalúa una rama inocua y responde con HTTP 200:
  $$\text{Payload:} \quad \texttt{POLYGON(...)', 32719)) AND 1=(CASE WHEN (SELECT SUBSTR(password\_hash, 1, 1)...)='a' THEN CAST(ST\_GeomFromText('ERR') AS INT) ELSE 1 END) --}$$
* **Resultado:** Mediante un script automatizado en Python, el atacante logró exfiltrar el hash criptográfico y el nombre de usuario administrativo (`admin`) en menos de 45 segundos, demostrando que la ausencia de salidas textuales no protege contra la exfiltración cuando los errores de PostGIS son reflejados por el servidor web.

### 4.3. Simulación 3: Denegación de Servicio Espacial (Spatial DoS)
* **Escenario Operativo:** El endpoint `GET /api/v1/vulnerable/predios/analisis-expansion` realiza operaciones de análisis geométrico.
* **Mecanismo del Ataque:** El atacante inyecta una subconsulta que computa un producto cruzado espacial $O(N^2)$ con buffers de alta densidad de segmentos sobre polígonos no indexados:
  $$\text{Payload:} \quad \texttt{10 + (SELECT COUNT(*) FROM tg\_lote a CROSS JOIN tg\_lote b WHERE ST\_Intersects(ST\_Buffer(a.geom, 5, seg), ST\_Buffer(b.geom, 5, seg)) ...)}$$
* **Resultado:** Como se evidencia empíricamente en la Figura 1, para aislar el coste computacional del producto cartesiano sin inducir un bloqueo permanente del servidor de pruebas, la inyección evaluó un subconjunto sistemático de 20 parcelas cruzadas entre sí (400 pares de polígonos), variando la resolución de vértices en el buffer. Esta inyección del producto cartesiano desencadena una explosión cuadrática $O(N^2)$ que eleva la latencia desde 10.8 ms hasta 1,692.1 ms a medida que los vértices evaluados en el buffer crecen de 14,400 a más de 345,600 puntos, saturando los workers de PostgreSQL en el procesador Intel Core Ultra 5 245KF. En contraste, la arquitectura mitigada preserva una latencia acotada de ~15 ms al restringir los parámetros a escalares validados mediante Pydantic y GeoAlchemy2.
 
![Figura 1: Curva de degeneración algorítmica cuadrática O(N²) en PostGIS/GEOS ante inyección de sobrecarga geométrica vs. mitigación acotada](figures/fig3_spatial_dos_complexity.png)  
*Figura 1. Curva de degeneración algorítmica cuadrática O(N²) en PostGIS/GEOS ante inyección de sobrecarga geométrica vs. mitigación acotada*

### 4.4. Simulación 4: Fraude en Ficha Catastral (Tampering de Autovalúo y Titularidad)
* **Escenario Operativo:** El endpoint `POST /api/v1/vulnerable/ficha/modificar` permite actualizar datos prediales mediante concatenación directa en la cláusula `SET`.
* **Mecanismo del Ataque:** Un atacante manipula el parámetro numérico de autovalúo y el nombre del titular para adjudicarse el predio y reducir fraudulentamente la deuda fiscal a cero:
  $$\text{Payload:} \quad \texttt{id\_lote = '21010101000000', nuevo\_autovaluo = 0, nuevo\_titular = 'HACKER\_TERRENOS\_ILEGAL'}$$
* **Resultado:** La base de datos actualizó el registro fiscal sin validación de tipos ni de integridad de esquema. En contraste, el endpoint mitigado con SQLAlchemy forzó validación de rangos (`gt=0`) y expresiones regulares alfabéticas, bloqueando el fraude con código HTTP 422.

### 4.5. Simulación 5: Borrado Masivo de Cartografía Predial (Data Destruction)
* **Escenario Operativo:** El endpoint `DELETE /api/v1/vulnerable/predios/borrar` recibe un identificador de sector para depuración de capas cartográficas.
* **Mecanismo del Ataque:** Mediante interpolación de cadenas, se inyecta una tautología en la cláusula `WHERE` del comando `DELETE`:
  $$\text{Payload:} \quad \texttt{filtro\_sector = '0101' OR '1'='1'}$$
* **Resultado:** La consulta se convirtió en una eliminación incondicional (`DELETE FROM tg_lote WHERE cod_sector = '0101' OR '1'='1'`), suprimiendo los 487 registros de la tabla y dejando el visor webmapping sin cartografía. En el sistema mitigado, el parámetro fue tipado estrictamente con el patrón regex `^\d{4}$` y compilado mediante `delete(TgLote).where(...)`, impidiendo el borrado masivo.

### 4.6. Simulación 6: Evasión de Autenticación en el Visor Catastral (Authentication Bypass)
* **Escenario Operativo:** El endpoint `POST /api/v1/vulnerable/auth/login` valida credenciales para otorgar acceso a capas privadas de catastro.
* **Mecanismo del Ataque:** El atacante inyecta una secuencia de comentario en el campo de usuario:
  $$\text{Payload:} \quad \texttt{username = admin' --, password = cualquier\_valor}$$
* **Resultado:** La verificación de la contraseña fue anulada en la sentencia SQL, otorgando acceso inmediato y emitiendo un token con rol `superadmin_catastro`. El endpoint mitigado implementó parametrización de credenciales con hashing criptográfico SHA-256, neutralizando el acceso ilícito.

---

## 5. Estrategias de Mitigación y Evaluación de Rendimiento (Fase 2)

### 5.1. Rediseño Arquitectónico Seguro
Como se ilustra en la Figura 2, la mitigación arquitectónica integró un pipeline de defensa en profundidad con tres barreras secuenciales en el módulo `src/api/mitigated.py`, donde la Barrera 2 (Shapely) opera como filtro de integridad topológica en memoria activado específicamente ante cargas útiles geométricas complejas (WKT o GeoJSON, descartando anomalías o geometrías auto-intersecadas con HTTP 422 antes de interactuar con la base de datos), mientras que los parámetros puramente numéricos o alfanuméricos transitan directamente desde la validación estricta de Pydantic (Barrera 1) hacia la compilación de variables tipadas (EWKB) y sentencias preparadas en GeoAlchemy2 y SQLAlchemy (Barrera 3):
1. **Barrera 1 (Acotamiento Rígido en Pydantic):** Restricciones estrictas de tipo y rangos numéricos (`gt=0, le=2000` para distancias; expresiones regulares `^\d{4}$` para identificadores de sector), eliminando la superficie de inyección de modificadores como `quad_segs`.
2. **Barrera 2 (Validación Previa de Topología con Shapely):** Para los endpoints que reciben datos vectoriales (WKT/GeoJSON), se incorporó un validador en memoria de aplicación utilizando Shapely (`shapely.wkt.loads`). Las geometrías con auto-intersecciones o sintaxis corrupta se descartan con un error HTTP 422 antes de interactuar con la base de datos.
3. **Barrera 3 (Parametrización Nativa con GeoAlchemy2 y SQLAlchemy):** Se reemplazó el ensamblado manual de consultas SQL por compilación con *bind variables* binarias (EWKB), garantizando que el motor de la base de datos interprete la entrada estrictamente como dato literal y permitiendo al planificador reutilizar sentencias preparadas (*prepared statements*).

![Figura 2: Arquitectura del pipeline de defensa en profundidad de tres barreras para servicios catastrales en PostGIS](figures/fig1_defense_pipeline.png)  
*Figura 2. Arquitectura del pipeline de defensa en profundidad de tres barreras para servicios catastrales en PostGIS*

### 5.2. Benchmarking y Análisis de Latencia
Para la evaluación empírica de rendimiento y latencia (Tabla 1 y Figura 3), se seleccionó como escenario representativo de alta frecuencia transaccional el endpoint de consulta espacial por radio (`GET /api/v1/vulnerable/predios/radio` frente a `GET /api/v1/mitigated/predios/radio`), evaluando peticiones válidas bajo una carga estandarizada de 300 peticiones con 10 clientes concurrentes. Los resultados se resumen en la Tabla 1.

**Tabla 1: Comparativa de Rendimiento y Latencia entre API Vulnerable y API Mitigada**

| Métrica de Rendimiento | API Vulnerable (SQL Dinámico) | API Mitigada (GeoAlchemy2) | Variación (Overhead) |
| :--- | :--- | :--- | :--- |
| **Throughput (Rendimiento)** | 556.21 req/s | 484.36 req/s | -71.85 req/s (-12.92%) |
| **Latencia Media (Mean)** | 17.26 ms | 19.89 ms | +2.63 ms (+15.24%) |
| **Percentil 50 (Mediana / p50)** | 15.37 ms | 18.42 ms | +3.05 ms |
| **Percentil 95 (p95)** | 31.49 ms | 32.63 ms | +1.14 ms |
| **Percentil 99 (p99)** | 43.75 ms | 38.24 ms | -5.51 ms (-12.59%) |
| **Tasa de Error HTTP (Error Rate)** | 0.0% | 0.0% | 0.0% |

*Nota: Mediciones empíricas obtenidas con 300 peticiones concurrentes sobre el contenedor Docker en PostgreSQL 15 / PostGIS 3.3.*

Para medir la resiliencia bajo estrés progresivo, se evaluó una serie de concurrencia escalonada de 1 a 100 clientes concurrentes. Como se evidencia en la Figura 3(a), el throughput de la arquitectura mitigada escala eficientemente alcanzando una meseta estable superior a 450 req/s sin degradación por bloqueos. Asimismo, la Figura 3(b) revela que la arquitectura mitigada neutraliza los picos severos de latencia de cola observados en la API vulnerable bajo baja concurrencia (140.8 ms frente a 33.1 ms a 5 clientes). A niveles de estrés elevados (50 a 100 clientes), el percentil 99 de la versión mitigada experimenta un incremento moderado (~101 ms vs. ~62 ms), atribuible a la serialización y sobrecosto de CPU en la capa de aplicación (Pydantic/ORM), lo que representa un compromiso aceptable frente a las garantías de seguridad obtenidas.

![Figura 3: Comparativa empírica de rendimiento (Throughput) y percentiles de latencia (p50 y p99) ante concurrencia escalonada (1 a 100 clientes)](figures/fig2_concurrency_latency.png)  
*Figura 3. Comparativa empírica de rendimiento (Throughput) y percentiles de latencia (p50 y p99) ante concurrencia escalonada (1 a 100 clientes)*

---

## 6. Discusión

Los resultados empíricos demuestran que la mitigación basada en GeoAlchemy2 y validación previa con Shapely introduce un sobrecosto medio de latencia de **2.63 ms por petición (+15.24%)**, conservando una tasa de procesamiento de **484.36 req/s**. Un aspecto relevante para el diseño de software es el comportamiento en el percentil 99 (p99): en la prueba de carga estandarizada (10 clientes), la latencia de cola disminuyó de 43.75 ms a 38.24 ms (**mejora del 12.59% en la estabilidad del servicio**) gracias a la reutilización de planes de ejecución preparados (*prepared statements*) en PostgreSQL al evitar el re-parseo continuo de consultas dinámicas, mientras que bajo estrés masivo concurrente el sobrecosto de serialización en la capa de aplicación modula la respuesta sin comprometer la estabilidad ni registrar fallos (0.0%).

Este sobrecosto medio resulta plenamente asumible frente a las garantías de protección obtenidas: neutraliza la exfiltración masiva de predios, los canales laterales de error y la denegación de servicio espacial. Como se ilustra en la **Figura 4**, los cortafuegos de aplicaciones web tradicionales (WAF basados en firmas como OWASP CRS) carecen de gramática geoespacial y bloquean únicamente entre el 0% y el 20% de las inyecciones topológicas (`ST_DWithin` y `ST_Intersects`). El bloqueo residual del 15% al 20% registrado por el WAF en V1 y V2 se debió exclusivamente a la detección de tokens SQL convencionales (como operadores booleanos 'OR' o comillas desparejadas) en ciertas variantes del payload, y no a una inspección semántica de las funciones topológicas subyacentes, como lo demuestra su inoperancia absoluta (0%) frente al vector DoS en V3. En contraste, el pipeline de tres barreras implementado en la capa de aplicación alcanzó una **tasa de mitigación del 100%** en todos los vectores evaluados de la tríada CIA.

![Figura 4: Tasa de mitigación y bloqueo de ataques (%) entre arquitectura desprotegida, WAF tradicional (OWASP CRS) y pipeline propuesto](figures/fig4_attack_mitigation_matrix.png)  
*Figura 4. Tasa de mitigación y bloqueo de ataques (%) entre arquitectura desprotegida, WAF tradicional (OWASP CRS) y pipeline propuesto*

**Independencia de plataforma y validez del benchmarking.** Aunque los valores absolutos de latencia dependen del hardware base de pruebas, la validez metodológica y la generalización de los resultados residen en las proporciones relativas (+15.24% de sobrecosto medio y -12.59% de mejora en p99) y en las complejidades asintóticas. En servidores municipales o instancias de nube con recursos acotados, el consumo computacional de la validación previa en Python (GeoAlchemy2 y Shapely) es marginal frente a la latencia de acceso a disco y la concurrencia relacional. Por el contrario, omitir la mitigación ante ataques de complejidad cuadrática ($O(N^2)$), como el DoS espacial (Simulación 3), expone a los procesadores con menor paralelismo a una saturación inmediata, donde un número reducido de peticiones maliciosas bloquea por completo el geoportal catastral.

**Impacto sistémico en la integridad de trámites y datos catastrales.** La viabilidad empírica del fraude en autovalúos y titularidad (Simulación 4) demuestra que una inyección en la capa de persistencia trasciende la modificación de una tabla aislada y compromete la fe pública del gobierno electrónico local. En la actualidad, los geoportales interoperan de forma autónoma para emitir certificados catastrales con código QR, constancias de no adeudo tributario y transferencias inmobiliarias bajo el estándar ISO 19152 (LADM). La inyección de datos arbitrarios en `catastro_titulares` y `tg_lote` propaga inconsistencias jurídicas y fiscales hacia estos documentos oficiales sin generar alertas en la interfaz de usuario. Este escenario ratifica que el tipado estricto en el ORM constituye una salvaguarda indispensable para preservar la legitimidad y trazabilidad de los servicios públicos digitales.

---

## 7. Conclusiones y Recomendaciones

Este artículo formalizó y demostró empíricamente la viabilidad de seis vectores de inyección SQL espacial orientados a la tríada CIA (Confidencialidad, Integridad y Disponibilidad) en sistemas de información catastral basados en PostGIS, evidenciando que las funciones topológicas nativas no garantizan el aislamiento de datos cuando se construyen mediante concatenación de cadenas. La evaluación experimental sobre un dataset de 487 lotes catastrales estructurados bajo el estándar ISO 19152 (LADM) comprobó que un atacante puede evadir límites zonales, reconstruir credenciales mediante canales laterales de error geométrico, inducir denegación de servicio por sobrecarga algorítmica cuadrática, alterar fichas prediales tributarias y ejecutar borrados cartográficos masivos. Frente a ello, la arquitectura de defensa en profundidad basada en compilación tipada mediante ORM (GeoAlchemy2), tipado rígido con Pydantic y validación topológica previa en memoria con Shapely mitigó con éxito el 100% de los escenarios de explotación evaluados. El benchmarking transaccional demostró que este esquema introduce un sobrecosto medio de latencia de 2.63 ms (+15.24%), mejorando simultáneamente la estabilidad en el percentil 99 en un 12.59% gracias a la reutilización de planes de ejecución preparados en PostgreSQL. En conclusión, la seguridad en infraestructuras catastrales exige abandonar el paradigma de sanitización escalar tradicional, adoptando parametrización en el ORM y controles sintácticos con conciencia espacial integrados desde el diseño arquitectónico de software.

---

## 8. Referencias

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
Rodrigo, A. (2026). Evaluación de Vulnerabilidades de Inyección SQL Espacial en Sistemas de Información Catastral basados en PostGIS. *International Multidisciplinary Journal of Emerging Technologies and Applications*, 1(1), 1–8. https://imjeta.org/index.php/IMJETA/libraryFiles/downloadPublic/1

---

## Appendix 1

**Instrumento de Investigación: Batería de Vectores de Explotación: Operadores Espaciales (V1–V3) y Flujo Catastral / Control (V4–V6)**

| Vector de Prueba | Endpoint Evaluado | Payload Representativo | Dimensión CIA y Efecto |
| :--- | :--- | :--- | :--- |
| **1. Evasión Lógica** | `GET /api/v1/vulnerable/predios/radio` | `50) OR 1=1 --` | **Confidencialidad:** Exfiltración de predios de sectores restringidos. |
| **2. Canal Lateral Ciego** | `GET /api/v1/vulnerable/predios/poligono` | `POLYGON(...) AND 1=(CASE WHEN ... THEN CAST(ST_GeomFromText('ERR') AS INT) ELSE 1 END)` | **Confidencialidad:** Exfiltración carácter por carácter de hashes administrativos. |
| **3. DoS Algorítmico** | `GET /api/v1/vulnerable/predios/analisis-expansion` | `10 + (SELECT COUNT(*) FROM tg_lote a CROSS JOIN ... ST_Buffer(..., 100))` | **Disponibilidad:** Explosión combinatoria $O(N^2)$ y saturación de CPU en GEOS. |
| **4. Tampering Predial** | `POST /api/v1/vulnerable/ficha/modificar` | `id_lote = '21010101000000', nuevo_autovaluo = 0, nuevo_titular = 'HACKER'` | **Integridad:** Alteración de autovalúo fiscal a S/ 0 y fraude de titularidad. |
| **5. Borrado Masivo** | `DELETE /api/v1/vulnerable/predios/borrar` | `filtro_sector = '0101' OR '1'='1'` | **Integridad y Disponibilidad:** Eliminación incondicional de los 487 lotes catastrales. |
| **6. Evasión de Auth** | `POST /api/v1/vulnerable/auth/login` | `username = admin' --` | **Confidencialidad e Integridad:** Evasión de credenciales y escalación a `superadmin_catastro`. |

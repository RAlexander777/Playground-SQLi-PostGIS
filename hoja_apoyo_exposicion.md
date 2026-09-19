# Guía de Exposición Doctoral y Hoja de Apoyo Técnico

**Artículo:** *Evaluación de Vulnerabilidades de Inyección SQL Espacial en Sistemas de Información Catastral basados en PostGIS*  
**Autor:** Rodrigo Alexander Becerra Lucano  
**Marco Académico:** Seminario de Investigación / Tesis Doctoral en Ciberseguridad  
**Material de Soporte:** Sincronizado 1:1 con las 7 diapositivas de [Evaluación de Inyección SQL Espacial en PostGIS.pptx](file:///C:/Users/RODRIGO/Desktop/DOCTORADO/CURSOS/Segundo%20Semestre/CIBERSEGURIDAD/PROYECTO_INVESTIGACI%C3%93N/Evaluaci%C3%B3n%20de%20Inyecci%C3%B3n%20SQL%20Espacial%20en%20PostGIS.pptx) y [Evaluation of Spatial SQL Injection in PostGIS.pptx](file:///C:/Users/RODRIGO/Desktop/DOCTORADO/CURSOS/Segundo%20Semestre/CIBERSEGURIDAD/PROYECTO_INVESTIGACI%C3%93N/Evaluation%20of%20Spatial%20SQL%20Injection%20in%20PostGIS.pptx)  
**Tiempo Total Estimado:** 8 a 10 minutos (aprox. 1 a 1.5 minutos por diapositiva)

---

## 1. Glosario Conceptual y Fundamentos Técnicos (MANDATORIO PARA LA DEFENSA)

Antes de iniciar la exposición, tené muy claros estos conceptos fundamentales, ya que son los que un jurado técnico preguntará para evaluar tu dominio conceptual:

### A. Estándar Internacional ISO 19152 (LADM)
* **¿Qué significa la sigla?** *Land Administration Domain Model* (Modelo para el Dominio de la Administración del Territorio).
* **¿Por qué es relevante en este proyecto?** No se usaron datos genéricos o inventados. El catastro define jurídicamente quién es dueño de la tierra y cuánto debe tributar. LADM es la norma ISO que formaliza la ontología catastral a nivel global.
* **Clases ontológicas clave utilizadas:**
  * **`LA_SpatialUnit`:** Modela la parcela, predio o lote territorial. En el laboratorio corresponde a la tabla **`tg_lote`** (los 487 lotes urbanos con sus geometrías poligonales).
  * **`LA_Party`:** Modela a los sujetos de derecho (propietarios, ciudadanos o personas jurídicas). En el laboratorio corresponde a **`catastro_titulares`** (DNI, nombre, base imponible y autovalúo).
  * **`LA_RRR`:** Modela los Derechos (*Rights*), Restricciones (*Restrictions*, como zonificación comercial o residencial) y Responsabilidades (*Responsibilities*, como el pago fiscal).
  * **`LA_BAUnit`:** *Basic Administrative Unit*, la unidad administrativa que asocia las personas con sus predios.
* **Implicancia en Ciberseguridad ("Fe Pública"):** En un catastro digital, alterar una tabla no es un simple incidente de base de datos; corrompe la **fe pública registral** del Estado. Permite evadir impuestos prediales (reduciendo el autovalúo a cero en la Simulación 4) o despojar digitalmente de la titularidad predial a un ciudadano.

---

### B. Operadores Espaciales de PostGIS Evaluados

PostGIS extiende PostgreSQL añadiendo tipos geométricos y operadores conformes a la especificación *OGC Simple Features for SQL*. Cada operador evaluado en la investigación tiene una matemática y un comportamiento específico:

#### 1. `ST_DWithin` (Operador de Proximidad Métrica)
* **¿Qué hace?** Evalúa si dos geometrías se encuentran a una distancia menor o igual a un umbral $d$:
  $$\text{ST\_DWithin}(geom_1, geom_2, distancia)$$
* **Retorno:** Booleano (`true` o `false`).
* **Optimización interna:** PostGIS primero expande la Envolvente Mínima (*Bounding Box* / MBR) de la geometría por la distancia y realiza un filtrado rápido con el índice espacial **GiST** ($O(\log N)$). Solo los candidatos que pasan el MBR son evaluados con cálculo euclidiano exacto.
* **Mecánica del Ataque (V1 - Evasión Lógica):** La API concatena el parámetro `distancia` como texto en la consulta:
  ```sql
  WHERE ST_DWithin(geom, ST_MakePoint(x, y), 50) AND cod_sector = '0101'
  ```
  El atacante inyecta en `distancia`: `50) OR (1=1`. La consulta muta a:
  ```sql
  WHERE ST_DWithin(geom, ST_MakePoint(x, y), 50) OR (1=1) AND cod_sector = '0101'
  ```
  Al evaluarse el `OR (1=1)` como tautología, se anula tanto el límite métrico de 50 metros como el filtro de seguridad de sector territorial (`0101`), exfiltrando masivamente predios restringidos en **7.03 ms**.

#### 2. `ST_Intersects` (Predicado Topológico)
* **¿Qué hace?** Determina si dos geometrías comparten al menos un punto en común (en su interior, frontera o ambos), siguiendo el modelo de matriz topológica **DE-9IM** (*Dimensionally Extended 9-Intersection Model* de Egenhofer, 1994).
* **Retorno:** Booleano (`true` o `false`).
* **Mecánica del Ataque (V2 - Canal Lateral por Error / Blind SQLi):** Cuando la API no devuelve los datos del predio en la respuesta HTTP, el atacante no puede leerlos directamente. Por tanto, inyecta un oráculo condicional topológico:
  * Si el $N$-ésimo bit del hash de la contraseña administrativa es `1`, la consulta fuerza una excepción matemática en PostGIS (como división topológica por cero o llamar a `ST_GeomFromText('ERR')` con WKT inválido).
  * Si el bit es `0`, la consulta termina normalmente retornando código HTTP 200.
  * Con 128 o 256 peticiones automáticas, el atacante reconstruye la credencial hash completa en **42 segundos**, sin necesidad de ver los datos en pantalla.

#### 3. `ST_Buffer` (Dilatación Geométrica y Spatial DoS)
* **¿Qué hace?** Genera un nuevo polígono que representa el área envolvente a una distancia de amortiguamiento $r$ alrededor de la geometría de entrada.
* **El parámetro crítico `quad_segs`:** Define cuántos segmentos de recta se calculan para aproximar cada cuadrante de círculo al redondear las esquinas del buffer (por defecto 8).
* **Mecánica del Ataque (V3 - Spatial DoS por Complejidad Algorítmica $O(N^2)$):**
  * Se apoya en el principio de **Crosby y Wallach (2003)**: en lugar de saturar el servidor con millones de peticiones (ataque volumétrico), se envía **una sola consulta** que activa la rama asintótica de peor caso en el algoritmo.
  * Los predios urbanos de Puno poseen hasta 222 vértices. El payload inyecta un `CROSS JOIN` (producto cartesiano) combinando polígonos con buffers hiperdensos (`quad_segs = 100`).
  * Esto fuerza a la biblioteca en C/C++ **GEOS** (subyacente en PostGIS) a evaluar intersecciones arista por arista sobre cientos de miles de vértices sin respaldo de índices espaciales GiST.
  * **Impacto empírico:** La latencia explota de 10.8 ms a **1,692.1 ms (degradación de 93.5x o ~9,700%)**. Dos peticiones concurrentes monopolizan el 100% de los workers de PostgreSQL, congelando el geoportal municipal.

---

### C. Sistema de Coordenadas EPSG:32719 y GiST
* **¿Qué es `EPSG:32719`?**
  * Proyección cartográfica **UTM (Universal Transversal de Mercator), Zona 19 Sur**, datum WGS 84. Corresponde geográficamente a la región de Puno y el altiplano peruano.
  * **Diferencia vital con EPSG:4326 (grados):** En coordenadas geográficas (latitud/longitud en grados), una distancia de `50` equivaldría a 50 grados (~5,500 km, un absurdo). En `EPSG:32719`, las coordenadas $(X, Y)$ están expresadas en **metros planos**. Por eso un radio de `50` en `ST_DWithin` representa exactamente 50 metros en el terreno físico.
* **¿Qué es el índice `GiST`?**
  * *Generalized Search Tree*. Implementa una estructura de árbol R (*R-Tree*) sobre las envolventes mínimas rectangulares (*Bounding Boxes*) de las geometrías. Reduce la búsqueda de vecinos de $O(N)$ a $O(\log N)$. La inyección espacial en V3 evita deliberadamente el GiST forzando escaneos secuenciales cuadráticos en memoria.
* **¿Qué es `EWKB`?**
  * *Extended Well-Known Binary*. Formato binario nativo de PostGIS que codifica tipo geométrico, coordenadas y SRID. El pipeline seguro compila los parámetros a EWKB mediante GeoAlchemy2, haciendo matemáticamente imposible que caracteres como `'` o `OR` se mezclen con el código SQL.

---

## 2. Guía de Exposición Diapositiva por Diapositiva

### Diapositiva 1: Portada
* **Tiempo sugerido:** 45 segundos.
* **Título:** *Evaluación de Vulnerabilidades de Inyección SQL Espacial en Sistemas de Información Catastral basados en PostGIS*.
* **Qué decir:**
  > "Buenos días, miembros del jurado. La presente investigación aborda una brecha crítica en la seguridad de infraestructuras geoespaciales: la susceptibilidad de los sistemas de información catastral basados en PostgreSQL y PostGIS ante inyecciones SQL espaciales. Demostraremos que los operadores geométricos, frecuentemente asumidos como inmunes, exigen un nuevo paradigma defensivo en la capa de software para proteger la fe pública y la estabilidad del Estado."

---

### Diapositiva 2: Introducción
* **Tiempo sugerido:** 1 minuto 15 segundos.
* **Contenido en lámina:** Servicios web cliente-servidor, operadores geométricos (`ST_DWithin`, `ST_Intersects`, `ST_Buffer`), tríada CIA y mitigación.
* **Argumentación clave:**
  1. *Exposición del Catastro Moderno:* Los geoportales municipales e Infraestructuras de Datos Espaciales (IDE) publican APIs REST para recaudación de tributos, visores urbanos e interoperabilidad.
  2. *El Mito de Seguridad Espacial:* Existe una falsa presunción técnica de que las funciones espaciales (`ST_DWithin`, `ST_Intersects`, `ST_Buffer`) son inmunes a inyecciones SQL porque operan sobre geometrías y números. La realidad es que los desarrolladores suelen concatenar parámetros de coordenadas o radios como cadenas de texto.
  3. *Objetivo del Trabajo:* Evaluar de manera cuantitativa 6 vectores de ataque orientados a la Tríada CIA (Confidencialidad, Integridad y Disponibilidad) y medir el impacto computacional de un pipeline defensivo multicapa.

---

### Diapositiva 3: Dataset de Prueba y Entorno de Evaluación
* **Tiempo sugerido:** 1 minuto 30 segundos.
* **Contenido en lámina:** 487 lotes urbanos (ISO 19152 / LADM), geometrías de 4 a 222 vértices, 3 entidades relacionales sin PII, arquitectura en contenedores Docker.
* **Argumentación clave:**
  1. *Rigor Metodológico (ISO 19152 LADM):* No se usaron datos sintéticos planos. El banco de pruebas carga **487 parcelas reales del casco urbano de Puno**, georreferenciadas en **EPSG:32719** (UTM 19S) bajo la clase estándar `LA_SpatialUnit`.
  2. *Complejidad Vectorial Realista:* Los polígonos poseen entre 4 y 222 vértices (promedio 9.0). Esta dispersión topológica es indispensable para someter al motor a cálculos de intersección no lineales.
  3. *Esquema Relacional y Ética:* Estructurado en 3 tablas (`tg_lote` para la cartografía, `catastro_titulares` para el autovalúo y `catastro_usuarios` para control de acceso). Se generaron atributos fiscales reproducibles libres de datos personales (sin PII).
  4. *Reproducibilidad Científica:* Todo el entorno está desacoplado en microservicios Docker (PostGIS 15 y FastAPI en Python 3.11) y publicado en GitHub para auditoría independiente.

---

### Diapositiva 4: Evaluación de los 6 Vectores de Ataque (Tríada CIA)
* **Tiempo sugerido:** 2 minutos.
* **Contenido en lámina:** Confidencialidad (V1, V2), Integridad (V4, V5, V6), Disponibilidad (V3).
* **Argumentación clave por vector:**
  * **Confidencialidad:**
    * **V1 (Evasión Lógica en `ST_DWithin`):** Inyección de tautología `50) OR (1=1` que anula el límite métrico y el sector; exfiltra 50 predios restringidos en 7.03 ms.
    * **V2 (Canal Lateral Ciego en `ST_Intersects`):** Inferencia booleana vinculada a excepciones topológicas forzadas; extrae hashes administrativos bit a bit en 42 segundos.
  * **Disponibilidad:**
    * **V3 (Spatial DoS en `ST_Buffer`):** Ataque de complejidad algorítmica $O(N^2)$ (Crosby & Wallach). Inyección de producto cartesiano espacial; satura los workers de GEOS elevando la latencia a 1,692 ms.
  * **Integridad:**
    * **V4 (Tampering de Ficha Predial):** Inyección en cláusula `UPDATE SET`; reduce el autovalúo a S/ 0.00 y suplanta la titularidad en `catastro_titulares`.
    * **V5 (Borrado Cartográfico):** Sentencia `WHERE 1=1` inyectada; purga los 487 lotes de `tg_lote`, destruyendo la cartografía del visor.
    * **V6 (Bypass de Autenticación):** Truncamiento SQL mediante comentarios (`admin' --`); escalación ilegítima a `superadmin_catastro`.

---

### Diapositiva 5: Barreras de Mitigación de Ataques
* **Tiempo sugerido:** 1 minuto 30 segundos.
* **Contenido en lámina:** Tres barreras: Pydantic, Shapely, GeoAlchemy2 / SQLAlchemy.
* **Argumentación clave (Defensa en Profundidad en Capa de Software):**
  * **Barrera 1 (Capa Web - Pydantic):** Valida tipos escalares estrictos en tiempo de ejecución, impone límites físicos de coordenadas y aplica expresiones regulares. Rechaza entradas maliciosas con código `HTTP 422` antes de tocar la base de datos.
  * **Barrera 2 (Capa Dominio - Shapely en memoria):** Inspección topológica anticipada de geometrías (WKT/GeoJSON). Detecta polígonos que se auto-cruzan o geometrías degeneradas y las descarta en memoria.
  * **Barrera 3 (Capa Persistencia - GeoAlchemy2 + SQLAlchemy):** Compilación nativa de geometrías al formato binario **EWKB** y uso mandatorio de **sentencias preparadas** (*prepared statements*). Garantiza la separación absoluta entre el código SQL y los datos.

---

### Diapositiva 6: Resultados y Rendimiento
* **Tiempo sugerido:** 1 minuto 30 segundos.
* **Contenido en lámina:** 100% efectividad de seguridad, +2.63 ms sobrecosto operativo (19.89 ms vs. 17.26 ms), -12.59% mejora en p99.
* **Argumentación clave:**
  1. *Eficacia Total:* El pipeline neutralizó el **100% de los 6 vectores evaluados** (cero brechas en la Tríada CIA).
  2. *Sobrecosto Mínimo (+2.63 ms):* La latencia media pasa de 17.26 ms a 19.89 ms (+15.24%), manteniendo un rendimiento de **484 req/s**. Este incremento de 2.6 milisegundos es completamente imperceptible para usuarios de geoportales y sistemas administrativos.
  3. *Mejora de Cola p99 (-12.59%):* La latencia en el percentil 99 bajó de 43.75 ms a 38.24 ms. Esto se debe a que PostgreSQL reutiliza los planes de ejecución compilados (*prepared statements*) en lugar de tener que analizar sintácticamente consultas de texto una y otra vez.

---

### Diapositiva 7: Conclusiones del Estudio
* **Tiempo sugerido:** 1 minuto.
* **Contenido en lámina:** Tres conclusiones principales del estudio.
* **Argumentación de cierre:**
  1. *Paradigma de Rigor Espacial:* Las funciones de PostGIS no son inmunes por ser geométricas; requieren el mismo rigor de parametrización que el SQL relacional clásico.
  2. *Defensa en la Capa Adecuada:* La validación tradicional no comprende topología. El filtrado anticipado en memoria con Shapely y Pydantic es indispensable para prevenir bloqueos por complejidad cuadrática $O(N^2)$.
  3. *Viabilidad en Producción:* El sobrecosto medio de 2.63 ms certifica la factibilidad de implementar este pipeline en geoportales municipales reales, blindando la fe pública del catastro sin penalizar la operatividad.

---

## 3. Banco de Preguntas Críticas del Jurado (Defensa Técnica)

| Pregunta Probable del Jurado | Respuesta Técnica y Directa |
| :--- | :--- |
| **"¿Por qué utilizó un dataset de solo 487 lotes y no millones de registros?"** | *"Porque la investigación evalúa la **vulnerabilidad lógica de las consultas y la complejidad algorítmica de los predicados espaciales**, no la capacidad de almacenamiento o I/O de PostgreSQL. 487 parcelas con geometrías reales de hasta 222 vértices son suficientes para desencadenar el cálculo no lineal en GEOS sin introducir ruido de paginación en disco."* |
| **"¿Qué es específicamente la norma ISO 19152 (LADM) y por qué la utilizó?"** | *"Es el Land Administration Domain Model. Estandariza las clases catastrales a nivel internacional: `LA_SpatialUnit` para la cartografía predial y `LA_Party` para los titulares y el autovalúo. Demuestra que vulnerar una base de datos catastral compromete la fe pública y la fiscalidad del Estado, no solo registros aislados."* |
| **"¿Por qué ocurre la explosión cuadrática $O(N^2)$ en el Spatial DoS?"** | *"Porque al inyectar un producto cartesiano (`CROSS JOIN`) con buffers hiperdensos, la biblioteca interna de PostGIS (GEOS) se ve obligada a comparar arista contra arista entre pares de polígonos complejos sin poder utilizar el árbol GiST, elevando la latencia de 10.8 ms a 1,692 ms."* |
| **"¿Por qué no basta con usar SQLAlchemy y se necesitó GeoAlchemy2?"** | *"SQLAlchemy tradicional solo entiende tipos escalares relacionales (enteros, cadenas, fechas). GeoAlchemy2 proporciona los tipos de columna espaciales nativos de PostGIS (`Geometry`), gestiona el SRID (EPSG:32719) y compila las geometrías en variables binarias EWKB directamente para el motor."* |
| **"¿Por qué mejoró el percentil 99 (p99) en un 12.59% en la versión mitigada?"** | *"Porque el pipeline mitigado utiliza consultas preparadas (*Prepared Statements*). PostgreSQL compila el plan de ejecución una sola vez y lo reutiliza en memoria, evitando el sobrecosto continuo de parsear cadenas de texto dinámicas en cada petición."* |
| **"¿Dónde se puede auditar y replicar su investigación?"** | *"Todo el banco de pruebas, el dataset de Puno y los scripts de explotación están empaquetados en contenedores Docker y disponibles abiertamente en GitHub en el repositorio `RAlexander777/Playground-SQLi-PostGIS`."* |

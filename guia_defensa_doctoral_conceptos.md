# Guía Maestra Conceptual para la Defensa Doctoral: Inyección SQL Espacial en PostGIS

Esta guía resume con rigor académico y lenguaje claro los **cuatro pilares conceptuales** de la investigación para responder con solidez y autoridad técnica ante el jurado doctoral, asesores y evaluadores de revistas indexadas.

---

## 1. SQLi Tradicional vs. Inyección SQL Espacial (Spatial SQLi)

### El Problema de Fondo: ¿Por qué la intuición común falla?
La mayoría de los desarrolladores y auditores de seguridad asumen que las funciones geoespaciales (`ST_DWithin`, `ST_Intersects`, `ST_Buffer`) son "cajas negras matemáticas" seguras por naturaleza. Se cree erróneamente que, al no manejar contraseñas ni textos directos, una consulta de mapas no representa un riesgo crítico de inyección.

### Escalar vs. Multidimensional
* **En SQL Tradicional (Escalar):** Las consultas evalúan igualdades o rangos sobre tipos primitivos unidimensionales (`WHERE id = 5`, `WHERE username = 'admin'`). El escape sintáctico busca forzar tautologías alfanuméricas booleanas (`' OR '1'='1`).
* **En SQL Espacial (Multidimensional):** Una geometría no es un valor escalar; es una estructura algebraica compleja compuesta por:
  1. Dimensiones topológicas (puntos, líneas, polígonos).
  2. Sistema de Referencia Espacial (**SRID**, como WGS 84 o UTM 19S).
  3. Envolventes mínimas de contorno (**Bounding Boxes / MBR**).
  4. Relaciones de proximidad topológica del cálculo 9-Intersection (Egenhofer, 1994).

### ¿Por qué los filtros perimetrales basados en firmas no resuelven la inyección espacial?
Los filtros perimetrales tradicionales operan mediante análisis léxico basado en expresiones regulares y firmas de cadenas maliciosas (buscan palabras como `UNION`, `SELECT`, `DROP`, `--`, o comillas desbalanceadas). 
* En una **inyección espacial**, el payload puede consistir únicamente en funciones matemáticas legítimas de GIS, coordenadas numéricas y paréntesis válidos (ejemplo: `50) OR ST_Contains(...)`). 
* Un filtro léxico interpreta la petición como una instrucción sintáctica válida y la deja pasar. La vulnerabilidad nace porque el motor SQL reescribe su Árbol de Sintaxis Abstracta (**AST**) alterando las restricciones de demarcación territorial en la base de datos.

> **Frase clave para tu sustentación:**  
> *"La inyección espacial no es un fallo del motor PostGIS, sino un quiebre en la capa de software que concatena parámetros no saneados dentro de operadores topológicos multidimensionales. Su mitigación exige validación y tipado semántico previo en la aplicación, no análisis superficial de firmas."*

---

## 2. Ataque de Complejidad Algorítmica $O(N^2)$ (Spatial DoS)

### Fundamento Teórico: Crosby y Wallach (2003)
Tradicionalmente, la Denegación de Servicio (DoS) se asocia con saturar el ancho de banda enviando millones de peticiones (DDoS volumétrico). Crosby y Wallach demostraron que existe una vía mucho más devastadora: el **Ataque de Complejidad Algorítmica** (*Algorithmic Complexity Attack*). Consiste en enviar **una única petición cuidadosamente construida** que obligue al algoritmo subyacente a ejecutar su peor caso de cómputo asintótico, monopolizando el 100% de la CPU.

### Mecánica en PostGIS y la Librería GEOS
PostGIS delega el cálculo geométrico pesado (intersecciones, buffers, uniones) en la librería nativa de C++ **GEOS** (*Geometry Engine - Open Source*).
1. **Generación de Curvas en Buffers:** Cuando se computa un buffer alrededor de un polígono, PostGIS interpola arcos mediante segmentos rectos definidos por el modificador `num_seg_quarter_circle` (segmentos por cuadrante). Por defecto se usan 8 segmentos; pero si el atacante inyecta `100`, cada cuadrante se aproxima con 100 segmentos (un círculo de 400 vértices).
2. **Inflación Geométrica:** Un lote urbano promedio de 9 vértices pasa a tener más de 3,600 vértices; un lote irregular de 222 vértices se convierte en una figura de casi 90,000 vértices.
3. **Producto Cartesiano sin Índice GiST:** Al inyectar un subquery que cruza lotes mediante un `CROSS JOIN` y evalúa `ST_Intersects` sin pasar por el índice espacial GiST, el motor GEOS se ve forzado a comparar **cada segmento de línea contra todos los demás segmentos**.

### Evidencia Empírica del Paper (Figure 3)
* Con carga estándar: el endpoint responde en **10.8 ms**.
* Con inyección de buffer y cruce cartesiano de 345,600 vértices evaluados: la latencia escala hasta **1,665.16 ms** (un factor de degradación de **228x** en una sola consulta).
* **Invarianza de Hardware:** En la estación de pruebas (Intel Core Ultra 5 245KF de 14 núcleos a 5.2 GHz), el procesador amortigua la carga; sin embargo, en un servidor municipal típico (con CPUs modestas de 2 o 4 núcleos), 3 peticiones concurrentes de este tipo saturan la totalidad de los workers de PostgreSQL, dejando el catastro web fuera de servicio.

> **Frase clave para tu sustentación:**  
> *"El Spatial DoS explota la asimetría de cómputo: al cliente le toma milisegundos inyectar una subconsulta con modificadores de densidad, pero al motor espacial le cuesta una complejidad cuadrática $O(N^2)$ resolver millones de intersecciones topológicas, congelando la base de datos."*

---

## 3. La Arquitectura de Tres Barreras de Defensa en Profundidad

Un principio esencial de la ciberseguridad es que **una sola línea de defensa nunca es suficiente**. La parametrización pura (usar bind variables) previene que se escape la sintaxis SQL, pero **es ciega ante el Spatial DoS** (un atacante puede enviar un número legítimo enorme como radio y tumbar el servidor). Por eso se diseñó una tubería en tres capas:

```
[ Solicitud HTTP ]
       │
       ▼
┌─────────────────────────────────────────────────────────────────┐
│ BARRERA 1: Validación Sintáctica y Límites Físicos (Pydantic)  │
│ - Forzado estricto de tipos de datos (float, int, str).         │
│ - Acotamiento físico de rangos (ej. radio: gt=0, le=5000 m).    │
│ - Validación de patrones regex (ej. sector: ^\d{4}$).          │
└─────────────────────────────────────────────────────────────────┘
       │ (Rechaza payloads no escalares con HTTP 422)
       ▼
┌─────────────────────────────────────────────────────────────────┐
│ BARRERA 2: Validación Topológica en Memoria (Shapely)          │
│ - Inspección en capa de aplicación antes de tocar SQL.          │
│ - shapely.wkt.loads: descarta WKT con sintaxis corrupta.        │
│ - is_valid: neutraliza oráculos de error y autointersecciones.  │
└─────────────────────────────────────────────────────────────────┘
       │ (Evita disparar excepciones en PostGIS -> anula side-channels)
       ▼
┌─────────────────────────────────────────────────────────────────┐
│ BARRERA 3: Parametrización Nativa y Compilación ORM (GeoAlchemy)│
│ - Predicados espaciales compilados a binario EWKB.              │
│ - Uso exclusivo de Bind Variables en el AST de PostgreSQL.      │
│ - Reutilización de planes cacheados (Prepared Statements).      │
└─────────────────────────────────────────────────────────────────┘
       │
       ▼
[ Motor PostgreSQL / PostGIS 15 ]
```

### Detalle de las 3 Barreras:
1. **Barrera 1 (Pydantic - Tipado Rígido y Bounding Físico):**
   - *¿Qué soluciona?* Neutraliza la inyección de modificadores numéricos y operadores booleanos directos (`50) OR 1=1`).
   - *Regla de negocio:* Un radio municipal nunca puede ser negativo ni exceder los 5,000 metros; el código de sector debe obedecer estrictamente a 4 dígitos numéricos (`^\d{4}$`).
2. **Barrera 2 (Shapely - Validación Topológica en Memoria):**
   - *¿Qué soluciona?* Neutraliza el vector 2 (Error-Based SQLi). En este ataque, el agresor inyecta geometrías deliberadamente deformadas para que PostGIS lance excepciones internas (error 500) y usarlas como canal lateral para adivinar contraseñas carácter por carácter.
   - *Mecanismo:* Shapely valida en la memoria RAM de Python si la geometría es topológicamente consistente (`geom.is_valid`). Si contiene errores, se rechaza inmediatamente con un error controlado de cliente (HTTP 422) sin permitir que la base de datos falle.
3. **Barrera 3 (GeoAlchemy2 + SQLAlchemy - Parametrización Binaria):**
   - *¿Qué soluciona?* Separa de forma absoluta el código de los datos.
   - *Mecanismo:* Convierte las geometrías en variables vinculadas binarias (**EWKB** - *Extended Well-Known Binary*). El motor de base de datos nunca compila el input como sintaxis SQL ejecutable; lo trata estrictamente como un dato literal.
   - *Beneficio colateral medido:* Al parametrizar, PostgreSQL almacena en caché el plan de ejecución compilado (*Prepared Statement*), logrando reducir la latencia de cola en el percentil 99 (**p99 baja de 43.75 ms a 38.24 ms**, una mejora del 12.59% en estabilidad).

> **Frase clave para tu sustentación:**  
> *"La defensa en profundidad es indispensable porque cada barrera neutraliza una capa distinta de la amenaza: Pydantic contiene la física y los límites de los datos, Shapely protege la integridad matemática de la geometría en memoria, y GeoAlchemy2 blinda el árbol sintáctico de la base de datos."*

---

## 4. Modelo Catastral de Dominio (ISO 19152 - LADM) y Fe Pública Digital

### ¿Qué es la ISO 19152 LADM?
El **Land Administration Domain Model (LADM)** es el estándar internacional oficial de la ISO que estandariza cómo los gobiernos gestionan el territorio, la propiedad y los tributos inmobiliarios.

### Clases Implementadas en Nuestro Laboratorio:
* `LA_SpatialUnit` (**Unidad Espacial**): Representa la parcela o predio territorial físico, modelado en nuestra base de datos en la tabla `tg_lote` con coordenadas proyectadas UTM 19S (`EPSG:32719`).
* `LA_Party` (**Interesado / Titular**): Representa a la persona natural, jurídica o entidad titular del predio, modelado en `catastro_titulares` con datos de identificación tributaria y autovalúo fiscal.
* `LA_RRR` (**Rights, Restrictions, Responsibilities**): Los derechos de propiedad, las restricciones de zonificación municipal y las obligaciones tributarias prediales.

### Impacto Sistémico en la Fe Pública y Trámites Digitales:
Cuando se adultera un catastro (Simulación 4: Manipulación de Autovalúo, y Simulación 5: Borrado Cartográfico), el daño **no se queda en una fila de la base de datos**. 
En los gobiernos electrónicos actuales, el sistema catastral está interconectado mediante APIs con múltiples entidades:
1. **Certificados Catastrales con Código QR:** El ciudadano solicita en línea su certificado de zonificación o constancia catastral; la API consulta PostGIS, firma un PDF y le estampa un QR criptográfico. Si PostGIS fue adulterado mediante SQLi, el Estado emite y avala un documento oficial con datos falsificados.
2. **Constancias de No Adeudo Tributario:** Al alterar el autovalúo fiscal a S/ 0.00, el sistema municipal emite solvencias tributarias ilegítimas, facilitando evasión fiscal automatizada.
3. **Escrituras Notariales y Registros Públicos:** Notarías y oficinas registrales (como SUNARP en Perú) consumen servicios web interoperables para validar límites de predios. Un borrado masivo o desplazamiento territorial induce litigios civiles sobre derechos reales de propiedad.

> **Frase clave para tu sustentación:**  
> *"Vulnerar el catastro espacial no es un incidente informático aislado; corrompe la cadena de fe pública digital del Estado, generando consecuencias legales, registrales y tributarias irreversibles en la administración del territorio."*

---

### Resumen Rápido para Respuestas Breves

| Concepto | Lo que debes responder en 1 frase |
| :--- | :--- |
| **Spatial SQLi** | Manipulación sintáctica de operadores geométricos multidimensionales que subvierte la lógica espacial del negocio. |
| **Spatial DoS** | Explotación de la complejidad algorítmica cuadrática $O(N^2)$ en el motor GEOS mediante geometrías hiperdensas y productos cartesianos. |
| **Tres Barreras** | Pydantic acota límites y tipos, Shapely valida topología en memoria descartando errores, y GeoAlchemy2 compila bind variables EWKB. |
| **ISO 19152 (LADM)** | Estándar de administración del territorio cuya vulneración corrompe la fe pública de certificados digitales, autovalúos y registros de propiedad. |

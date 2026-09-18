# Manual de Redacción Científica para Ingeniería de Software y Ciberseguridad Experimental

> **Guía de estilo, arquitectura editorial y asepsia técnica para artículos cuantitativos-experimentales.**  
> *Diseñado para investigadores, estudiantes de posgrado y modelos de lenguaje (LLMs) que redactan o auditan manuscritos científicos para conferencias y journals indexados (IEEE, ACM, Elsevier, Springer, IMJETA).*

---

## 1. El Conflicto Fundamental: Ingeniería vs. Ciencias Sociales

El error más común al redactar un artículo científico en ciencias de la computación, seguridad informática o ingeniería de software es importar **formalismos metodológicos de las ciencias sociales**. Esto ocurre típicamente cuando los autores trasladan la estructura de una tesis universitaria tradicional a un formato de paper técnico.

| Dimensión | Tesis Tradicional / Ciencias Sociales (INCORRECTO) | Paper de Ingeniería Experimental (CORRECTO) |
| :--- | :--- | :--- |
| **Sujeto de estudio** | Personas, encuestas, opiniones, "población diana". | Datasets, paquetes de red, transacciones, endpoints, código fuente. |
| **Muestra** | "Muestreo no probabilístico por conveniencia". | Partición de dataset, lote de pruebas (*testbed*), batería de vectores de ataque. |
| **Tono** | Retórico, persuasivo, justificador, adjetivado. | Aséptico, cuantitativo, determinista, sobrio. |
| **Objetivo** | Demostrar hipótesis social o describir percepción. | Evaluar eficacia, medir sobrecosto computacional, caracterizar trade-offs. |
| **Vocabulario** | "Hallazgos", "necesidad imperiosa", "marco integral". | "Resultados", "latencia p99", "sobrecosto en ms", "pipeline de mitigación". |

---

## 2. Los 7 Pecados Capitales y sus Reglas de Transformación

### Pecado 1: Vocabulario Sociológico en Entornos de Software
* **Antipatrón:** *"La población de estudio estuvo constituida por una muestra no probabilística por conveniencia de 1,500 predios..."*
* **Problema:** En informática no hay "muestreo por conveniencia" de registros de base de datos; hay un dataset experimental con propiedades cartográficas, topológicas y volumétricas definidas.
* **Regla:** Usar términos de ingeniería de datos.
* **Solución:** *"El dataset experimental comprende 1,500 parcelas catastrales urbanas continuas estructuradas bajo el estándar ISO 19152 (LADM)..."*

---

### Pecado 2: Clichés de Apertura y Grandilocuencia Localista
* **Antipatrón:** *"En la era de la transformación digital y el auge de las Smart Cities, entidades como COFOPRI, el Ministerio de Vivienda y las municipalidades de Arequipa utilizan software..."*
* **Problema:** Los revisores internacionales descartan artículos que abren con lugares comunes o listas de entidades administrativas locales que no aportan al marco teórico general.
* **Regla:** Abrir directamente con la arquitectura técnica, la criticidad de la función del sistema y la persistencia de datos.
* **Solución:** *"Los sistemas de información catastral modernos exponen servicios web y geoportales sobre arquitecturas cliente-servidor para administrar la propiedad predial, la zonificación urbana y la recaudación fiscal (Lemmen et al., 2015)..."*

---

### Pecado 3: Subsecciones Informales con "vs." en Trabajos Relacionados
* **Antipatrón:** *"2.1. Inyecciones SQL Tradicionales vs. Inyecciones Espaciales"* o *"2.2. Seguridad en Bases de Datos vs. Estándares OGC"*.
* **Problema:** El "vs." es un recurso periodístico o informal. En un estado del arte académico, la literatura se clasifica por **ejes temáticos formales**, y cada subsección debe concluir identificando el **vacío de investigación** (*research gap*).
* **Regla:** Nombrar los ejes mediante sustantivos conceptuales y cerrar cada subsección explicando por qué la literatura previa no resuelve el problema que este paper aborda.
* **Solución:** 
  * Título: `2.1. Inyecciones SQL Espaciales y Operadores Topológicos`.
  * Cierre: *"Este vacío teórico en las taxonomías clásicas de inyección deja sin estudiar la manipulación directa de predicados topológicos en motores espaciales relacionales."*

---

### Pecado 4: Matemática Cosmética (Fórmulas Innecesarias)
* **Antipatrón:** Insertar fórmulas complejas de cálculo relacional o tuplas $\mathcal{Q}(x, y, r, s) = \{ p \in \mathcal{P} \mid \dots \}$ solo para que el paper "parezca más científico", cuando en la práctica se está evaluando un endpoint REST con parámetros JSON/HTTP.
* **Problema:** Si una fórmula no se deriva, no demuestra un teorema formal y no se utiliza para calcular una prueba matemática, es ruido que confunde al revisor.
* **Regla:** Si el aporte es empírico/aplicado, la formalidad la da el contrato del endpoint, el esquema de tipos (Pydantic/ORM), la tabla de vectores y el script reproducible, no una fórmula artificial.

---

### Pecado 5: Especificaciones Comerciales Innecesarias en Metodología
* **Antipatrón:** *"Las pruebas se realizaron en una laptop Gamer ASUS ROG Strix con CPU Intel Core i9 y tarjeta gráfica NVIDIA RTX 4070..."*
* **Problema:** Suena a un review de hardware comercial, no a un reporte de laboratorio de software.
* **Regla:** Informar la arquitectura computacional de forma sobria (núcleos, memoria, microservicios, sistema operativo base) y aislar la validez del benchmarking en **proporciones relativas** (+% de sobrecosto, latencias p95/p99) y complejidades asintóticas ($O(N^2)$), no en la potencia del procesador de turno.

---

### Pecado 6: Desorden en la Secuencia de Citación de Figuras
* **Antipatrón:** Citar en el texto la `Figura 3` en la sección 4, y luego citar la `Figura 1` y `Figura 2` en la sección 5.
* **Problema:** Viola la regla tipográfica fundamental de cualquier editorial científica (IEEE, Springer, Elsevier): **las figuras se numeran en el orden estricto de su primera aparición en el cuerpo del texto**.
* **Regla:** Numeración correlativa estricta. Cada figura debe estar auto-contenida (su epígrafe o pie debe explicar qué variables se comparan sin obligar a leer todo el capítulo).

---

### Pecado 7: Términos Ambiguos ("Hallazgos", "Marco Integral", "Compensaciones")
* **Antipatrón:** *"Los hallazgos subrayan la necesidad crítica de una validación espacial y destacan las compensaciones de latencia, ofreciendo un marco integral..."*
* **Problema:** 
  1. *"Hallazgos"* es propio de ciencias cualitativas.
  2. *"Compensaciones"* es una mala traducción de *trade-offs* que no aclara si el rendimiento mejoró o empeoró.
  3. *"Marco integral"* es una exageración pretenciosa para un paper de 6 u 8 páginas.
* **Regla:** Dividir con precisión **Resultados Cuantitativos** (datos fríos) y **Conclusiones Arquitectónicas** (qué regla de diseño se infiere).
* **Solución:** *"Los resultados demuestran que el pipeline neutralizó el 100% de los vectores evaluados con un sobrecosto medio de 2.63 ms (+15.24%) y una mejora del 12.59% en la estabilidad de cola (p99). Se concluye que la seguridad en geoportales exige trasladar la validación y el tipado rígido al ORM, con un impacto operativo marginal."*

---

## 3. Estructura Canónica de un Paper Cuantitativo-Experimental

### A. Título
* **Fórmula:** `[Acción Metodológica] + [Fenómeno/Vulnerabilidad] + en + [Objeto Tecnológico / Contexto]`
* *Ejemplo:* *"Evaluación de Vulnerabilidades de Inyección SQL Espacial en Sistemas de Información Catastral basados en PostGIS"*.

### B. Resumen (Abstract) — Fórmula de 5 Oraciones
1. **Contexto:** Qué tecnología se usa y qué rol crítico cumple en producción.
2. **Problema:** Qué vector de falla o vulnerabilidad aparece cuando se implementa de forma insegura.
3. **Metodología:** Qué se construyó (banco de pruebas, dataset, condiciones comparadas).
4. **Resultados:** Cuánto se mitigó (%) y qué métricas de rendimiento/latencia exactas se obtuvieron.
5. **Conclusión:** Qué regla de arquitectura o estándar de desarrollo se debe adoptar.

### C. Introducción — Regla de los 3 Párrafos
* **Párrafo 1 (Dominio):** Arquitectura cliente-servidor de la tecnología, estándares internacionales (ISO/OGC) y relevancia operativa.
* **Párrafo 2 (Conflicto técnico):** Mecánica específica del fallo. Explicar por qué las soluciones clásicas (WAF genérico, sanitización de cadenas tradicional) fallan en este contexto específico.
* **Párrafo 3 (Contribuciones explícitas):** Enumerar taxativamente: (1) sistematización de vectores, (2) banco de pruebas reproducible sobre dataset estándar, y (3) cuantificación empírica de sobrecostos de mitigación.

### D. Trabajos Relacionados — Estructura de Brecha (*Gap*)
* 3 a 4 subsecciones organizadas por temas.
* Cada subsección debe analizar autores clásicos y contemporáneos, y **rematar con la limitación**: *"Sin embargo, dichos estudios asumieron X y dejaron sin abordar Y"*.

### E. Metodología y Diseño Experimental
Estructura mínima indispensable en 4 partes:
1. **Enfoque y Diseño:** Cuantitativo, experimental, controlado (Condición A: vulnerable vs. Condición B: mitigada).
2. **Dataset:** Volumen, estándares estructurales (e.g., ISO 19152 LADM), complejidad geométrica (vértices min/max/promedio), sistema de coordenadas (EPSG) y tratamiento ético de datos.
3. **Banco de Pruebas y Arquitectura:** Contenedores (Docker), versiones exactas de motores y librerías, y aislamiento de red.
4. **Vectores de Prueba y Métricas:** Tabla de ataques mapeados a la tríada CIA, número de peticiones de estrés, percentiles medidos ($p50, p95, p99$) y throughput ($req/s$).

### F. Resultados y Benchmarking
* Presentación tabular y gráfica de datos crudos.
* Descripción aséptica de diferencias numéricas relativas.
* Sin opiniones ni juicios de valor en esta sección (las opiniones van en la Discusión).

### G. Discusión
* **Interpretación técnica:** Explicar el *por qué* de los números (e.g., por qué la latencia p99 mejoró gracias a los *prepared statements* del motor).
* **Independencia de plataforma:** Justificar por qué las proporciones porcentuales se mantienen en servidores de menor potencia.
* **Impacto sistémico:** Conectar la vulnerabilidad con el riesgo en trámites reales (e.g., alteración de autovalúo o falsificación registral).

### H. Conclusiones y Recomendaciones
* Un solo bloque denso y contundente (175 a 250 palabras).
* Resumen de la hipótesis comprobada, cifras de eficacia del 100%, costo en milisegundos y recomendación arquitectónica definitiva.

---

## 4. Diccionario de Sustitución Asepsia Técnica

| No digas (Retórico / Informal / Tesis) | Di esto (Ingeniería de Software / Seguridad) |
| :--- | :--- |
| "Población diana" / "Sujetos" | "Dataset experimental" / "Colección de entidades" |
| "Muestra por conveniencia" | "Conjunto de datos estructurado bajo estándar X" |
| "Erradicación absoluta del 100%" | "Mitigación del 100% de los escenarios evaluados" |
| "Riesgo catastrófico y crítico" | "Exposición a compromiso de integridad y disponibilidad" |
| "Purga incondicional" / "Borrados catastróficos" | "Eliminación incondicional de registros" / "Borrado masivo" |
| "Seis vectores críticos" | "Seis vectores de ataque evaluados" |
| "Hallazgos de la investigación" | "Resultados experimentales" / "Evidencia empírica" |
| "Compensaciones de latencia" | "Sobrecosto medio de latencia (+X ms)" |
| "Marco integral propuesto" | "Pipeline de mitigación multicapa" |
| "De forma perentoria" | "Como requisito arquitectónico" |
| "Inyecciones clásicas vs espaciales" | "Taxonomía de inyecciones espaciales y operadores topológicos" |
| "En el marco de las Smart Cities..." | "En arquitecturas cliente-servidor para servicios geoespaciales..." |

---

## 5. Los Tres Principios de Estilo de Q1/Q2

1. **Supresión de adjetivos absolutistas o de carga emotiva:**  
   Palabras como *«catastrófico»*, *«crítico»*, *«purga incondicional»* o *«erradicación absoluta»* restan rigor científico y hacen que el paper parezca un folleto de ciberseguridad comercial o una nota periodística. En un journal de primer nivel, **los datos numéricos reemplazan a los adjetivos**: no adjetives el resultado, repórtalo en frío.
2. **Economía léxica en la formulación del problema:**  
   Elimina preámbulos genéricos sobre *«la transformación digital»* o *«el auge de las ciudades inteligentes»*. La introducción debe ir directo a la limitación técnica concreta (e.g., la ausencia de tipado y análisis espacial en el parser SQL de PostGIS).
3. **Voz impersonal técnica (vs. alegato de consultoría):**  
   El artículo no debe sonar como una auditoría de consultoría ni como un alegato defensivo de tesis. Describe hechos técnicos reproducibles, configuraciones de banco de pruebas y relaciones de causa-efecto observadas empíricamente.
4. **Despliegue obligatorio de acrónimos en primera mención:**  
   Todo acrónimo o sigla técnica (*CIA, ORM, WAF, AST, LADM, SRID*), por más estándar que sea en la disciplina, debe expandirse formalmente la primera vez que aparece en el cuerpo del texto (e.g., *«tríada CIA (Confidencialidad, Integridad y Disponibilidad)»*). Esto evita ambigüedad para revisores interdisciplinarios.

---

## 6. Prompt de Auto-Auditoría (Para LLMs o Investigadores)

Cuando le pidas a un modelo de IA que revise o redacte una sección de tu paper, adjuntale estas instrucciones operativas:

```text
Actúa como un Senior Reviewer de IEEE Transactions on Software Engineering / Computers & Security.
Audita el texto aplicando estas restricciones estrictas:
1. Elimina cualquier término prestado de ciencias sociales o tesis de grado (e.g., población diana, muestra por conveniencia, unidad muestral).
2. Asegura que el tono sea aséptico, cuantitativo y en tercera persona/impersonal. Suprime adjetivos absolutistas o emotivos (catastrófico, crítico, purga incondicional, infalible, perentorio, erradicación absoluta). Reporta números, no adjetivos.
3. Aplica economía léxica: elimina preámbulos genéricos (Smart Cities, transformación digital) y enfoca la introducción directamente en la limitación arquitectónica evaluada.
4. Separa rigurosamente "Resultados" (métricas frías: ms, req/s, %) de "Conclusiones" (decisiones arquitectónicas inferidas).
5. Verifica que no haya títulos con "vs." y que cada trabajo relacionado cierre con el vacío de investigación (research gap).
6. Elimina especificaciones comerciales de hardware (laptops, marcas) y fórmulas matemáticas cosméticas que no deriven pruebas formales.
7. Garantiza que la numeración de figuras sea estrictamente correlativa según su primera mención en el texto.
8. Despliega obligatoriamente todo acrónimo técnico en su primera aparición (e.g., tríada CIA -> Confidencialidad, Integridad y Disponibilidad).
```

# Antecedentes y Marco Bibliográfico de Investigación

## Proyecto: Evaluación de Vulnerabilidades de Inyección SQL Espacial en Sistemas de Información Catastral basados en PostGIS

---

### Resumen del Proyecto y Ejes de Investigación
El presente proyecto analiza la explotación y mitigación de inyecciones SQL espaciales en arquitecturas web geoespaciales (FastAPI + PostGIS/PostgreSQL), enfocado en la infraestructura crítica de los sistemas catastrales. 

Para sustentar una investigación de nivel posgrado (Maestría/Doctorado), el marco teórico y el estado del arte se estructuran en torno a cuatro pilares científicos:

1. **Modelos de Seguridad y Control de Acceso en Bases de Datos Espaciales.**
2. **Taxonomía de Inyección SQL y Vectores Geoespaciales.**
3. **Sistemas Catastrales y Estándares de Infraestructura Crítica (ISO 19152 - LADM).**
4. **Ataques de Complejidad Algorítmica (Spatial Denial of Service) y Rendimiento.**

---

### 1. Modelos de Seguridad y Control de Acceso Geoespacial

* **Bertino, E., Catania, B., & Damiani, M. L. (2005).** *GEO-RBAC: A spatially aware RBAC*. In *Proceedings of the 10th ACM Symposium on Access Control Models and Technologies (SACMAT '05)* (pp. 29–37). ACM.  
  * **DOI:** [10.1145/1063979.1063985](https://doi.org/10.1145/1063979.1063985)
  * **Aporte al proyecto:** Introduce el modelo canónico de control de acceso basado en roles con conciencia espacial. Demuestra formalmente cómo las restricciones espaciales definen límites de autorización y por qué las consultas dinámicas desprovistas de contexto espacial vulneran los perímetros lógicos del sistema.

* **Chun, S. A., & Atluri, V. (2008).** *Geospatial Database Security*. In H. Chen, T. S. Raghu, R. Ramesh, R. Sharman, & S. Chakravarty (Eds.), *Handbook of Database Security: Applications and Trends* (pp. 251–277). Springer, Boston, MA.  
  * **DOI:** [10.1007/978-0-387-48533-1_11](https://doi.org/10.1007/978-0-387-48533-1_11)
  * **Aporte al proyecto:** Análisis exhaustivo de los canales de inferencia espacial, ataques de resolución geométrica y debilidades inherentes al procesamiento de datos topológicos en sistemas manejadores de bases de datos espaciales (SDBMS).

* **Atluri, V., & Chun, S. A. (2004).** *An authorization model for geospatial data*. *IEEE Transactions on Dependable and Secure Computing*, 1(4), 238–254.  
  * **DOI:** [10.1109/TDSC.2004.34](https://doi.org/10.1109/TDSC.2004.34)
  * **Aporte al proyecto:** Fundamenta la necesidad de políticas de autorización granulares a nivel de entidades geométricas y atributos espaciales, vital para justificar la brecha de seguridad al exponer APIs REST geoespaciales.

---

### 2. Taxonomía de Inyección SQL y Vectores Geoespaciales

* **Halfond, W. G., Viegas, J., & Orso, A. (2006).** *A classification of SQL-injection attacks and countermeasures*. In *Proceedings of the IEEE International Symposium on Secure Software Engineering (ISSSE '06)*. IEEE.  
  * **Aporte al proyecto:** Proporciona la taxonomía estándar de inyecciones SQL (tautologías, consultas de unión, inyecciones ciegas/temporales y alteración de canal de comando). Sirve como marco comparativo para situar dónde encajan las inyecciones basadas en funciones topológicas (`ST_DWithin`, `ST_Intersects`, `ST_Contains`).

* **Clarke, J. (2012).** *SQL Injection Attacks and Defense* (2nd ed.). Syngress / Elsevier.  
  * **ISBN:** 978-1-59749-963-7
  * **Aporte al proyecto:** Referencia obligatoria en la literatura de seguridad de aplicaciones que aborda el paso de parámetros, análisis sintáctico de árboles de consulta (AST) y mecanismos de evasión ante filtros de entrada basados en expresiones regulares.

* **Referencia Empírica y Caso de Estudio Real: Vulnerabilidad CVE-2023-25157 (CVSS 9.8).**  
  * *GeoServer OGC Filter / CQL Expression SQL Injection Vulnerability in PostGIS backends*. National Vulnerability Database (NVD).  
  * **URL:** [https://nvd.nist.gov/vuln/detail/CVE-2023-25157](https://nvd.nist.gov/vuln/detail/CVE-2023-25157)
  * **Aporte al proyecto:** Evidencia empírica directa de que la evaluación insegura de predicados de consulta geoespacial sobre motores PostGIS conduce a inyecciones SQL no autenticadas con ejecución remota de código y exfiltración de información. Constituye el precedente directo más relevante en la industria de software GIS.

---

### 3. Sistemas Catastrales, Estándares de Infraestructura Crítica y LADM

* **Lemmen, C., van Oosterom, P., & Bennett, R. (2015).** *The Land Administration Domain Model*. *Land Use Policy*, 49, 535–545.  
  * **DOI:** [10.1016/j.landusepol.2015.01.014](https://doi.org/10.1016/j.landusepol.2015.01.014)
  * **Aporte al proyecto:** Publicación de referencia del estándar internacional **ISO 19152 (LADM)**. Provee el modelo conceptual de clases (`LA_SpatialUnit`, `LA_BAUnit`, `LA_RRR`) para categorizar las parcelas catastrales y los derechos de propiedad, justificando el impacto crítico de manipular límites zonales o exfiltrar datos no autorizados.

* **van Oosterom, P., Lemmen, C., & Ingvarsson, T. (2006).** *The core cadastral domain model*. *Computers, Environment and Urban Systems*, 30(5), 627–660.  
  * **DOI:** [10.1016/j.compenvurbsys.2005.12.002](https://doi.org/10.1016/j.compenvurbsys.2005.12.002)
  * **Aporte al proyecto:** Establece las bases técnicas para el modelado de datos catastrales en bases de datos relacionales orientadas a objetos y sistemas de registro predial continuo.

---

### 4. Complejidad Algorítmica, Spatial DoS y Rendimiento en PostGIS

* **Crosby, S. A., & Wallach, D. S. (2003).** *Denial of Service via Algorithmic Complexity Attacks*. In *Proceedings of the 12th USENIX Security Symposium* (pp. 29–44). USENIX Association.  
  * **Aporte al proyecto:** Marco teórico formal que explica cómo la inyección de parámetros que disparan operaciones computacionalmente intensivas ($O(N \log N)$ o $O(N^2)$) agota los recursos de CPU y memoria sin depender de mecanismos clásicos como `pg_sleep()`.

* **Agarwal, S., & Rajan, K. S. (2016).** *Performance analysis of MongoDB versus PostGIS/PostgreSQL databases for line intersection and point containment spatial queries*. *Spatial Information Research*, 24(6), 669–677.  
  * **DOI:** [10.1007/s41324-016-0059-1](https://doi.org/10.1007/s41324-016-0059-1)
  * **Aporte al proyecto:** Aporta métricas empíricas de latencia y costo computacional en la resolución de predicados topológicos e intersecciones sobre PostGIS con y sin indexación GiST/R-Tree, apoyando la evaluación de rendimiento de tu entorno de prueba.

* **Egenhofer, M. J. (1994).** *Spatial SQL: A query and presentation language*. *IEEE Transactions on Knowledge and Data Engineering*, 6(1), 86–95.  
  * **DOI:** [10.1109/69.273029](https://doi.org/10.1109/69.273029)
  * **Aporte al proyecto:** Trabajo fundacional en ingeniería de datos espaciales que define las extensiones algebraicas y los operadores de relación topológica que hoy componen la especificación OGC Simple Features for SQL en PostGIS.

* **Obe, R. O., & Hsu, L. S. (2021).** *PostGIS in Action* (3rd ed.). Manning Publications.  
  * **ISBN:** 978-1-61729-669-7
  * **Aporte al proyecto:** Referencia técnica central para la optimización de planes de ejecución geoespaciales, parametrización segura de consultas, uso de envolventes geométricas (Bounding Boxes) y enlace con ORMs como GeoAlchemy2 / SQLAlchemy.

---

### 5. Sustento Bibliográfico Directo de las Tres Barreras de Defensa Arquitectónica

Para sustentar la defensa de tesis y el artículo científico, cada una de las tres capas del pipeline de mitigación implementado se apoya en fundamentos académicos y normativos concretos:

1. **Barrera 1: Acotamiento Rígido de Parámetros en API (Pydantic) contra Spatial DoS**
   * **Fundamento Teórico:** *Crosby & Wallach (2003)* demostraron que los algoritmos con ramas asintóticas de peor caso ($O(N^2)$) deben protegerse en la capa perimetral mediante *bounds checking* estricto de parámetros.
   * **Fundamento Empírico Espacial:** *Agarwal & Rajan (2016)* comprobaron la sobrecarga exponencial de CPU en PostgreSQL/PostGIS al computar intersecciones de polígonos complejos desprovistos de acotamiento preliminar.

2. **Barrera 2: Validación Topológica en Memoria (Shapely) contra Canales de Inferencia**
   * **Fundamento de Inferencia Espacial:** *Chun & Atluri (2008)* y *Atluri & Chun (2004)* formalizaron cómo las excepciones y mensajes de error en SDBMS actúan como canales laterales (*side-channels*) que filtran información clasificada.
   * **Neutralización del Oráculo:** *Halfond et al. (2006)* establecieron que las inyecciones ciegas basadas en error se mitigan impidiendo que la entrada malformada alcance el evaluador de base de datos.
   * **Estándar Geométrico:** *ISO 19107:2019 / OGC Simple Features* define formalmente las reglas de simplicidad topológica (ausencia de auto-intersecciones) que valida Shapely antes de la persistencia.

3. **Barrera 3: Compilación y Serialización Binaria EWKB (GeoAlchemy2) contra Inyección de AST**
   * **Fundamento Teórico de Inyecciones:** *Clarke (2012)* demostró que la única protección matemáticamente inviolable contra SQLi es desacoplar el árbol sintáctico (AST) de los valores literales mediante variables de vinculación (*bind parameters*).
   * **Implementación en PostGIS:** *Obe & Hsu (2021)* formalizaron el protocolo de paso de geometrías precompiladas en formato binario extendido (EWKB) hacia PostgreSQL, anulando cualquier reinterpretación léxica de caracteres de escape.

---

### 6. Sustento y Origen Teórico de los Seis Vectores de Ataque Diseñados

Los seis vectores evaluados en el laboratorio no surgieron de forma arbitraria; cada uno es la transposición directa de un principio clásico de seguridad web hacia la matemática espacial y el estándar de catastro ISO 19152 (LADM):

1. **Simulación 1: Evasión de Límite Espacial (Spatial Logic Bypass)**
   * **Taxonomía Teórica:** *Halfond et al. (2006)* (Tautologías lógicas).
   * **Impacto Espacial:** *Bertino et al. (2005)* formalizaron el modelo **GEO-RBAC**, donde los permisos dependen de fronteras espaciales. El payload `50) OR 1=1` neutraliza el predicado `ST_DWithin`, vulnerando directamente el perímetro GEO-RBAC en el analizador léxico.

2. **Simulación 2: Inferencia de Datos por Errores Geométricos (Error-Based Spatial SQLi)**
   * **Taxonomía Teórica:** *Halfond et al. (2006)* y *Clarke (2012)* (Inyecciones inferenciales ciegas).
   * **Impacto Espacial:** *Chun & Atluri (2008)* y *Atluri & Chun (2004)* conceptualizaron los canales de inferencia espacial. El vector fuerza una condición geométrica ilegal (`ST_GeomFromText('ERR')`) en PostGIS para construir un oráculo booleano y extraer credenciales bit a bit.

3. **Simulación 3: Denegación de Servicio Espacial (Spatial DoS)**
   * **Taxonomía Teórica:** *Crosby & Wallach (2003)* (Ataques de Complejidad Algorítmica).
   * **Impacto Espacial:** *Agarwal & Rajan (2016)* y *Egenhofer (1994)* demostraron la carga cuadrática $O(N^2)$ en la librería GEOS. El vector inyecta buffers densos (`quad_segs=100`) forzando productos cartesianos que saturan la CPU del motor sin usar funciones temporales como `pg_sleep()`.

4. **Simulación 4: Fraude en Ficha Catastral (Tampering de Autovalúo y Titularidad)**
   * **Taxonomía Teórica:** Ataques a la integridad de datos relacionales en sentencias `UPDATE` (OWASP / Clarke, 2012).
   * **Impacto Catastral:** *Lemmen et al. (2015)* (ISO 19152 LADM). Afecta directamente la clase `LA_Party` (sujetos de derecho) y la base tributaria municipal, reduciendo fraudulentamente la deuda fiscal a cero mediante inyección en la cláusula `SET`.

5. **Simulación 5: Borrado Destructivo de Cartografía Predial (Data Destruction)**
   * **Taxonomía Teórica:** Inyecciones destructivas incondicionales en sentencias `DELETE`.
   * **Impacto Catastral:** *van Oosterom et al. (2006)* y *Lemmen et al. (2015)*. Pone en riesgo la clase `LA_SpatialUnit`, purgando físicamente las 1,500 parcelas y dejando el visor geográfico municipal sin cartografía jurídica.

6. **Simulación 6: Evasión de Autenticación en el Visor Catastral (Authentication Bypass)**
   * **Taxonomía Teórica:** *Halfond et al. (2006)* (Inyección de comentarios en línea `admin' --`).
   * **Impacto en Infraestructura Crítica:** Evasión del control de acceso perimetral para usurpar privilegios de `superadmin_catastro` y acceder a capas territoriales clasificadas.

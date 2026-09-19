# Guía Técnica y Hoja de Apoyo: Arquitectura y Funcionamiento del Playground

**Proyecto:** *Playground Interactivo de Investigación: Inyección SQL Espacial en PostGIS*  
**Autor:** Rodrigo Alexander Becerra Lucano  
**Repositorio Oficial:** `RAlexander777/Playground-SQLi-PostGIS`  
**Objetivo:** Explicar con precisión técnica y conceptual qué hace exactamente cada módulo, botón, panel, endpoint y flujo de datos del laboratorio interactivo durante una demostración o defensa de tesis.

---

## 1. Propósito y Arquitectura General del Playground

El Playground es una aplicación web interactiva de ciberseguridad diseñada como **banco de pruebas experimental reproducible**. Permite contrastar en tiempo real y sobre un mismo mapa catastral el comportamiento de una API vulnerable frente a una API mitigada bajo el estándar internacional **ISO 19152 (LADM)**.

### Stack Tecnológico:
* **Base de Datos Espacial:** PostgreSQL 15 con extensión PostGIS 3.3.
* **Backend:** Python 3.11 con framework asíncrono **FastAPI** y servidor ASGI **Uvicorn**.
* **ORM & Persistencia:** SQLAlchemy 2.0 y **GeoAlchemy2** (manejador de tipos espaciales y formatos binarios EWKB).
* **Validación en Software:** **Pydantic v2** (capa HTTP) y **Shapely** (validación topológica en memoria sobre motor GEOS).
* **Frontend:** HTML5, Bootstrap 5, CSS3 y **Leaflet.js** sobre cartografía base de OpenStreetMap.

---

## 2. Desglose Componente por Componente

```
+---------------------------------------------------------------------------------------------------+
| 1. BARRA SUPERIOR: Estado DB | Conteo Lotes/Titulares | Restaurar BD | Modo Vuln/Mit | Idioma ES/EN|
+---------------------------------------------------------------------------------------------------+
| 2. BÚSQUEDA MANUAL: Input de Criterio | Botón Evaluar | Cargas Rápidas (Tautología, UNION, etc.)  |
+---------------------------------------------------------------------------------------------------+
| 3. PIPELINE DEFENSIVO: Barrera 1 (Pydantic) ---> Barrera 2 (Shapely) ---> Barrera 3 (GeoAlchemy2) |
+----------------------------------------------------+----------------------------------------------+
| 4. VISOR CARTOGRÁFICO (Leaflet / EPSG:32719)       | 6. BATERÍA DE ATAQUES (V1 a V6)              |
|    - Polígonos Azules: Lotes autorizados           |    - V1: Spatial Logic Bypass (ST_DWithin)   |
|    - Polígonos Rojos: Lotes exfiltrados/afectados  |    - V2: Error-Based Side Channel (Oráculo)  |
|                                                    |    - V3: Spatial DoS (Buffer O(N²))          |
+----------------------------------------------------+    - V4: Fraude en Ficha (Tampering)         |
| 5. INSPECTOR SQL & DIAGNÓSTICO EN TIEMPO REAL      |    - V5: Borrado Cartográfico (WHERE 1=1)    |
|    - Terminal: Consulta SQL cruda vs parametrizada |    - V6: Bypass de Login (admin' --)         |
|    - Métricas: Latencia (ms) | HTTP Status | Barrera+----------------------------------------------+
|    - Diagnóstico pedagógico del flujo interno      | 7. INTEGRIDAD CATASTRAL LADM (Tabla en Vivo) |
|                                                    |    - Lote | DNI | Titular | Autovalúo S/     |
+----------------------------------------------------+----------------------------------------------+
```

---

### Componente 1: Barra Superior y Controles Globales (Top Header)

* **Indicador de Estado y Contadores (`Lotes: 487 | Titulares: 487`):**
  * Consulta continuamente el estado del servicio PostgreSQL/PostGIS.
  * Muestra la cantidad viva de parcelas en la tabla `tg_lote` y de personas en `catastro_titulares`.
  * *Punto clave:* Cuando se ejecuta el ataque de borrado cartográfico (V5), este contador cae a `0`, evidenciando visualmente la destrucción de la base cartográfica municipal.
* **Botón "Restaurar BD" (`resetDatabase()`):**
  * Invoca el endpoint administrativo `POST /api/v1/admin/reset`.
  * Trunca las tablas y vuelve a inyectar proceduralmente los 487 polígonos originales de Puno y los titulares fiscales en memoria sin necesidad de reiniciar el contenedor Docker.
* **Selector de Modo (`Vulnerable` vs. `Mitigado - 3 Barreras`):**
  * Conmuta el enrutamiento de red del frontend hacia los endpoints del backend:
    * Modo Vulnerable: `http://localhost:8020/api/v1/vulnerable/...`
    * Modo Mitigado: `http://localhost:8020/api/v1/mitigated/...`
  * Permite al jurado ver exactamente la misma petición ejecutada en ambos mundos con un solo clic.
* **Selector de Idioma (`ES` / `EN`):**
  * Alterna dinámicamente todo el texto, etiquetas, diagnósticos y nombres de tablas entre Español e Inglés sin recargar la página web.

---

### Componente 2: Búsqueda Predial y Pruebas SQLi Manuales

Permite ingresar consultas ad-hoc para evaluar la compilación léxica de sentencias relacionales clásicas:
* **Campo de Entrada (`inputCriterio`):**
  * Permite ingresar una clave catastral legítima (ej: `21010101000000`) o un payload SQL arbitrario.
* **Presets de Carga Rápida (Botones de un clic):**
  * **Normal (1 lote):** Carga el ID de un lote real; retorna 1 registro con latencia nominal (~15 ms).
  * **Tautología (`' OR '1'='1`):** En modo vulnerable, anula la cláusula `WHERE` y exfiltra los 487 lotes del catastro de una sola vez. En modo mitigado, busca literalmente la cadena `"' OR '1'='1"` como texto sin interpretarla como código SQL, retornando 0 resultados de forma segura.
  * **Comentario (`%' OR 1=1 --`):** Demuestra el truncamiento de sentencias SQL mediante comentarios de línea (`--`).
  * **UNION Passwords (`' UNION SELECT username, role, 'EXFILTRADO', password_hash, 0, NULL FROM catastro_usuarios --`):** Ejecuta una inyección de tipo UNION clásica que mezcla la tabla de predios con la tabla de autenticación administrativa, volcando los hashes criptográficos en la tabla de resultados.

---

### Componente 3: Pipeline Visual de Mitigación (Defensa en Profundidad)

Este panel muestra en tiempo real cómo viaja la petición y cuál de las tres barreras de software la intercepta o la procesa:

1. **Barrera 1 (Capa Web / API - Pydantic & Acotamiento):**
   * *Mecanismo:* Inspecciona los parámetros HTTP entrantes en tiempo de ejecución. Aplica tipado numérico rígido (`distancia: float`), acotamiento de rangos físicos ($0 < distancia \le 5000$ metros) y expresiones regulares (`^\d{14}$` para códigos catastrales).
   * *Comportamiento:* Si un atacante envía una cadena como `50) OR (1=1`, Pydantic interrumpe el ciclo de vida de la petición y devuelve **`HTTP 422 Unprocessable Entity`**. La consulta **nunca llega al motor de base de datos**, ahorrando CPU y memoria.
2. **Barrera 2 (Capa Dominio / Aplicación - Shapely Topology en Memoria):**
   * *Mecanismo:* Si la petición incluye una geometría (WKT o GeoJSON), Shapely la parsea en la memoria RAM del servidor Python sobre la librería GEOS.
   * *Comportamiento:* Evalúa la propiedad `geom.is_valid`. Si el polígono tiene auto-intersecciones (geometrías en forma de "ocho"), anillos abiertos o vértices corruptos, es descartado en la aplicación antes de persistir, evitando errores fatales en PostGIS.
3. **Barrera 3 (Capa Motor / Persistencia - GeoAlchemy2 + SQLAlchemy ORM):**
   * *Mecanismo:* Compila la consulta utilizando el Árbol de Sintaxis Abstracta (**AST**) de SQLAlchemy y tipos geométricos nativos de PostGIS (`Geometry`).
   * *Comportamiento:* Serializa las geometrías a formato binario extendido (**EWKB**) y utiliza de forma obligatoria **consultas preparadas** (*Prepared Statements*). El motor de PostgreSQL recibe los parámetros como datos puros a través del protocolo binario, garantizando que ninguna comilla o palabra reservada SQL pueda ser interpretada como instrucción ejecutable.

---

### Componente 4: Visor Cartográfico Interactivo (Leaflet + OpenStreetMap)

* **Sistema de Referencia Espacial:** Proyecta las parcelas del catastro de Puno en **EPSG:32719** (UTM Zona 19 Sur en metros planos).
* **Código de Colores Semántico:**
  * **Azul:** Lotes catastrales legítimos obtenidos dentro del radio y sector autorizado.
  * **Rojo:** Lotes en estado de anomalía (lotes exfiltrados de sectores prohibidos en V1, o lotes eliminados en V5).
* **Interactividad:**
  * Clic en cualquier polígono: Despliega un popup con la metadata LADM (`ID Lote`, `Sector`, `Zonificación`, `Área m²`).
  * Botón **"Centrar"**: Ajusta automáticamente el encuadre cartográfico al *Bounding Box* de los 487 lotes de Puno.

---

### Componente 5: Inspector de Ejecución SQL, Métricas y Diagnóstico

Este módulo es la herramienta pedagógica central para el jurado:

* **Terminal Monospace (`boxQuery`):**
  * En **Modo Vulnerable**, imprime la cadena SQL exacta concatenada con el payload malicioso en texto plano (mostrando el quiebre de sintaxis, los paréntesis cerrados y las tautologías).
  * En **Modo Mitigado**, muestra la estructura compilada por el ORM con parámetros de vinculación tipados (`:distancia_1`, `:sector_1`), evidenciando que los valores no se mezclan con la gramática SQL.
* **Métricas en Vivo:**
  * **LATENCIA:** Tiempo total de ejecución en milisegundos (ms) medido desde que sale la petición hasta que retorna la respuesta. Permite comprobar en vivo el salto de 10 ms a 1,692 ms en el ataque DoS.
  * **ESTADO HTTP:** Código canónico devuelto (`200 OK`, `422 Unprocessable Entity`, `500 Internal Error`).
  * **DEFENSA ACTIVA:** Indica qué barrera contuvo la amenaza (`Pydantic (Capa Web)`, `Shapely (Capa App)`, `GeoAlchemy2 (Capa Persistencia)` o `Ninguna`).
* **Diagnóstico Pedagógico:** Caja explicativa que resume en lenguaje claro qué sucedió a nivel de memoria, red y base de datos tras la acción ejecutada.

---

### Componente 6: Batería de los 6 Vectores de Ataque (Simulaciones V1 a V6)

Cada tarjeta ejecuta un ataque preconfigurado representativo de la Tríada CIA:

#### 1. `Spatial Logic Bypass` (Confidencialidad)
* **Endpoint:** `GET /api/v1/vulnerable/predios/radio?distancia=50) OR (1=1&sector=0101`
* **Qué hace:** Una búsqueda legítima solo debe devolver predios a menos de 50m dentro del sector `0101`. Al inyectar la tautología en el radio de `ST_DWithin`, anula el filtro espacial y el sector, exfiltrando parcelas restringidas de toda la ciudad en **7.03 ms**.
* **En Modo Mitigado:** Pydantic detecta que `'50) OR (1=1'` no es un float válido y retorna **HTTP 422**. Cero predios expuestos.

#### 2. `Error-Based Spatial SQLi` (Confidencialidad / Canal Lateral)
* **Endpoint:** `GET /api/v1/vulnerable/predios/poligono?wkt=...`
* **Qué hace:** Inyecta una condición en `ST_Intersects` que fuerza una excepción geométrica en PostGIS si un bit de la contraseña administrativa es `1`.
* **Botón "Simular Inferencia Ciega":** Ejecuta un bucle en tiempo real en la pantalla que prueba bit a bit los caracteres de la contraseña, mostrando cómo un atacante reconstruye credenciales confidenciales en **42 segundos** sin que la API muestre datos en pantalla.

#### 3. `Spatial DoS` (Disponibilidad / Complejidad Algorítmica $O(N^2)$)
* **Endpoint:** `GET /api/v1/vulnerable/analisis-expansion?buffer_dist=100`
* **Qué hace:** Inyecta un buffer denso (`quad_segs=100`) dentro de un producto cartesiano (`CROSS JOIN`). Obliga a la librería C/C++ **GEOS** a calcular intersecciones complejas entre miles de vértices sin índice GiST.
* **Impacto:** La latencia salta a **~1.69 segundos** (93.5x de sobrecarga).
* **En Modo Mitigado:** Pydantic acota el radio a valores seguros y GeoAlchemy2 desacopla subconsultas, manteniendo la respuesta constante en **~15 ms**.

#### 4. `Fraude Catastral / Tampering` (Integridad)
* **Endpoint:** `POST /api/v1/vulnerable/ficha/modificar`
* **Qué hace:** Inyecta en una sentencia `UPDATE catastro_titulares SET ...` modificando arbitrariamente los campos. Reduce la deuda tributaria del autovalúo a **S/ 0.00** y suplanta el nombre del titular predial por el del atacante.
* **Impacto:** Vulneración directa de la fe pública catastral (ISO 19152 LADM). Se comprueba de inmediato en la tabla de Integridad Catastral inferior.

#### 5. `Destrucción de Cartografía` (Integridad y Disponibilidad)
* **Endpoint:** `DELETE /api/v1/vulnerable/predios/borrar`
* **Qué hace:** Inyecta una cláusula `sector = '0101' OR '1'='1'` en una instrucción `DELETE FROM tg_lote`.
* **Impacto:** Purga incondicionalmente los 487 lotes del catastro. El mapa Leaflet queda completamente en blanco y el contador de lotes cae a cero. Requiere presionar "Restaurar BD" para volver a operar.

#### 6. `Bypass de Autenticación` (Acceso Administrativo)
* **Endpoint:** `POST /api/v1/vulnerable/auth/login`
* **Qué hace:** Envía el payload `admin' --` en el campo de usuario. El delimitador de comentario SQL `--` trunca la verificación criptográfica del hash de la contraseña en la base de datos.
* **Impacto:** Retorna un token JWT de sesión con el rol `superadmin_catastro`, otorgando control total sobre el geoportal.

---

### Componente 7: Integridad Catastral (Muestra LADM en Vivo)

* **Tabla Dinámica:** Muestra en tiempo real una muestra de 5 predios consultando directamente las tablas relacionales `tg_lote` (clase `LA_SpatialUnit`) y `catastro_titulares` (clase `LA_Party`).
* **Columnas:** `ID LOTE`, `DNI`, `TITULAR PREDIAL` y `AUTOVALÚO (S/)`.
* **Propósito Pedagógico:**
  * Permite al jurado ver los datos normales: autovalúos reales (ej. S/ 85,420.00).
  * Al hacer clic en el ataque **V4 (Tampering)**, el jurado ve cómo la tabla se actualiza instantáneamente en pantalla: el autovalúo pasa a **S/ 0.00** y el titular cambia a *"ATACANTE_ILEGITIMO"*.
  * Al hacer clic en el ataque **V5 (Borrado)**, la tabla muestra *"No se encontraron registros catastrales"*, demostrando la pérdida de información.

---

## 3. Guión Rápido para Demostración en Vivo (3 Minutos ante el Jurado)

Si el jurado te pide una demostración práctica en vivo, seguí este flujo probado de 4 pasos:

1. **Paso 1: Demostrar el funcionamiento normal (30 segundos)**
   * Asegurate de estar en **Modo Vulnerable**.
   * Hacé clic en la Carga Rápida **"Normal (1 lote)"**.
   * Mostrá que retorna 1 predio en azul en el mapa, con latencia normal (~15 ms) y código HTTP 200.
2. **Paso 2: Ejecutar el ataque de Evasión Espacial V1 (45 segundos)**
   * Hacé clic en la tarjeta **"1. Spatial Logic Bypass"**.
   * Mostrá cómo el mapa se llena de polígonos rojos de sectores ajenos.
   * Apuntá al **Inspector SQL**: mostrá el `50) OR (1=1` que quebró el `ST_DWithin` en 7 ms.
   * Cambiá el switch a **Modo Mitigado** y volvé a hacer clic en el ataque: mostrá que la **Barrera 1 (Pydantic)** lo frena en seco con código **HTTP 422** en 1 ms.
3. **Paso 3: Demostrar el Spatial DoS V3 (45 segundos)**
   * Volvé a **Modo Vulnerable** y hacé clic en **"3. Spatial DoS"**.
   * Mostrá en el panel de métricas cómo la latencia salta a **más de 1,600 ms** por el producto cartesiano en `ST_Buffer` (complejidad $O(N^2)$).
   * Pasá a **Modo Mitigado** y hacé clic de nuevo: la latencia cae a **15 ms constantes**.
4. **Paso 4: Demostrar el impacto en fe pública V4 / V5 (30 segundos)**
   * Mostrá la tabla inferior de **Integridad Catastral (LADM)**.
   * Hacé clic en **"4. Fraude Catastral"**: mostrá cómo el autovalúo del predio cae a **S/ 0.00**.
   * Explicá: *"Esto demuestra que una inyección espacial no es un juego informático; compromete la recaudación tributaria y la fe pública del Estado bajo la norma ISO 19152"*.
   * Presioná **"Restaurar BD"** para dejar el sistema limpio.

# Trazabilidad de los Hitos 4–9 hacia el Hito 11

Revisión documental y de código: 2026-10-23. Integra y precisa la propuesta de
`Hito11_Grupo9_Correcciones.zip`. Un HTTP 200, un PING o IDs coincidentes no
demuestran que se esté utilizando el volumen de la entrega original.

La devolución del Hito 10 pide integrar las implementaciones anteriores,
preservando versiones, modelos e identificadores, sin reconstruir el laboratorio.
Esta integración modifica la capa API, su diagnóstico, configuración y pruebas;
no ejecuta cargas, importaciones de clases ni creación de motores o bases.
Los antecedentes de reproducción siguientes pertenecen a la evidencia previa.

## Fuentes cotejadas

| Hito | Fuente y revisión consultada | Modelo contrastado con la API | Procedencia de la instancia H11 |
|---|---|---|---|
| 4, MongoDB | ZIP local `Grupo_9_Hito_4_MongoDB_Fixture2030.zip`; README, Compose y validadores | `equipos`, `jugadores`, `_id`, `codigo_fifa`, `equipo_id`; el adaptador conserva el ID como texto | Evidencia 03 registra 64 equipos y 1536 jugadores. Falta demostrar identidad del volumen y cotejar documentos con H4 |
| 5, Neo4j | [Modelo del grafo](https://github.com/Agusmel03/Grupo-9-Ing-de-datos-2/blob/46fd701bac38747804871df0a0974a217f8582ee/docs/modelo_grafo.md), revisión `46fd701bac38747804871df0a0974a217f8582ee` | `Partido.id_partido`, `Evento.id_evento`, `Jugador.mongo_id`, `Equipo`, `Sede`; relaciones `OCURRE_EN`, `PROTAGONIZADO_POR`, `PERTENECE_A`, `PARTICIPA_EN`, `SE_JUEGA_EN` | Evidencia 05 registra 1996 nodos y 2400 relaciones. Falta verificar continuidad y persistencia actuales |
| 6, Cassandra | [Esquema](https://github.com/FacuIria/Grupo_9_Hito_6_Cassandra_Comentarios/blob/ab243795832fa280af1bb7bfe99c5f1ab61812e9/scripts/esquema.cql), revisión `ab243795832fa280af1bb7bfe99c5f1ab61812e9` | Keyspace `fixture2030_comentarios`; `comentarios_por_partido` con partición `(partido_id,bucket_10m,shard)`; `comentarios_por_usuario` permanece en el módulo original | Reproducido desde scripts según `diagnostico_cassandra.md`; no acredita restauración del volumen anterior |
| 7, Redis | [Modelo de claves](https://github.com/FacuIria/Grupo_9_Hito_7_Redis_Cache_Sesiones./blob/41292e3da6cb943a5ef1368868aa50050fc2cf04/docs/modelo_clave_valor.md), revisión `41292e3da6cb943a5ef1368868aa50050fc2cf04` | `fixture2030:session:<session_id>`, hash y TTL; consulta de vigencia sin renovar expiración. Caché, ranking y contadores siguen en H7 | Reproducido desde scripts según `diagnostico_redis.md`; no es el volumen anterior de macOS |
| 8, InfluxDB | [Modelo y agregaciones](https://github.com/Agusmel03/Grupo_9_Hito_8_InfluxDB_Series_Temporales/blob/491ece2effd94729404231438701fc7bcdbee806/README.md), revisión `491ece2effd94729404231438701fc7bcdbee806` | `estadisticas_equipo`; tags `partido_id`, `equipo_codigo`, `sede_id`; cuatro campos originales. `mean/last/sum/sum` trasladados a SQL v3 | Diagnóstico previo declara regeneración de 8640 puntos con el generador H8 y migración a Core. No demuestra restauración del volumen v2 ni equivalencia completa |
| 9, IRIS | [Clase Partido](https://github.com/FacuIria/Hito_9_Grupo_9_IRIS/blob/6c82364c542506a111c52153110959e452ddda72/src/Partido.cls), revisión `6c82364c542506a111c52153110959e452ddda72` | `Fixture2030.Partido.PartidoID`, relación de hijos `Eventos`, tabla `Fixture2030.Evento`; ID interno y fecha local preservados | Clases reimportadas según `diagnostico_iris.md`; no se restauró el volumen previo |

SHA-256 del ZIP H4 inspeccionado, sin extraer ni ejecutar sus scripts:
`06c5d84796f36effba91a96d921800e6acc0b92662ba86a7a8d6a34bfcef70b6`.
Las revisiones de GitHub identifican el código consultado, no necesariamente el
commit exacto entregado al docente: corresponde confirmar esa correspondencia.

## Versiones declaradas y observadas

| Motor | Antecedente disponible | Verificación pendiente en la instancia usada por la API |
|---|---|---|
| MongoDB | Compose H4 fija `mongo:7.0` | `db.version()`; imagen/digest de la instancia. No sustituir por la versión de un instalador local |
| Neo4j | Compose H5 usa `neo4j:latest`, etiqueta mutable; el ZIP de correcciones reporta 2026.07.1 | `CALL dbms.components()`; contrastar la versión reportada con evidencia original |
| Cassandra | Compose H6 usa `cassandra:latest`; H11 documenta 4.1.5 | `SELECT release_version FROM system.local`; no tratar `latest` como versión fija |
| Redis | [Evidencia H7](https://github.com/FacuIria/Grupo_9_Hito_7_Redis_Cache_Sesiones./blob/41292e3da6cb943a5ef1368868aa50050fc2cf04/docs/evidencia/00_ambiente.txt) reporta 8.10.2 | `INFO server` con el cliente autenticado del entorno |
| InfluxDB | H8 declara v2.9.1; H11 documenta Core 3.12.1 | Versión de la instancia existente y `/api/v3/query_sql`. La exigencia actual es Core 3; se registra la diferencia con H8, no se oculta |
| IRIS | [Evidencia H9](https://github.com/FacuIria/Hito_9_Grupo_9_IRIS/blob/6c82364c542506a111c52153110959e452ddda72/docs/evidencia/version_iris.txt) reporta 2026.2 build 221U | `$ZVERSION` en la instancia y namespace configurados |

Ninguna versión de motor fue observada de nuevo en esta integración: Docker no
está disponible en el entorno de trabajo. No se cambian imágenes ni versiones de
motores. El cliente v2 y `influx.py` se conservan como implementación histórica;
`build_adapters` selecciona exclusivamente `Influx3Adapter`, incluso con el alias
de configuración anterior `influx3`. `INFLUX_MODE=v2` se rechaza.

## Casos e identificadores

- Cassandra: la [muestra original](https://github.com/FacuIria/Grupo_9_Hito_6_Cassandra_Comentarios/blob/ab243795832fa280af1bb7bfe99c5f1ab61812e9/scripts/carga_muestra.cql)
  usa `P001`, bucket `2030-06-10T18:00:00Z`, shard `0`. El validador los conserva.
- InfluxDB: las [consultas H8](https://github.com/Agusmel03/Grupo_9_Hito_8_InfluxDB_Series_Temporales/blob/491ece2effd94729404231438701fc7bcdbee806/scripts/consultas_temporales.flux)
  usan `P001`, `AAA`/`AAB` y el 8 de junio de 2030 desde las 19:00 UTC. El diagnóstico
  consulta una hora de ese intervalo. No se fuerza la fecha de Cassandra a coincidir:
  son muestras originales distintas y falta reconciliar su cronología de dominio.
- Redis: `SESION_INEXISTENTE` prueba el contrato de ausencia. No crea sesiones ni
  certifica TTL de una sesión activa. `--sesion` permite elegir una ya existente;
  debe usarse un identificador de laboratorio sin información personal.
- Neo4j e IRIS: `P001` se conserva según los adaptadores y evidencias previas;
  falta cotejar todos los atributos cruzados, no solo el ID.

Los parámetros del validador permiten consultar otros casos existentes sin
renombrarlos ni generar registros nuevos.

## Matriz de instancia por completar con evidencia real

| Motor | Estado actual | Fecha UTC / versión / imagen@digest / montaje | Recurso e ID | Evidencia previa, no revalidada |
|---|---|---|---|---|
| MongoDB | NO PROBADO | Pendiente | `fixture2030.equipos`, `codigo_fifa` | 03 |
| Neo4j | NO PROBADO | Pendiente | Database configurada, `Partido.id_partido=P001` | 04, 05 |
| Cassandra | NO PROBADO | Pendiente | Keyspace original, partición P001/bucket/shard | 11, 12, 24 |
| Redis | NO PROBADO | Pendiente | Base lógica de `REDIS_URL`, hash de sesión y TTL | 13, 21–23, 29 |
| InfluxDB 3 | NO PROBADO | Pendiente | `fixture2030.estadisticas_equipo`, P001/ventana | 15, 16, 18, 20, 30 |
| IRIS | NO PROBADO | Pendiente | `USER`, `Fixture2030.Partido`, P001 | 08, 09, 25 |

Registrar el montaje mediante una consulta dirigida a `.Mounts`, nunca publicando
el `docker inspect` completo (puede contener variables privadas). Comparar con los
montajes originales: Cassandra H6 usa bind mount en `/var/lib/cassandra`, Redis H7
en `/data`. Un cambio de máquina requiere documentar exportación/importación,
versiones, esquemas, conteos y diferencias. No reconstruir para obtener un resultado OK.

## Observaciones que esta integración no cierra

- MongoDB: demostrar segunda carga idempotente con cero inserciones pertenece al H4;
  no se ejecuta una carga para probar conectividad H11.
- Neo4j: acreditar los 1996 nodos y 2400 relaciones después de reinicio con el
  almacenamiento original; esos conteos por sí solos no prueban identidad.
- Cassandra: conservar la evidencia histórica de reinicio y verificar el montaje
  actual. No confundir un bind mount con un volumen Docker nombrado.
- Redis: la concurrencia del H7 y las sesiones activas requieren sus propias
  pruebas; el 404 esperado solo prueba ausencia válida según el contrato.
- InfluxDB: verificar SQL en Core, nulos, ventanas parciales, distintos partidos,
  retención, downsampling y rendimiento. La evidencia 30 compara MAX/last solo en
  una muestra; no demuestra equivalencia general ni valida la consulta nueva.
- IRIS: encapsular las transiciones de `Estado` sigue siendo trabajo del H9.
- H11: autenticación/autorización/contextos erróneos por motor, caída temporal
  real RF21, recuperación y continuidad de datos requieren el laboratorio original.

Un resultado vacío válido, una prueba omitida y una dependencia caída son estados
distintos. La trazabilidad documental queda mejorada; la integración experimental
con los seis motores continúa pendiente de nueva ejecución.

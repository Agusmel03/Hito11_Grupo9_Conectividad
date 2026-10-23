# Integración del paquete de correcciones

Fecha: 2026-10-23. Base revisada: `772aeedf7e9f76a8eb17d18b35b21b34781f5a43`.
Rama: `correcciones/hito11-conectividad-trazabilidad`.

## Fuentes y alcance

Se cotejaron los PDF suministrados por el equipo y la devolución del profesor del
Hito 10: evitar reconstruir el laboratorio, usar las implementaciones previas y
preservar versiones, modelos e identificadores. Se aplicó la instrucción actual
de utilizar InfluxDB 3 Core y de conservar toda la API y la persistencia.

| Archivo fuente local | SHA-256 |
|---|---|
| `Hito11_Grupo9_Correcciones.zip` | `59bb77b5a704fc8e392b966f8e0477b1077b5ace0d6c23ca8eb8da129d52542a` |
| `Hito_10_Requisitos_Tecnicos_-_API_REST_Integrada_Fixture_2030.md.pdf` | `6ec70b254a0b5685fb3bdea3b9ce4c3a5cf7cfbe69e42df595a0f001861d18ee` |
| `Hito 11 — Requisitos Técnicos_ Evaluación de la Conectividad.pdf` | `f2493540d8095691d85ed436a2246844e80cbb1ee0ab806f9f13961a7aa0389f` |

Las instrucciones de copia del ZIP se trataron como propuestas a comparar, no
como autorización para sobrescribir funcionalidades. La versión previa permanece
en el commit base; no se agregaron copias que puedan divergir del código activo.

## Comparación y decisiones

| Archivo del ZIP | Diferencia con la base | Integración realizada |
|---|---|---|
| `README_CORRECCIONES.md` | Guía de copia, advertencias y cambios sugeridos | Incorporada en esta guía y el README; no se promueve la copia automática |
| `api_hito11/validar_conectividad.py` | Reemplazaba salud por rutas funcionales; 404 aceptado con solo una clave `error`; origen fijado a contenedor | Conserva `tcp/native/api/all`, `--producto`, salud y salida por motor; suma lectura funcional, contratos reales, request ID, categorías, SKIP, parámetros y JSON con origen/revisión explícitos |
| `config/configuracion-ejemplo.env` | Añade database Neo4j, corrige keyspace/datacenter y modo v3 | Integrados manteniendo comentarios y placeholders; sin secretos reales |
| `docs/trazabilidad_hitos_4_9.md` | Documento nuevo con procedencia y pendientes | Integrado y cotejado con ZIP H4, código H5–H9, commits y evidencias históricas |
| `__pycache__/validar_conectividad.cpython-313.pyc` | Bytecode generado | No incorporado; no es fuente ni evidencia |

## Correcciones de código

- `Settings`: puerto predeterminado 8181, modo v3 validado; acepta `influx3` como
  alias anterior. Las variables del entorno siguen teniendo prioridad.
- `build_adapters`: mantiene los seis productos y permite construir solo los
  seleccionados. Un driver faltante se registra como SKIP en diagnóstico nativo;
  no impide evaluar los otros motores. Los clientes ya creados se cierran ante fallos.
- InfluxDB: `/api/v3/query_sql`, token privado y database configurada. Se conservan
  los cuatro campos y dimensiones H8, filtro `[desde,hasta)`, resolución y límite.
  Pases usa `selector_last(..., time)['value']`, no MAX; tiempo etiqueta el final
  de la ventana. Se conservan microsegundos de los límites UTC.
- Fallos HTTP/conexión de InfluxDB pasan a 503 con dependencia identificada;
  timeout usa código `dependencia_timeout`. Errores inesperados mantienen 500 seguro.
  Las operaciones SQL registran duración y request ID a través del guard existente.
- El ping InfluxDB usa `SELECT time ... LIMIT 1` para evitar COUNT de toda la tabla.
  Una tabla vacía accesible no demuestra que exista el dataset original.
- La descripción OpenAPI se alinea con el SQL. Ninguna ruta ni modelo se elimina.
  El adaptador histórico `influx.py` y su dependencia permanecen disponibles, pero
  no se seleccionan en la API. No se modifica `requirements.txt` ni se cambian drivers.

La elección de selector y etiqueta temporal se apoya en la documentación de
[selectores SQL de Core](https://docs.influxdata.com/influxdb3/core/reference/sql/functions/selector/),
[date_bin](https://docs.influxdata.com/influxdb3/core/reference/sql/functions/time-and-date/) y
[aggregateWindow de Flux](https://docs.influxdata.com/flux/v0/stdlib/universe/aggregatewindow/).
Es una corrección de código pendiente de contrastar con el motor y los datos reales;
no equivale a haber migrado retención, downsampling ni todo el laboratorio H8.

## Requisitos oficiales y estado

| Requisito H11 | Cambio o evidencia | Límite pendiente |
|---|---|---|
| RF1–3, RNF1/14/18 | Configuración, mapa existente, procedencia y revisiones documentadas | Verificar valores efectivos, versiones y montajes desde la API original |
| RF4–6, RNF2/4/13 | TCP distingue DNS/rechazo/timeout; cliente nativo por producto, SKIP si falta driver | Nuevas pruebas reales desde la red original; DNS depende del resolver del SO |
| RF7–14 | Lecturas funcionales con contexto/IDs originales, ausencia Redis, SQL Core | Autenticación, autorización, contexto erróneo, TTL activo, salud HTTP del motor Influx y versiones efectivas |
| RF15–16, RF19 | Salud conservada + seis rutas funcionales; estado HTTP, request ID, duración, fecha/origen/revisión | Evidencias reales y logs correlacionados del despliegue |
| RF17–18, RNF7/8/11/12 | Tests locales de 404/422/503/500 y timeout Influx; detalles privados no se imprimen | Casos de fallo de cada driver real; timeout distinguido en Influx, otros motores mantienen su contrato genérico 503 |
| RF20 | Recuperación de transporte simulada en prueba unitaria; evidencias Redis 21–23 preservadas | No atribuir la simulación a una recuperación real nueva |
| RF21 | Sigue pendiente | No se detuvo ningún contenedor; la corrección de puerto anterior no cumple detención real |
| RF22, RNF16 | Cambios preparados para PR al repositorio del equipo | Revisión y aceptación del PR por el equipo |
| RNF6/17 | Solo lecturas; pruebas nuevas separadas de evidencia histórica | Sin afirmaciones de disponibilidad actual, rendimiento o continuidad de volúmenes |

También se revisaron H10 §5.2–5.13: separación por adaptadores, modelos originales,
contratos, errores y configuración. La documentación no declara resuelta la
observación principal de procedencia mientras falte verificar las instancias.

## Validación realizada

- Python 3.13.7 en Windows; dependencias locales de pruebas según
  `api_hito11/requirements-test.txt`, en `.venv` excluido de Git.
- Ejecución final: **40 pruebas unitarias aprobadas**, con una advertencia de
  deprecación de Starlette/AnyIO. Dobles HTTP y adaptadores en
  memoria, exclusivamente dentro de tests; no reemplazan la API ni crean datos en motores.
- Suite original ejecutada sin modificar: **9 fallos de transporte** al intentar
  acceder a `127.0.0.1:8000`. No son nueve regresiones funcionales comprobadas: el
  entorno Docker no está accesible. Las sondas a 8000 y 8011 devolvieron ConnectTimeout.
- Docker CLI no disponible en PATH ni en su ubicación habitual. No se instalaron,
  crearon, detuvieron ni reiniciaron motores. No se modificaron volúmenes o datos.
- Las 9 aprobaciones y 18 comprobaciones de la evidencia original son antecedentes,
  no resultados de esta ejecución. La nueva modalidad completa incorpora 24
  resultados (TCP, nativo, salud y funcional por motor); salud se solicita una vez.

Ver también [trazabilidad](trazabilidad_hitos_4_9.md) y el procedimiento del README.
Resumen de ejecución: [evidencia 31](evidencia/31_integracion_correcciones.txt).
Las pruebas unitarias de SQL verifican la construcción de consultas y contratos;
**no ejecutan un motor SQL**. La sintaxis y semántica de Core deben probarse en el
servidor existente antes de aprobar el cambio.

## Pruebas adicionales sobre el entorno original

1. Confirmar versiones, digest y montajes mediante lecturas; completar la matriz
   de trazabilidad con fecha, origen y commit desplegado.
2. Ejecutar los cuatro modos y la suite original desde la API existente. Probar
   sesión Redis ya activa, recurso inexistente y resultados vacíos sin cargar datos.
3. Consultar en Core ventanas de 1m/5m/15m/1h, límites parciales, valores nulos y
   distintos partidos. Contrastar último valor, promedio, sumas y timestamps con
   los datos crudos existentes; no reactivar InfluxDB 2 como dependencia de H11.
4. Verificar salud HTTP de InfluxDB separada de autorización SQL y database;
   credenciales inválidas, contexto incorrecto y timeouts en configuración local
   de prueba, sin alterar la configuración persistente del laboratorio.
5. Realizar RF21 en una ventana coordinada: detener temporalmente una dependencia,
   observar liveness y degradación, volver a iniciarla y comprobar recuperación.
   Conservar datos y montajes; no usar eliminación de contenedores/volúmenes.
6. Adjuntar evidencia redactada y logs con request ID. Mantener cada resultado no
   ejecutado como NO PROBADO, no como disponible ni caído.

## Inventario de archivos

Modificados:

- `README.md`
- `api_hito11/validar_conectividad.py`
- `api_hito11/app/config/settings.py`
- `api_hito11/app/main.py`
- `api_hito11/app/adapters/influx3.py`
- `api_hito11/app/routes/api.py` (solo descripción OpenAPI)
- `config/configuracion-ejemplo.env`
- `docs/auditoria_requisitos_hito11.md`
- `docs/diagnostico_influx3.md`

Agregados:

- `api_hito11/requirements-test.txt`
- `api_hito11/tests/unit/test_correcciones.py`
- `pytest.ini`
- `docs/trazabilidad_hitos_4_9.md`
- `docs/integracion_correcciones.md`
- `docs/evidencia/31_integracion_correcciones.txt`

Sin eliminaciones. Se conserva bytecode fuera de Git; no se incorporan los ZIP,
PDF, credenciales ni dependencias instaladas en `.venv`.

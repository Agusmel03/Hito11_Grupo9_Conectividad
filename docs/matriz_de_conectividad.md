# Matriz de conectividad — Hito 11

## Entorno y alcance

Fecha de la ultima verificacion integral: 2026-10-23.

Origen de las pruebas: contenedor fixture2030-hito11-api.
Red: fixture2030-hito11-net.
API publicada en Windows: http://localhost:8011.

Estado observado: disponible para las seis dependencias
en el momento de la evaluacion.

## Matriz general

| Producto | TCP | Nativo | API | Estado observado | Evidencia |
|---|---|---|---|---|---|
| MongoDB | OK | OK | OK | Disponible | 28 |
| Neo4j | OK | OK | OK | Disponible | 28 |
| Cassandra | OK | OK | OK | Disponible | 28 |
| Redis | OK | OK | OK | Disponible | 28, 29 |
| InfluxDB 3 | OK | OK | OK | Disponible | 28, 30 |
| IRIS | OK | OK | OK | Disponible | 28 |

Resultado: 18 de 18 comprobaciones satisfactorias.

## Pruebas e interpretacion

TCP:
- Verifica resolucion del host y conexion al puerto.
- No garantiza autenticacion ni permisos.

Nativo:
- Ejecuta el metodo ping del adaptador correspondiente.
- Verifica la operacion definida por ese adaptador.
- No constituye una auditoria completa de autorizacion.

API:
- Consulta /api/v1/salud.
- Verifica el estado reportado por cada dependencia.
- Las rutas funcionales se probaron por separado.

## Latencias

Las duraciones individuales, expresadas en milisegundos,
se encuentran en la evidencia 28.

La latencia observada corresponde a estas pruebas puntuales.
No representa una medida de rendimiento sostenido.

## Diagnostico

MongoDB: conexion y lectura funcional verificadas.
Neo4j: Bolt y lectura funcional verificados.
Cassandra: CQL y lectura limitada de comentarios verificadas.
Redis: PING, ausencia y sesion activa verificadas.
InfluxDB 3: SQL y consulta temporal verificadas.
IRIS: conexion SQL y lectura de partido y eventos verificadas.

## Clasificacion de estados

Disponible:
La prueba configurada finalizo correctamente.

No disponible:
La prueba se ejecuto y fallo.

Degradado:
La API funciona, pero una dependencia presenta problemas.

No probado:
La prueba aun no se ejecuto.

Desconocido:
La evidencia no permite determinar el estado.

## Fallo controlado

Se simulo una configuracion incorrecta de Redis
en una instancia temporal de la API.

Resultado: HTTP 503 y estado degradado.
Posteriormente se corrigio la configuracion
y se recupero HTTP 200.

Evidencias: 21, 22 y 23.

No se detuvo el contenedor principal de Redis.

## Evidencias

- docs/evidencia/19_api_seis_motores_ok.txt
- docs/evidencia/21_redis_degradado_http503.txt
- docs/evidencia/22_api_principal_disponible.txt
- docs/evidencia/23_redis_recuperado_http200.txt
- docs/evidencia/28_diagnostico_capas_seis_motores.txt
- docs/evidencia/29_redis_sesion_activa_http200.txt
- docs/evidencia/30_influx3_comparacion_agregaciones.txt

## Limitaciones

- Los estados corresponden a la fecha evaluada.
- No se verifico disponibilidad permanente.
- No se realizaron pruebas de carga.
- La persistencia se comprobo tras reinicio,
  no tras eliminar y recrear contenedores.
- La equivalencia general entre MAX y last
  en InfluxDB 3 no esta demostrada.

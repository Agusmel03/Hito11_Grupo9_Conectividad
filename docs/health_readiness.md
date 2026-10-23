# Health, readiness y diagnostico — Hito 11

## Objetivo

Diferenciar el estado del proceso HTTP
de la disponibilidad de sus dependencias.

## Liveness

Endpoint implementado:

GET /health/live

Direccion desde Windows:

http://localhost:8011/health/live

Resultado verificado: HTTP 200.

Este endpoint confirma que la API responde,
pero no demuestra que las bases de datos
esten disponibles.

## Diagnostico por dependencia

Endpoint implementado:

GET /api/v1/salud

Direccion desde Windows:

http://localhost:8011/api/v1/salud

Evalua los seis motores:

- MongoDB
- Neo4j
- Cassandra
- Redis
- InfluxDB 3
- IRIS

Se registra el estado y la duracion
de cada comprobacion.

Resultado observado:
HTTP 200 con seis dependencias en estado ok.

## Readiness

No se implemento un endpoint independiente
denominado /health/ready.

El endpoint /api/v1/salud permite evaluar
la disponibilidad de las dependencias.

Como propuesta de readiness:

- Preparada: todas las dependencias necesarias
  responden correctamente.
- Degradada: una dependencia presenta fallas.
- No preparada: no es posible cumplir las
  operaciones necesarias de la aplicacion.

Esta propuesta no debe confundirse con
un endpoint de readiness ya implementado.

## Estados de diagnostico

Disponible:
La comprobacion configurada finaliza correctamente.

No disponible:
Se intento la comprobacion y fallo.

Degradado:
La API permanece activa, pero una dependencia falla.

No probado:
No se ejecuto la comprobacion.

Desconocido:
No hay informacion suficiente para evaluar el estado.

Los nombres anteriores describen la clasificacion
documental. La API puede utilizar otros valores
en sus respuestas JSON.

## Timeouts y costo

Los adaptadores utilizan limites de espera
configurables para evitar bloqueos indefinidos.

El diagnostico por dependencia ejecuta
comprobaciones reales contra los motores.

No debe interpretarse como una medicion
de rendimiento o disponibilidad permanente.

No se requiere consultar las seis bases
en cada solicitud funcional normal.

## Falla controlada

Se utilizo una instancia temporal de la API
con configuracion incorrecta de Redis.

Resultado:
- Dependencia Redis afectada.
- Respuesta HTTP 503.
- API principal disponible.
- Recuperacion posterior con HTTP 200.

Evidencias:
- docs/evidencia/21_redis_degradado_http503.txt
- docs/evidencia/22_api_principal_disponible.txt
- docs/evidencia/23_redis_recuperado_http200.txt

## Observabilidad

Las respuestas HTTP incluyen X-Request-ID.

Los registros permiten relacionar
solicitud, dependencia, operacion,
estado y duracion.

No deben incluir contrasenas ni tokens.

## Limitaciones

- No existe un endpoint readiness separado.
- Los resultados representan pruebas puntuales.
- No se midio rendimiento bajo carga.
- No se garantiza disponibilidad permanente.

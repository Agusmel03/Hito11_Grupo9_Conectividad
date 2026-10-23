# Diagnostico de fallas — Hito 11

## Objetivo

Identificar problemas de conectividad por capa
sin confundir un puerto abierto con una conexion
autenticada y funcional.

## Capas de diagnostico

1. Configuracion: comprobar variables y puertos.
2. DNS: verificar resolucion del host.
3. TCP: comprobar acceso al puerto.
4. Protocolo: utilizar el cliente apropiado.
5. Autenticacion: validar la identidad.
6. Autorizacion: comprobar permisos.
7. Contexto: seleccionar database o namespace.
8. Operacion: ejecutar una lectura minima.
9. API: verificar el endpoint correspondiente.

## Interpretacion de errores

| Situacion | Posible causa | Accion recomendada |
|---|---|---|
| DNS_ERROR | Host inexistente o incorrecto | Revisar nombre y red Docker |
| CONNECTION_REFUSED | Puerto cerrado o sin listener | Verificar servicio y puerto |
| TIMEOUT | Red, ruta o servicio lento | Revisar conectividad y timeout |
| Error de autenticacion | Credenciales incorrectas | Revisar configuracion privada |
| Error de autorizacion | Permisos insuficientes | Revisar privilegios |
| Contexto inexistente | Database o namespace incorrecto | Revisar contexto |
| HTTP 404 | Recurso inexistente | Verificar identificador |
| HTTP 422 | Parametros invalidos | Revisar contrato de API |
| HTTP 503 | Dependencia no disponible | Revisar diagnostico por motor |
| HTTP 500 | Error interno | Revisar logs y request ID |

Estas causas son hipotesis de diagnostico.
No todas las situaciones fueron provocadas
experimentalmente durante el Hito 11.

## Falla controlada verificada

Se ejecuto una instancia temporal de la API
con una configuracion incorrecta de Redis.

Resultado observado:
- Redis no disponible en la instancia temporal.
- API temporal: HTTP 503.
- La API principal permanecio disponible.
- Tras corregir la configuracion, HTTP 200.

Evidencias:
- docs/evidencia/21_redis_degradado_http503.txt
- docs/evidencia/22_api_principal_disponible.txt
- docs/evidencia/23_redis_recuperado_http200.txt

No se detuvo el contenedor principal de Redis.

## Diferencia entre ausencia y falla

Una sesion Redis inexistente puede producir HTTP 404
sin significar que Redis este caido.

Una solicitud con parametros invalidos puede
producir HTTP 422 sin implicar un problema de red.

La disponibilidad se determina mediante pruebas
de conectividad y operaciones concretas.

## Observabilidad

La API registra identificadores de solicitud,
dependencia, operacion, resultado y duracion.

El encabezado X-Request-ID permite correlacionar
solicitudes HTTP con registros del servicio.

No deben registrarse passwords ni tokens.

## Limitaciones pendientes

- No se verificaron experimentalmente todos los tipos de error.
- No se acredito una detencion real de una dependencia.
- No se realizaron pruebas de carga ni rendimiento.
- La conectividad exitosa no garantiza disponibilidad permanente.

# Auditoria de requisitos — Hito 11

## Alcance

Esta matriz relaciona la consigna oficial
con las implementaciones y evidencias disponibles.

Los estados son preliminares y deben validarse
contra los resultados concretos de cada prueba.

## Requisitos funcionales

| RF | Tema | Estado preliminar | Evidencia o pendiente |
|---|---|---|---|
| RF1 | Dependencias | Documentado | mapa_de_dependencias.md |
| RF2 | Topologia | Documentado | topologia_y_entornos.md |
| RF3 | Configuracion | Documentado | configuracion-ejemplo.env |
| RF4 | DNS | Verificado | evidencia 17 y 28 |
| RF5 | TCP | Verificado | evidencia 17 y 28 |
| RF6 | Cliente nativo | Verificado | evidencia 28 |
| RF7 | Autenticacion y contexto | Parcial | Revisar permisos por motor |
| RF8 | Operacion minima | Verificado | evidencias funcionales |
| RF9 | MongoDB | Verificado | evidencia 03 |
| RF10 | Neo4j | Verificado | evidencias 04 y 05 |
| RF11 | Cassandra | Verificado | evidencias 11 y 24 |
| RF12 | Redis | Verificado | evidencias 13 y 29 |
| RF13 | InfluxDB | Verificado | evidencias 15 y 20 |
| RF14 | IRIS | Verificado | evidencias 08, 09 y 25 |
| RF15 | Rutas API | Verificado | evidencias 19 a 27 |
| RF16 | Matriz | Documentado | matriz_de_conectividad.md |
| RF17 | Fallas de dependencia | Parcial | HTTP 503 y recuperacion Redis; otros escenarios documentados |
| RF18 | Clasificacion de errores | Parcial | HTTP 404 y 422 comprobados; HTTP 503 en falla controlada |
| RF19 | Logs y request ID | Verificado | evidencia 26 y logs |
| RF20 | Recuperacion | Verificado | evidencias 21 a 23 |
| RF21 | Detencion temporal | Pendiente | No se detuvo un motor |
| RF22 | Publicacion GitHub | Pendiente | Sin remoto configurado |

## Requisitos no funcionales

| RNF | Tema | Estado preliminar |
|---|---|---|
| RNF1 | Reproducibilidad | Parcial |
| RNF2 | Capas de diagnostico | Parcial |
| RNF3 | Entorno correcto | Documentado |
| RNF4 | Clientes adecuados | Verificado |
| RNF5 | Timeouts | Documentado |
| RNF6 | No destructivo | Verificado |
| RNF7 | Seguridad | Verificado en archivos revisados |
| RNF8 | Evidencias redactadas | Pendiente de auditoria |
| RNF9 | Estados | Documentado |
| RNF10 | Diagnostico de fallas | Parcial |
| RNF11 | Observabilidad | Documentado |
| RNF12 | Degradacion | Parcial |
| RNF13 | Independencia de pruebas | Verificado |
| RNF14 | Integridad del contexto | Parcial |
| RNF15 | Legibilidad | Documentado |
| RNF16 | GitHub | Pendiente |
| RNF17 | Honestidad experimental | Documentado |
| RNF18 | Trazabilidad | Parcial |

## Pendientes prioritarios

1. Comprobar autenticacion, autorizacion y contexto.
2. Evaluar cobertura de errores y timeouts.
3. Revisar seguridad de todas las evidencias.
4. Determinar si hace falta una prueba de detencion real.
5. Confirmar reproducibilidad y publicacion en GitHub.

## Interpretacion

Documentado no significa necesariamente
verificado experimentalmente.

Verificado significa que existe una prueba concreta
con resultado satisfactorio dentro del alcance indicado.

Parcial significa que falta evidencia o una comprobacion.

Pendiente significa que todavia no se acredito.

## Resultados finales de comprobacion

Fecha: 2026-10-23.

- Liveness de API: HTTP 200.
- Sesion Redis inexistente: HTTP 404.
- Parametro de comentarios invalido: HTTP 422.
- Salud: seis dependencias con estado ok.
- Falla controlada previa: HTTP 503 y recuperacion HTTP 200.
- Pruebas automatizadas previas: 9 aprobadas.
- Diagnostico por capas previo: 18 comprobaciones correctas.

## Aspectos no demostrados completamente

- Autorizacion y errores de contexto por cada motor.
- Timeout y error interno provocados experimentalmente.
- Detencion real de un contenedor de dependencia.
- Publicacion del repositorio en GitHub.
- Revision exhaustiva de secretos en todo el historial Git.

La falla mediante configuracion incorrecta de Redis
fue reversible y se documento. No debe describirse
como una detencion real del contenedor Redis.

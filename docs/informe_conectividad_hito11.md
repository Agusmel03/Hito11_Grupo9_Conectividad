# Informe de conectividad - Hito 11 - Grupo 9

## Proyecto

Fixture Mundial 2030 - Ingeniería de Datos II.

## Objetivo

Evaluar la conectividad entre la API REST del Hito 10
y los seis motores de datos utilizados en el proyecto.

## Motores evaluados

| Motor | Salud API | Consulta funcional |
|---|---|---|
| MongoDB | OK | HTTP 200 |
| Neo4j | OK | HTTP 200 |
| Cassandra | OK | HTTP 200 |
| Redis | OK | Consulta ejecutada; sesion inexistente HTTP 404 |
| InfluxDB 3 Core | OK | HTTP 200 |
| InterSystems IRIS | OK | HTTP 200 |

## Resultados

### Conectividad

Se verifico la disponibilidad de los seis motores mediante
el endpoint GET /api/v1/salud.

Resultado observado: HTTP 200, estado general ok.

### Consultas funcionales

- MongoDB: consulta de equipos.
- Neo4j: consulta del grafo.
- Cassandra: lectura de comentarios del partido P001.
- Redis: consulta de sesion inexistente, HTTP 404 esperado.
- InfluxDB 3: estadisticas temporales del partido P001.
- IRIS: lectura del partido P001 y sus dos eventos.

### Fallos controlados

Se probo una instancia temporal de la API con Redis
deliberadamente inaccesible.

Resultados:
- API temporal: HTTP 503, estado degradado.
- API principal: permanecio disponible.
- API temporal recuperada: HTTP 200.
- Instancia temporal retirada al finalizar.

### Pruebas automatizadas

Framework: pytest.

Resultado confirmado:
9 pruebas aprobadas.

Archivo:
api_hito11/tests/test_integracion_hito11.py

## Evidencias principales

- 17_dns_tcp_seis_motores.txt
- 18_influx3_desde_python.txt
- 19_api_seis_motores_ok.txt
- 20_api_estadisticas_p001_ok.txt
- 21_redis_degradado_http503.txt
- 22_api_principal_disponible.txt
- 23_redis_recuperado_http200.txt
- 24_cassandra_comentarios_http200.txt
- 25_iris_partido_eventos_http200.txt
- 26_salud_seis_motores_http200.txt
- 27_pytest_integracion_nueve_pruebas.txt

Todas estas evidencias se encuentran en docs/evidencia/.

## Limitaciones y verificaciones pendientes

- Contrastar la implementacion con la consigna oficial y sus RF.
- Ampliar las pruebas automatizadas de errores y validaciones.
- Verificar que las agregaciones SQL de InfluxDB 3 conservan
  la semantica requerida respecto de las consultas Flux originales.
- Revisar el alcance de las pruebas de persistencia existentes.
- Verificar el comportamiento de sesiones Redis activas.
- Completar las instrucciones de ejecucion y entrega.

## Conservacion de datos

Las consultas funcionales utilizadas son de solo lectura.
Se mantuvieron separados los recursos del Hito 11.
No se reemplazo la API original del Hito 10.

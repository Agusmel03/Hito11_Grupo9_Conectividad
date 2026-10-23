# Informe de conectividad - Hito 11 - Grupo 9

## Proyecto

Fixture Mundial 2030 - IngenierÃ­a de Datos II.

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

## Persistencia verificada

Se comprobaron lecturas posteriores al reinicio de
cuatro contenedores de bases de datos:

- Cassandra: comentario P001 / USR001 conservado.
- Redis: clave permanente conservada, TTL -1.
- InfluxDB 3: 8640 puntos y 4 partidos conservados.
- IRIS: partido P001 y dos eventos conservados.

Evidencias:
- 12_cassandra_persistencia.txt
- 13_redis_persistencia.txt
- 16_influx3_persistencia.txt
- 08_iris_antes.txt
- 09_iris_despues.txt

Estas pruebas confirman persistencia tras reinicio,
no necesariamente tras eliminar y recrear contenedores.
## Verificaciones complementarias finales

### Diagnostico por capas

Se comprobaron los seis motores mediante tres capas:

- TCP: resolucion DNS y conexion al puerto.
- Native: comprobacion mediante el adaptador del motor.
- API: consulta HTTP de salud de la dependencia.

Resultado: 18 de 18 comprobaciones satisfactorias.

Evidencia: 28_diagnostico_capas_seis_motores.txt.

### Sesion activa de Redis

Se creo una sesion temporal con estado activa y TTL de 120 segundos.

La API devolvio HTTP 200 y confirmo el estado activa.
La sesion temporal fue eliminada al finalizar.

Evidencia: 29_redis_sesion_activa_http200.txt.

### Comparacion de InfluxDB 3

Se analizaron 2160 registros del partido P001,
agrupados en 36 ventanas de cinco minutos.

No se detectaron diferencias entre MAX y last
para los datos examinados.

Esto no demuestra equivalencia general.
MAX y last pueden diferir en otros conjuntos de datos.
Las etiquetas temporales de Flux y SQL tambien difieren.

Evidencia: 30_influx3_comparacion_agregaciones.txt.
## Limitaciones y verificaciones pendientes

- Contrastar la implementacion con la consigna oficial y sus RF.
- Ampliar las pruebas automatizadas de errores y validaciones.
- Verificar que las agregaciones SQL de InfluxDB 3 conservan
  la semantica requerida respecto de las consultas Flux originales.
- Verificar persistencia tras eliminar y recrear contenedores; solo se comprobo el reinicio.
- Sesiones Redis activas: verificadas mediante HTTP 200.
- Instrucciones de ejecucion y diagnostico: documentadas en README.md.

## Conservacion de datos

Las consultas funcionales utilizadas son de solo lectura.
Se mantuvieron separados los recursos del Hito 11.
No se reemplazo la API original del Hito 10.

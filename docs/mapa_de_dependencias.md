# Mapa de dependencias — Hito 11

## Entorno evaluado

La API del Hito 11 se ejecuta dentro del contenedor
fixture2030-hito11-api, conectado a la red Docker
fixture2030-hito11-net.

Puerto publicado de la API: localhost:8011.
Puerto interno de la API: 8000.

Las conexiones a las bases de datos se realizan desde
el contenedor utilizando la red Docker, no desde
localhost de Windows.

## Dependencias integradas

| Producto | Modulo | Puerto interno | Protocolo | Contexto |
|---|---|---|---|---|
| MongoDB | Equipos | 27017 | MongoDB Wire Protocol | fixture2030 |
| Neo4j | Grafo y eventos | 7687 | Bolt | neo4j |
| Cassandra | Comentarios | 9042 | CQL | fixture2030_comentarios |
| Redis | Sesiones | 6379 | RESP | Base logica configurada |
| InfluxDB 3 | Estadisticas | 8181 | HTTP / SQL | fixture2030 |
| IRIS | Partidos y eventos | 1972 | Superserver / SQL | USER |

Los hosts reales corresponden a los servicios
conectados a fixture2030-hito11-net y se obtienen
de las variables privadas de configuracion.

No se publican URI con credenciales ni tokens.

## Clientes y operaciones

| Producto | Cliente | Operacion minima | Endpoint API |
|---|---|---|---|
| MongoDB | PyMongo | Ping y lectura de equipos | /api/v1/equipos |
| Neo4j | Driver Neo4j | Ping y lectura de grafo | /api/v1/grafo |
| Cassandra | Driver CQL | Conexion y lectura limitada | /api/v1/partidos/P001/comentarios |
| Redis | redis-py | PING y lectura de sesion | /api/v1/sesiones/{id} |
| InfluxDB 3 | Cliente HTTP SQL | Consulta temporal | /api/v1/partidos/P001/estadisticas |
| IRIS | Cliente SQL | Lectura de partido y eventos | /api/v1/objetos/partidos/P001 |

## Resultados observados

Se comprobaron las seis dependencias desde el
entorno de la API mediante:

- Resolucion y conectividad TCP.
- Comprobacion nativa con el adaptador.
- Diagnostico HTTP de la API.

Resultado: 18 de 18 comprobaciones satisfactorias.

Evidencia:
docs/evidencia/28_diagnostico_capas_seis_motores.txt

Las pruebas confirman conectividad en el entorno
evaluado, no disponibilidad permanente ni rendimiento.

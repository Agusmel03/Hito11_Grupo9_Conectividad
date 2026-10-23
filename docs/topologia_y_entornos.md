# Topologia y entornos — Hito 11

## Arquitectura evaluada

El entorno utiliza Docker Desktop sobre Windows.

La API integrada se ejecuta en el contenedor:

- fixture2030-hito11-api

Red de comunicacion:

- fixture2030-hito11-net

Los seis motores se ejecutan en contenedores
independientes conectados a la misma red.

## Contenedores

| Producto | Contenedor | Puerto interno |
|---|---|---|
| API integrada | fixture2030-hito11-api | 8000 |
| MongoDB | fixture2030-mongodb | 27017 |
| Neo4j | fixture2030-neo4j | 7687 |
| Cassandra | baseDeDatosIICassandra | 9042 |
| Redis | baseDeDatosIIRedis | 6379 |
| InfluxDB 3 | fixture2030-influxdb3 | 8181 |
| IRIS | baseDeDatosIIIRIS | 1972 |

## Conexion desde Windows

La API publica el puerto 8011 en la notebook.

Direccion de acceso:

http://localhost:8011

Los puertos publicados de cada base de datos
pueden diferir de sus puertos internos.

Para comprobar las publicaciones reales:

    docker ps

## Conexion desde la API

Dentro del contenedor, localhost representa
al propio contenedor y no a Windows.

La API utiliza las direcciones configuradas
mediante variables de entorno privadas y
la red Docker para comunicarse con los motores.

Ejemplo:

- Windows accede a la API por localhost:8011.
- La API escucha internamente en el puerto 8000.
- Los motores se alcanzan por la red Docker.

## Origen de las pruebas

Pruebas TCP iniciales:
- Ejecutadas desde Windows con Python.

Diagnostico por capas:
- Ejecutado dentro de fixture2030-hito11-api.

Pruebas nativas:
- Ejecutadas mediante los adaptadores de FastAPI.

Pruebas HTTP:
- Ejecutadas contra la API integrada.

## Conservacion del entorno

- No se eliminaron volumenes.
- No se sustituyo la API original del Hito 10.
- Las pruebas de conectividad utilizan
  operaciones minimas no destructivas.

## Evidencias

- docs/evidencia/17_dns_tcp_seis_motores.txt
- docs/evidencia/19_api_seis_motores_ok.txt
- docs/evidencia/28_diagnostico_capas_seis_motores.txt

Los resultados representan el estado observado
durante la evaluacion, no una garantia
de disponibilidad permanente.

# Diagnóstico Cassandra — Hito 11

## Origen

Laboratorio reproducido desde el repositorio original del Hito 6.

## Entorno

- Motor: Apache Cassandra 4.1.5.
- Contenedor: baseDeDatosIICassandra.
- Clúster: Fixture2030Cluster.
- Puerto CQL: 9042.
- Keyspace: fixture2030_comentarios.
- Persistencia: directorio local montado en /var/lib/cassandra.

## Pruebas exitosas

- Estado healthy.
- Consulta CQL a system.local.
- Creación del esquema original.
- Verificación de las tablas comentarios_por_partido y comentarios_por_usuario.
- Ejecución de carga_muestra.cql.
- Lectura del comentario P001 / USR001 / Que partidazo.
- Reinicio del contenedor sin pérdida del comentario.

## Alcance

Se reprodujo el esquema y la carga de muestra originales del Hito 6.
No se restauró el volumen anterior de macOS.
No se ejecutaron las cargas masivas.

## Pendiente

- Prueba TCP desde el entorno de la API.
- Conexión con el driver Cassandra de FastAPI.
- Consulta mediante endpoint HTTP de la API.
- Pruebas de fallo controlado y recuperación.

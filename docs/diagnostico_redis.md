# Diagnóstico Redis — Hito 11

## Origen

Laboratorio reproducido desde el repositorio original del Hito 7.

## Entorno

- Motor: Redis.
- Contenedor: baseDeDatosIIRedis.
- Puerto: 6379.
- Persistencia: AOF habilitada.
- Configuración AOF: appendfsync everysec.
- Almacenamiento: directorio local montado en /data.

## Pruebas exitosas

- Contenedor en estado healthy.
- Conexión mediante Redis PING: PONG.
- Inicialización original ejecutada: 4 respuestas y 0 errores.
- Carga de muestra original ejecutada: 11 respuestas y 0 errores.
- Lectura del caché del partido P001.
- Verificación del TTL del caché.
- Lectura del ranking de partidos.
- Reinicio del contenedor sin pérdida de la clave permanente.
- Verificación de fixture2030:config:version = hito7.
- TTL de la clave permanente = -1.

## Alcance

Se reprodujo el laboratorio desde el código original del Hito 7.
No se restauró el volumen anterior de macOS.

Las claves temporales pueden desaparecer al vencer su TTL.
Esto es un comportamiento esperado y no implica una falla de persistencia.

## Pendiente

- Prueba TCP desde el entorno de la API.
- Conexión mediante el cliente Redis de FastAPI.
- Consulta a través de un endpoint HTTP.
- Prueba de fallo controlado y recuperación.

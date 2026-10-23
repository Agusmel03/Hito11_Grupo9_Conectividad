# Diagnóstico InfluxDB 3 Core — Hito 11

## Origen

Migración del laboratorio original del Hito 8 desde InfluxDB 2 a InfluxDB 3 Core.

## Entorno

- Motor: InfluxDB 3 Core 3.12.1.
- Contenedor: fixture2030-influxdb3.
- Puerto HTTP: 8181.
- Base de datos: fixture2030.
- Persistencia: volumen Docker independiente.
- Autenticación: token administrativo local, excluido de Git.

## Pruebas exitosas

- Inicio del servidor y creación del catálogo.
- Corrección de permisos del volumen.
- Creación de la base fixture2030.
- Autenticación mediante token.
- Generación de 8640 puntos con el script original del Hito 8.
- Escritura HTTP exitosa (204).
- Lectura mediante SQL.
- Verificación de 8640 puntos y 4 partidos.
- Regeneración del token administrativo.
- Consulta SQL exitosa con la nueva credencial.

## Alcance

Se reutilizó el generador original del Hito 8.
La migración utiliza InfluxDB 3 Core y SQL en lugar de InfluxDB 2 y Flux.

No se restauró el volumen original de InfluxDB 2.
No se ejecutó la carga masiva completa ni se migraron
todavía todas las consultas y agregaciones Flux.

## Pendiente

- Verificar persistencia después del reinicio.
- Comprobar conectividad desde el entorno de FastAPI.
- Ejecutar una consulta mediante la API REST.
- Realizar pruebas de fallo y recuperación.

## Actualización de integración - Hito 11

Se completaron las siguientes verificaciones:

- Persistencia después del reinicio del contenedor.
- Conservación de 8640 puntos y 4 partidos.
- Conectividad desde Python y desde FastAPI.
- Consulta HTTP de estadísticas del partido P001: HTTP 200.
- Prueba automatizada de integración aprobada.

Evidencias: 16, 18, 20 y 27 de docs/evidencia/.

Sigue pendiente comparar formalmente la semántica de las
agregaciones SQL de InfluxDB 3 con las consultas Flux originales.

No se documentó una prueba de fallo controlado específica
de InfluxDB 3.

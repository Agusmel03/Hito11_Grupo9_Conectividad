# Hito 11 - Grupo 9 - Evaluación de Conectividad

## Proyecto

Fixture Mundial 2030 - Ingeniería de Datos II.

Este hito evalúa la conectividad de la API REST del Hito 10 con los motores NoSQL utilizados durante la cursada.

## Productos

- MongoDB
- Neo4j
- Cassandra
- Redis
- InfluxDB
- InterSystems IRIS

## Objetivos

1. Verificar configuración y conectividad TCP.
2. Comprobar protocolo, autenticación y contexto.
3. Ejecutar lecturas mínimas no destructivas.
4. Probar la API REST integrada.
5. Registrar fallos controlados y recuperación.
6. Documentar resultados y limitaciones.

## Reutilización

Este repositorio contiene pruebas, scripts, configuración de ejemplo y evidencias.

No reemplaza la API del Hito 10 ni recrea automáticamente los datos de los hitos anteriores.
## Ejecucion y verificacion del Hito 11

### Requisitos
- Docker Desktop y PowerShell.
- Seis motores disponibles en la red fixture2030-hito11-net.
- API principal: fixture2030-hito11-api.
- Configuracion privada: config/hito11_api.env.

### Verificar conectividad
Ejecutar desde PowerShell:

    docker ps
    curl.exe -i http://localhost:8011/health/live
    curl.exe -i http://localhost:8011/api/v1/salud

### Pruebas automatizadas
Ejecutar desde PowerShell:

    docker exec fixture2030-hito11-api python -m pytest /app/tests/test_integracion_hito11.py -v --tb=short

Resultado verificado: 9 pruebas aprobadas.

### Documentacion
- Informe: docs/informe_conectividad_hito11.md
- Diagnosticos: docs/diagnostico_*.md
- Evidencias: docs/evidencia/
- Pruebas: api_hito11/tests/

### Precauciones
- No subir credenciales ni tokens a Git.
- No eliminar los volumenes Docker.
- No modificar la API original del Hito 10.

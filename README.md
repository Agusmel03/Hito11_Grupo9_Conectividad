# Hito 11 - Grupo 9 - Evaluación de Conectividad

## Proyecto

Fixture Mundial 2030 - Ingeniería de Datos II.

Este hito evalúa la conectividad de la API REST del Hito 10 con los motores NoSQL utilizados durante la cursada.

## Integración de correcciones (2026-10-23)

**Para cerrar la entrega:** seguir la [guía de entrega](docs/guia_entrega.md).
En la computadora del integrante con el Docker original, después de actualizar
y recargar la API, ejecutar `python scripts/verificar_entrega.py`. Recoge evidencia
nueva de código desplegado, conectividad, tests y agregaciones, sin cambiar datos
ni servicios. Sin Docker deja registrada la comprobación como no ejecutada.

Se conservan la API, sus rutas, los seis adaptadores, los tests originales y todas
las evidencias previas. El motor temporal activo es **InfluxDB 3 Core / SQL**.
Esta revisión no crea bases, contenedores, clases ni datos de reemplazo.

- [Comparación del ZIP, requisitos oficiales y validación](docs/integracion_correcciones.md).
- [Trazabilidad, versiones y modelos H4–H9](docs/trazabilidad_hitos_4_9.md).
- Las cifras históricas de 9 tests aprobados y 18 comprobaciones corresponden al
  entorno documentado anteriormente. En esta revisión, los tests originales se
  intentaron ejecutar y fallaron por falta de acceso a la API/Docker. No se
  revalidaron las instancias ni la persistencia.

### Configuración y orden de ejecución

1. Identificar las instancias originales y cotejar sus versiones, modelos y
   montajes con la trazabilidad. No reconstruir el laboratorio para ejecutar H11.
2. Adaptar `config/configuracion-ejemplo.env` en un archivo privado
   `config/hito11_api.env`, excluido de Git. Los nombres de ejemplo son internos
   de Docker; desde Windows deben usarse los hosts y puertos ya publicados.
   `Settings` lee `.env` en el directorio de ejecución o variables del proceso;
   no carga `config/hito11_api.env` automáticamente. El validador acepta
   `--env-file`; las variables del proceso prevalecen sobre el archivo.
3. Actualizar únicamente el código de la API mediante el mecanismo de despliegue
   existente y confirmar el commit efectivamente ejecutado. Ejecutar las pruebas
   desde el contenedor API existente con las variables originales. No instalar
   otro laboratorio ni ejecutar scripts de carga.

```powershell
$revisionHito11 = git rev-parse HEAD
docker exec fixture2030-hito11-api python /app/validar_conectividad.py --mode all --producto todos --origen contenedor-api --revision $revisionHito11 --json
docker exec fixture2030-hito11-api python -m pytest /app/tests/test_integracion_hito11.py -v --tb=short
```

El commit pasado debe coincidir con el código del contenedor; no basta con que sea
el HEAD local. `--api-url` usa el puerto interno 8000 por defecto. Desde Windows,
con las dependencias Python instaladas y los puertos originales accesibles:

```powershell
python api_hito11/validar_conectividad.py --env-file config/hito11_api.env --mode api --api-url http://127.0.0.1:8011 --origen host --json
```

`api` conserva salud y añade una lectura funcional por motor. En `all` se informan
24 resultados; la lectura de salud se comparte entre los seis motores. `--producto`
y los modos `tcp`, `native`, `api` siguen disponibles. El modo nativo carga solo el
driver seleccionado y cierra sus clientes, incluso si falla la prueba.

Los parámetros `--partido`, `--bucket-10m`, `--shard`, `--desde`, `--hasta`,
`--resolucion` y `--sesion` permiten seleccionar casos ya existentes. Los valores
predeterminados proceden de los ejemplos originales y de los tests conservados.
No introducir tokens ni datos personales como identificadores de sesión.

Interpretación de resultados:

- `ok`: la comprobación indicada funcionó; no acredita procedencia ni rendimiento.
- `vacio_valido`: HTTP 200 con contrato válido y cero filas; no prueba existencia
  del dataset original. `ausencia_valida` exige 404 Redis con código
  `recurso_inexistente` y correlación válida; no equivale a Redis caído.
- `error`: comprobación fallida, con categoría y duración; no imprime el mensaje
  privado de la excepción. Los resultados HTTP incluyen request ID válido.
- `skip`: no se ejecutó por falta de herramienta o capacidad; no declara caída.
  Código de salida: 0 sin errores/omisiones, 1 con errores, 2 incompleto/configuración
  inválida. El origen no se presume: indicar `--origen`.

DNS y TCP se distinguen por su categoría de fallo. La resolución DNS depende del
resolver del sistema; el timeout del socket limita la conexión TCP, no garantiza
un límite estricto del resolver. Los pings tampoco prueban permisos completos:
MongoDB verifica el servidor y Neo4j una constante; consultar la ruta funcional
para evaluar el acceso al dominio. Ver pendientes por capa en el informe.

### Pruebas locales sin motores

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r api_hito11/requirements-test.txt
.\.venv\Scripts\python.exe -m pytest api_hito11/tests/unit -q -p no:cacheprovider
```

Estas pruebas usan dobles HTTP en memoria y no escriben en bases. Verifican
contratos, errores, selección de drivers, configuración y construcción SQL;
no sustituyen la suite original contra las seis implementaciones reales.
Las dependencias completas de la API siguen en `api_hito11/requirements.txt`.

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

## Diagnostico de conectividad por capas

El Hito 11 incluye un validador independiente:

api_hito11/validar_conectividad.py

Permite comprobar seis motores mediante cuatro modos:

- tcp: resolucion DNS y conexion al puerto.
- native: comprobacion mediante el adaptador del motor.
- api: consulta HTTP del estado de la dependencia.
- all: ejecuta los tres modos.

### Ejecutar el diagnostico completo

Desde la raiz del repositorio, con los contenedores activos:

    docker exec fixture2030-hito11-api python /app/validar_conectividad.py --mode all --producto todos

### Ejecutar un modo especifico

    docker exec fixture2030-hito11-api python /app/validar_conectividad.py --mode tcp --producto todos

    docker exec fixture2030-hito11-api python /app/validar_conectividad.py --mode native --producto todos

    docker exec fixture2030-hito11-api python /app/validar_conectividad.py --mode api --producto todos

### Evaluar un solo motor

    docker exec fixture2030-hito11-api python /app/validar_conectividad.py --mode all --producto iris

### Resultados verificados

- Seis motores evaluados.
- Dieciocho comprobaciones satisfactorias en modo all.
- Modos individuales verificados.
- Evidencia: docs/evidencia/28_diagnostico_capas_seis_motores.txt

Las comprobaciones se ejecutan dentro del contenedor de la API,
que utiliza la misma red y configuracion de los motores.

El diagnostico native reutiliza los metodos ping de los adaptadores.
No sustituye una auditoria completa de permisos o esquemas.

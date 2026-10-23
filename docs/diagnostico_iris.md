# Diagnóstico de InterSystems IRIS — Hito 11

## Origen

Laboratorio reproducido desde el repositorio original del Hito 9.

## Entorno

- Sistema operativo: Windows con Docker Desktop.
- Producto: InterSystems IRIS Community 2026.2.
- Contenedor: baseDeDatosIIIRIS.
- Namespace: USER.
- Puerto Superserver: 1972.
- Puerto HTTP: 52773.
- Persistencia: directorio local montado en /durable.

## Pruebas exitosas

- Importación y compilación de las cinco clases originales.
- Importación y compilación de los dos scripts originales.
- Creación del partido P001 con dos eventos.
- Consultas SQL de partidos y eventos.
- Navegación mediante objetos.
- Validación de propiedades obligatorias.
- Reinicio del contenedor conservando P001 y sus dos eventos.
- Conectividad TCP desde Windows al puerto 1972.
- Conectividad TCP desde Windows al puerto 52773.

## Resultados observados

Antes del reinicio:
- Partido: P001.
- Eventos: 2.

Después del reinicio:
- Partido: P001.
- Eventos: 2.

TCP:
- Puerto 1972: TcpTestSucceeded = True.
- Puerto 52773: TcpTestSucceeded = True.

## Pendiente

- Conexión desde el adaptador IRIS de FastAPI.
- Prueba HTTP de extremo a extremo mediante la API.
- Persistencia después de recrear el contenedor.

## Limitaciones

El laboratorio fue reproducido desde el código original.
No se restauró el volumen de datos de macOS.

La propiedad Estado continúa siendo modificable directamente.
No están completamente encapsuladas las transiciones de estado,
según la observación del profesor en el Hito 9.

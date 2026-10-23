# Guía de cierre de entrega — Grupo 9

El equipo informa que un integrante probó el estado anterior en su Docker y
funcionó. Se conservan las evidencias originales de esas pruebas. La revisión
nueva debe validarse en ese mismo laboratorio; la falta de Docker en esta
computadora no invalida los resultados históricos ni certifica cambios nuevos.

## Preparación en la computadora con Docker

1. Obtener la rama `correcciones/hito11-conectividad-trazabilidad` del
   [PR #1](https://github.com/Agusmel03/Hito11_Grupo9_Conectividad/pull/1).
2. Actualizar y recargar únicamente el código de la API mediante el despliegue
   existente. Conservar configuración privada, motores, clases, datos y montajes.
   No ejecutar cargas ni crear contenedores de reemplazo.
3. Con la API y los seis motores originales disponibles, ejecutar desde la raíz:

```powershell
python scripts/verificar_entrega.py
```

El comando usa Python estándar en el host y las dependencias ya instaladas en el
contenedor. Si los nombres difieren, utilizar `--contenedor-api`, `--ruta-api` y
`--motores` con los nombres reales. `python scripts/verificar_entrega.py --help`
describe las opciones. No se instala Docker ni se cambian servicios automáticamente.

## Qué hace el comando

- Registra fecha UTC y commit; detecta cambios de código sin commit.
- Lee identidad, imagen y montajes de los contenedores sin volcar variables de
  entorno. Los orígenes de los montajes se guardan como hashes, sin rutas privadas.
- Compara las huellas del código Python y del test original entre el checkout y
  el contenedor; evita atribuir pruebas de código viejo al commit nuevo. El cotejo
  es del código en disco: es necesario recargar la API en el paso 2.
- Ejecuta el diagnóstico completo y los nueve tests originales.
- Verifica salud y versión de InfluxDB 3 Core y compara las cuatro agregaciones
  con cálculos independientes sobre hasta 10000 puntos **existentes**. Evalúa
  1m/5m/15m/1h y ventanas completas/parciales, sin escribir ni generar puntos.
- Guarda un JSON nuevo en `docs/evidencia/validacion_*.json`; no sobrescribe
  evidencias anteriores ni imprime tokens o mensajes privados de los drivers.

`comprobaciones_automaticas_ok` significa que pasó ese conjunto de pruebas, no
que se certificó todo el hito. `no_probado`/`incompleto` conserva las limitaciones;
si falta Docker, se registra esa ausencia y no se inventan resultados.

Para contrastar otro partido/intervalo existente, ejecutar el verificador dentro
de la API con `--partido`, `--desde` y `--hasta`:

```powershell
Get-Content -Raw api_hito11/verificar_agregaciones.py | docker exec -i -w /app fixture2030-hito11-api python - --partido P001 --desde 2030-06-08T19:00:00Z --hasta 2030-06-08T20:00:00Z
```

La comprobación de versión usa GET `/ping`, y la salud usa GET `/health`, con la
autorización privada existente, según la [documentación de Core](https://docs.influxdata.com/influxdb3/core/api/server-information/).
Un 403 en salud/versionado se registra: no justifica ampliar privilegios sin revisar
el contexto. La comparación temporal solo certifica la muestra efectivamente leída.

## Cierre que requiere el laboratorio

- Completar versiones y procedencia en [trazabilidad H4–H9](trazabilidad_hitos_4_9.md).
  Los hashes actuales de montajes no demuestran por sí solos continuidad con H4–H9.
- Completar RF21 en una ventana coordinada: verificar salud inicial, detener
  temporalmente una dependencia original, observar liveness y HTTP 503, volver a
  iniciarla y verificar recuperación. Registrar request ID, tiempo y logs redactados.
  No eliminar contenedores, volúmenes ni datos; el script no ejecuta esta detención.
- Revisar el JSON y los logs, incorporarlos al PR y aprobar su incorporación a
  `main` cuando las pruebas necesarias estén acreditadas.

La evidencia histórica sigue en `docs/evidencia/00_*` a `30_*`; la evidencia 31
corresponde a la primera revisión local. No presentar las pruebas nuevas de código
como ejecutadas en Docker hasta adjuntar su resultado real.

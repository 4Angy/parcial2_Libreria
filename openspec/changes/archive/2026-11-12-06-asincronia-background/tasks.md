# Tasks

## 1. Aviso en segundo plano en ventas

- [x] 1.1 Agregar la función async `avisar_comprobante(cliente_id, venta_id)` en `app/modules/ventas/service.py`, usando `await asyncio.sleep(0.5)` y `logging.getLogger(__name__)`, con `try/except` que loguee errores sin propagarlos. Verificación: importación sin error.
- [x] 1.2 Modificar `crear_venta` en `app/modules/ventas/router.py` para inyectar `BackgroundTasks` y registrar `background_tasks.add_task(service.avisar_comprobante, venta.cliente_id, venta.id)` antes de devolver la respuesta. Verificación: inspección de código.
- [x] 1.3 Verificar que el aviso no recibe sesión ni accede a la base. Verificación: inspección de la firma y del cuerpo de la función.

## 2. Verificación automatizada

- [x] 2.1 Crear o extender un test que registre una venta y afirme que el tiempo de respuesta es menor a `0.5` segundos y que el aviso aparece en el log después de la respuesta. Verificación: el script imprime `ok` y termina con código 0.
- [x] 2.2 Ejecutar `test/consultas.py`, `test/altas_relaciones.py`, `test/carga_anticipada.py` y `test/rutas.py` para confirmar que nada se rompió. Verificación: todos imprimen `ok`.
- [x] 2.3 Verificar manualmente con `uvicorn` que `docker logs` (o la consola) muestra el aviso después de la respuesta del `POST /ventas/`. Verificación: observación del log.

## 3. Cierre del change

- [x] 3.1 Actualizar `docs/ESTADO.md` para reflejar que el Ejercicio 6 queda cubierto. Verificación: revisión del documento.
- [x] 3.2 Archivar el change con `/opsx-archive 06-asincronia-background`. Verificación: el change aparece en `openspec/changes/archive/` y la spec se promueve a `openspec/specs/background-tasks/spec.md`.

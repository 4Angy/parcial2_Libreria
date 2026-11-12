# Tasks

## 1. Auditoría y orden en los modelos

- [ ] 1.1 Repetir la auditoría de las trece lecturas con un evento `before_cursor_execute` sobre la base sembrada (sesión nueva por lectura) y contrastar cada número con la tabla de la decisión 1 de `design.md`; si alguna lectura dependiera de la carga perezosa, corregirla con `joinedload`/`selectinload` y anotar el cambio en `design.md`.
  **Verificación:** las trece lecturas medidas coinciden con la tabla (1, 1, 2, 1, 2, 1, 2, 1, 2, 1, 2, 1, 2) y ninguna emite una consulta por elemento; si no hay hallazgos, el diseño queda como está.

- [ ] 1.2 Agregar `order_by` a `Libro.autorias` en `app/modules/libros/models.py` con `sa_relationship_kwargs={"order_by": "LibroAutor.orden, LibroAutor.autor_id"}`, sin tocar el resto de la relación.
  **Verificación:** `.venv\Scripts\python.exe -c "import asyncio; from app.core.registry import import_model_modules; from app.modules.libros.models import Libro; import_model_modules(); print(Libro.autorias.property.order_by)"` imprime las dos columnas, y una lectura del libro 9 devuelve `[(1, 9), (2, 10)]` con la segunda sentencia terminada en `ORDER BY libro_autor.orden, libro_autor.autor_id`.

- [ ] 1.3 Agregar `order_by` a `Venta.renglones` en `app/modules/ventas/models.py` conservando `cascade: "all, delete-orphan"` y `passive_deletes: True`.
  **Verificación:** `.venv\Scripts\python.exe -c "import asyncio; from app.core.registry import import_model_modules; from app.modules.ventas.models import Venta; import_model_modules(); p = Venta.renglones.property; print(p.cascade, p.passive_deletes, p.order_by)"` muestra la cascada, `True` y `renglon_venta.id`, y la consulta de la colección de una venta termina en `ORDER BY renglon_venta.id`.

## 2. Verificación del conteo fijo

- [ ] 2.1 Crear `test/consultas_n1.py` con el estilo de `test/consultas.py`: prefijo `Prueba 05`, un cliente, un libro con 1 autoría, uno con 5, una venta con 1 renglón y otra con 5, y un `finally` que borra renglones, ventas, autorías, libros y cliente y afirma los conteos `7, 5, 10, 9, 10, 4, 4, 2, 4`.
  **Verificación:** `.venv\Scripts\python.exe test\consultas_n1.py` termina con `ok` y, después de correrlo, `docker exec pg-libreria psql -U libreria -d libreria -c "SELECT (SELECT count(*) FROM libro), (SELECT count(*) FROM venta), (SELECT count(*) FROM cliente);"` devuelve `9 | 2 | 4` sin filas `Prueba 05`.

- [ ] 2.2 Agregar al script las aserciones de conteo: exactamente 2 `SELECT` en cada uno de los cuatro casos, el mismo número con 1 y con 5 hijos, y que la segunda sentencia sea la de la colección (`FROM libro_autor` en el libro, `FROM renglon_venta` en la venta).
  **Verificación:** el script imprime el conteo de los cuatro casos (`libro 1 autor`, `libro 5 autores`, `venta 1 renglón`, `venta 5 renglones`) y falla con `AssertionError` si alguno difiere de 2 o si el número cambia entre 1 y 5 hijos.

- [ ] 2.3 Agregar al script la serialización con la sesión cerrada (`LibroRead` y `VentaRead` con `model_dump(mode="json")`), la afirmación de que el registro de sentencias no crece, y las aserciones de orden y reproducibilidad de `autores` por `orden` y de `renglones` por `id` en dos lecturas consecutivas.
  **Verificación:** `.venv\Scripts\python.exe test\consultas_n1.py` termina con `ok`; la serialización no lanza, no agrega sentencias y las dos listas salen ordenadas en la primera y en la segunda lectura.

## 3. Contrato HTTP de C-07

- [ ] 3.1 Agregar a `test/lecturas.http` los bloques del detalle de un libro con cinco autores: `POST /libros/` con `# captura: libro_c07_id`, `GET /libros/{{libro_c07_id}}` con `# esperado: 200`, `# contiene:` los cinco nombres y `# cantidad: autores=5`.
  **Verificación:** con `uvicorn app.main:app --port 8000` arriba, ejecutar los dos bloques devuelve `201` y `200`, el cuerpo trae cinco autores ordenados por `orden` y el `GET` no muestra campos fuera de `LibroRead`.

- [ ] 3.2 Agregar los bloques del detalle de una venta con cinco renglones: `POST /ventas/` con `# captura: venta_c07_id`, `GET /ventas/{{venta_c07_id}}` con `# esperado: 200`, `# contiene:` los cinco títulos, `# cantidad: renglones=5` y `# termina-en-z: fecha`.
  **Verificación:** los dos bloques devuelven `201` y `200`, el cuerpo trae cinco renglones con `subtotal` calculado y en orden de `id`, y la fecha termina en `Z`.

- [ ] 3.3 Documentar la directiva `# cantidad: campo=n` en el encabezado de `test/lecturas.http` y agregar al final el bloque SQL de limpieza por `libro_c07_id` y `venta_c07_id`.
  **Verificación:** el encabezado explica la directiva; ejecutar el bloque de limpieza deja `libro`, `libro_autor`, `venta` y `renglon_venta` en `9, 10, 2, 4`.

## 4. Regresión y documentación

- [ ] 4.1 Ejecutar la regresión de scripts: `test/consultas.py`, `test/altas_relaciones.py`, `test/rutas.py`, `test/serializacion.py` y `test/errores_integridad.py`.
  **Verificación:** los cinco terminan con código 0 y `test/rutas.py` sigue exigiendo 26 rutas, sin cambios en rutas, DTO ni routers.

- [ ] 4.2 Ejecutar los cinco `.http` de dominio (`contratos`, `paginacion`, `errores`, `lecturas`, `altas`) contra la base sembrada y contrastar cada respuesta con sus comentarios, incluidos los bloques C-07 nuevos.
  **Verificación:** todas las respuestas coinciden con `# esperado:`, `# contiene:`, `# cantidad:`, `# es-null:` y `# termina-en-z:`, y la limpieza final deja los nueve conteos en `7, 5, 10, 9, 10, 4, 4, 2, 4`.

- [ ] 4.3 Capturar la evidencia de `SQL_ECHO=true` para C-07: un `GET /libros/{id}` de un libro con varios autores y un `GET /ventas/{id}` de una venta con varios renglones, con las dos sentencias de cada detalle.
  **Verificación:** la consola muestra dos `SELECT` por detalle —libro con editorial y género + autorías con autores, venta con cliente + renglones con libros— y el extracto queda en el resumen de la implementación; `docs/ESTADO.md` lo actualiza el orquestador y este change no lo edita.

- [ ] 4.4 Confirmar que el diff se limita a los archivos previstos y que no se tocaron `app/main.py`, los routers, los DTO, `lifespan`, `scripts/`, `requirements.txt` ni `Dockerfile`.
  **Verificación:** `git status --short` lista solo `app/modules/libros/models.py`, `app/modules/ventas/models.py`, `test/consultas_n1.py`, `test/lecturas.http` y `openspec/changes/05-lecturas-sin-n1/`; `git diff --stat` no muestra los archivos excluidos.

## Workflow follow-up

- Archivar el change después de la revisión del grupo y promover `eager-loading` a `openspec/specs/eager-loading/spec.md`.
- Actualizar `docs/ESTADO.md` con la fila de C-07 y el extracto de `SQL_ECHO=true` (lo hace el orquestador).

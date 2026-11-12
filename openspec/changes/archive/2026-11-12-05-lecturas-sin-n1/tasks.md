# Tasks

## 1. Contrato de carga en libros

- [x] 1.1 Verificar que `_consulta_libro` en `app/modules/libros/service.py` declara `joinedload(Libro.editorial)`, `joinedload(Libro.genero)` y `selectinload(Libro.autorias).joinedload(LibroAutor.autor)`; confirmar que `obtener_libro` y `_releer_libro` usan `_consulta_libro`. Verificación: inspección de código.
- [x] 1.2 Verificar que `listar_libros` precarga editorial y género con `joinedload` y no carga autorías. Verificación: inspección de código + `SQL_ECHO=true`.
- [x] 1.3 Evaluar agregar `lazy="raise"` a las relaciones de `Libro` y `LibroAutor` en `app/modules/libros/models.py` para impedir carga perezosa; si algún test existente falla, revertir y documentar la razón. Verificación: ejecución de `test/consultas.py` y `test/altas_relaciones.py`.

## 2. Contrato de carga en ventas

- [x] 2.1 Verificar que `_consulta_venta` en `app/modules/ventas/service.py` declara `joinedload(Venta.cliente)` y `selectinload(Venta.renglones).joinedload(RenglonVenta.libro)`. Verificación: inspección de código.
- [x] 2.2 Verificar que `obtener_venta` y `_releer_venta` usan `_consulta_venta`, y que `listar_ventas` no carga relaciones (resumen). Verificación: inspección de código.
- [x] 2.3 Evaluar agregar `lazy="raise"` a las relaciones de `Venta` y `RenglonVenta` en `app/modules/ventas/models.py`. Verificación: ejecución de `test/consultas.py` y `test/altas_relaciones.py`.

## 3. Sublistados y entidades restantes

- [x] 3.1 Verificar carga anticipada en `app/modules/autores/service.py` (`listar_autorias_de_autor`: `joinedload` encadenado a editorial y género), `app/modules/editoriales/service.py` (`listar_libros_de_editorial`) y `app/modules/generos/service.py` (`listar_libros_de_genero`). Verificación: inspección de código.
- [x] 3.2 Verificar que `obtener_cliente` en `app/modules/clientes/service.py` precarga el perfil con `joinedload`, y que `listar_ventas_de_cliente` no serializa relaciones. Verificación: inspección de código.
- [x] 3.3 Evaluar agregar `lazy="raise"` a las relaciones de `Autor`, `Editorial`, `Genero` y `Cliente`/`PerfilCliente`. Verificación: ejecución de la suite de tests.

## 4. Verificación automatizada de cantidad de consultas

- [x] 4.1 Extender `test/consultas.py` (o crear `test/carga_anticipada.py`) para registrar sentencias y afirmar que el detalle de un libro y el detalle de una venta emiten una cantidad fija de `SELECT`, sin consulta por elemento, y que la serialización fuera de sesión no emite consultas nuevas. Verificación: el script imprime `ok` y termina con código 0.
- [x] 4.2 Ejecutar `test/consultas.py`, `test/altas_relaciones.py` y el nuevo caso; todos deben imprimir `ok`. Verificación: salida de consola y código de salida 0.
- [x] 4.3 Ejecutar `test/rutas.py` para confirmar que el inventario de rutas sigue siendo 26 sin cambios. Verificación: salida `faltan set() sobran set()`.

## 5. Cierre del change

- [x] 5.1 Actualizar `docs/ESTADO.md` para reflejar que el Ejercicio 5 queda cubierto y archivado. Verificación: revisión del documento.
- [x] 5.2 Archivar el change con `/opsx-archive 05-lecturas-sin-n1` una vez verificados los tests. Verificación: el change aparece en `openspec/changes/archive/` y la spec se promueve a `openspec/specs/eager-loading/spec.md`.

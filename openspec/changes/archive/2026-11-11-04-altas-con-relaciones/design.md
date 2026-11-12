# Design

## Context

Ver `proposal.md` para la motivación y `specs/` para los requisitos. El estado que condiciona este diseño es el que dejaron los changes `01`, `02` y `03`:

- `app/core/errors.py` ya concentra `ErrorDeDominio`, `NoEncontrado` (404), `Conflicto` (409) y `confirmar(session, mensaje_conflicto)`, que hace `commit()`, `rollback()` ante `IntegrityError` y elige el mensaje por `SQLSTATE`: `23505` usa el mensaje de la operación, `23503` usa «La referencia indicada no existe.», `23514` usa el mensaje de rango y el resto usa un genérico. **Este change lo reutiliza sin modificarlo.**
- `app/core/pagination.py`, `app/core/database.py` y `app/main.py` están cerrados: los siete routers ya se registran y los handlers de `ErrorDeDominio` y `SQLAlchemyError` ya existen. `app/main.py` no se toca.
- `app/modules/libros/schemas.py` tiene `LibroUpdate`, `LibroRead`, `LibroResumenRead` y `LibroAutorRead`; no tiene `LibroCreate`. `app/modules/libros/service.py` tiene `_consulta_libro()` con `joinedload(Libro.editorial)`, `joinedload(Libro.genero)` y `selectinload(Libro.autorias).joinedload(LibroAutor.autor)`, más `_releer_libro()` con `populate_existing=True`, `listar_libros`, `obtener_libro` y `actualizar_libro`.
- `app/modules/ventas/schemas.py` tiene `VentaRead`, `VentaResumenRead` y `RenglonRead`; no tiene `VentaCreate` ni `RenglonCreate`. `app/modules/ventas/service.py` solo tiene `listar_ventas` y `obtener_venta`, y el detalle carga `joinedload(Venta.cliente)` y `selectinload(Venta.renglones).joinedload(RenglonVenta.libro)`.
- Los modelos `Libro`, `LibroAutor`, `Venta` y `RenglonVenta` ya declaran las claves foráneas, los `UNIQUE`, los `CHECK` y las relaciones con `cascade` que este change necesita. No hay cambios de esquema.
- `test/rutas.py` exige hoy que `POST /libros/` y `POST /ventas/` **no** existan; `test/contratos.http` espera `405` en esas dos rutas. Los dos archivos se actualizan en este change.
- PostgreSQL 16.15 en `pg-libreria` (`127.0.0.1:5433`), base sembrada con `editorial=7, genero=5, autor=10, libro=9, libro_autor=10, cliente=4, perfil_cliente=4, venta=2, renglon_venta=4`. Python local 3.14, imagen de entrega `python:3.12-alpine`.
- El `design.md` archivado de `03` fija trece decisiones (DTO separados, `Decimal` como cadena, fecha UTC con `Z`, `PATCH` con `exclude_unset`, `app/core/pagination.py`, `app/core/errors.py`, unicidad sin pre-consulta, capas router/service, carga anticipada, registro de routers en `app/main.py`, transacciones con `expire_on_commit=False`, verificación sin `pytest` y compatibilidad 3.12). Este change las extiende; no las contradice.

**Diferencia entre el ejemplo de la consigna y la semilla real.** El ejemplo de `POST /ventas/` de la consigna espera `id: 2`, total `77000.00`, «Rayuela» a `25000.00` para el libro 1 y «Respiración artificial» a `27000.00` para el libro 4, con el cliente 2 llamado «Tomás Ríos». La base sembrada por `scripts/datos_iniciales.py` tiene libro 1 = «Cien años de soledad» a `24500.00`, libro 4 = «El nombre de la rosa» a `19900.00`, cliente 2 = «Diego Sosa» y ya existen dos ventas (ids 1 y 2). El ejemplo es ilustrativo: este change reproduce la **forma** del cuerpo y la **regla** de cálculo, y las verificaciones calculan los valores esperados a partir de la base real, no de los números literales del ejemplo.

## Goals / Non-Goals

**Goals:**

- Publicar `POST /libros/` y `POST /ventas/` con DTO anidados, códigos `201`/`409`/`422` y la forma de respuesta que la consigna exige.
- Demostrar la diferencia entre asociación y composición: los ids de lo que ya existe se escriben a ciegas y la base rechaza; los datos de la parte viajan y nacen con el todo.
- Copiar el precio del libro y calcular el total en el servidor, sin que el cliente pueda enviarlos ni alterarlos después.
- Mantener el número de consultas fijo y sin carga perezosa en las respuestas de alta.
- Dejar verificaciones ejecutables contra la base real, sin dependencias nuevas.

**Non-Goals:**

- Medir y documentar formalmente la cantidad de consultas como criterio de aceptación (change `05`); acá solo se comprueba que no hay N+1 ni consultas posteriores a la lectura final.
- `BackgroundTasks` (change `06`), contenedor e imagen (changes `07` y `08`).
- Modificar `PATCH /ventas/{id}`: sigue sin existir y responde `405` (RN-08).
- Editar las autorías de un libro existente desde el `PATCH`: `LibroUpdate` no cambia y las autorías solo se declaran en el alta.
- Descontar stock al registrar una venta: ninguna regla de negocio lo pide.
- Cambiar tablas, restricciones, índices, relaciones, `lifespan`, `app/main.py` o `scripts/datos_iniciales.py`.

## Decisions

### 1. Inventario de DTO que se agrega

| Módulo | DTO nuevo | Campos |
|---|---|---|
| `libros` | `LibroAutorCreate` | `autor_id: int`, `rol: Literal["autor", "coautor", "traductor", "ilustrador"]`, `orden: int` (`ge=1`) |
| `libros` | `LibroCreate` | `isbn: str`, `titulo: str`, `precio: Decimal` (`gt=0`), `stock: int` (`ge=0`), `editorial_id: int`, `genero_id: Optional[int] = None`, `autores: list[LibroAutorCreate]` |
| `ventas` | `RenglonCreate` | `libro_id: int`, `cantidad: int` (`gt=0`) |
| `ventas` | `VentaCreate` | `cliente_id: int`, `renglones: list[RenglonCreate]` con `min_length=1` |

- Los cuatro DTO declaran `model_config = ConfigDict(extra="forbid")`, también los anidados: un campo extra dentro de una autoría o de un renglón responde `422`.
- Ningún `Create` declara `id`, y `VentaCreate`/`RenglonCreate` tampoco declaran `precio_unitario`, `subtotal`, `total` ni `fecha`. Esos valores los produce el servidor y el contrato los rechaza si llegan.
- `precio` se tipa `Decimal`, no `float`, por la decisión 2 del `03`: la consigna envía `"21000.00"` y Pydantic lo convierte sin perder la escala.
- `isbn` y `titulo` no llevan `min_length`: el `03` tampoco lo hace en `EditorialCreate` ni en `AutorCreate`, y agregarlo sería una regla que la consigna no pide. La base no tiene un `CHECK` de longitud; un texto vacío es un dato de negocio, no un error de contrato.

**Alternativas descartadas:** reutilizar `LibroUpdate` para el alta (sus campos son opcionales y permitiría crear un libro sin `isbn`); aceptar `precio_unitario` o `total` y descartarlos en el servicio (rompe RN-06 y RN-07 porque el cliente podría influir en el resultado); usar `float` (prohibido por la consigna y fuente de redondeo).

### 2. `autores` puede venir vacía; el campo es obligatorio

`autores` se declara como campo requerido (`autores: list[LibroAutorCreate]`) y **acepta la lista vacía**. La consigna exige al menos un renglón para la venta (RN-05) pero no exige al menos un autor para el libro: un libro puede registrarse sin autorías cargadas y completarse después por otra vía administrativa. Inventar un `422` para la lista vacía sería una regla que la consigna no pide.

Omitir la clave `autores` responde `422` porque el campo forma parte del contrato declarado (`LibroCreate` con `autores` en la tabla de endpoints). Es una decisión de contrato, no una regla de negocio: la diferencia entre «lista vacía» y «campo ausente» queda explícita en el DTO.

**Alternativas descartadas:** `Field(default_factory=list)` (permitiría omitir el campo y haría ambiguo el contrato); `min_length=1` (agregaría un `422` no pedido); aceptar `null` (el modelo no admite `autores` nulo y complicaría el servicio sin beneficio).

### 3. Autorías repetidas: `autor_id` y `orden` se validan en el DTO

`LibroCreate` usa un `model_validator(mode="after")` que rechaza con `422`:

- un `autor_id` repetido: la clave primaria de `libro_autor` es `(libro_id, autor_id)`, así que la base respondería `23505` y `confirmar` usaría el mensaje de la operación («El ISBN ya pertenece a otro libro.»), que sería engañoso;
- un `orden` repetido: el `orden` es la posición de la autoría en la tapa y dos autores no pueden ocupar la misma posición. La base solo exige `orden >= 1`, no unicidad, y el detalle no tendría un criterio estable para ordenar dos filas con el mismo `orden`.

La validación no reemplaza ninguna restricción de la base: agrega una regla de contrato que evita un `409` confuso y una respuesta ambigua. Si el grupo prefiere permitir órdenes repetidos, quitar el segundo chequeo es un cambio local en el DTO.

**Alternativas descartadas:** dejar que la base rechace el `autor_id` repetido (mensaje equivocado por el `23505`); validar solo `autor_id` y ordenar por `(orden, autor_id)` (aceptaría una tapa con dos «primeros» autores); agregar un `UNIQUE (libro_id, orden)` en la base (cambio de esquema que pertenece a `02` y que la consigna no pide).

### 4. Renglones: al menos uno y sin libros repetidos (RN-05)

`VentaCreate.renglones` usa `Field(min_length=1)` y un `model_validator(mode="after")` que detecta un `libro_id` repetido, aunque la `cantidad` sea distinta. Los dos casos responden `422` **antes** de tocar la base, que es lo que exige RN-05: el garante es el DTO, no una restricción.

`cantidad` usa `gt=0`, que reproduce el `CHECK cantidad > 0` en el contrato. Los ids (`cliente_id`, `libro_id`) **no** llevan `gt=0`: un id negativo o inexistente es una referencia que no existe y le corresponde `409`, no `422`; agregar `gt=0` convertiría el mismo hecho en dos códigos distintos según el signo.

**Alternativas descartadas:** confiar en el `CHECK` de la base para `cantidad` (devolvería `409` donde RN-05 pide `422`); agrupar renglones repetidos sumando cantidades (la consigna no lo pide y cambiaría el significado del cuerpo); validar ids con `gt=0` (mezcla validación de contrato con integridad referencial).

### 5. Alta de libro: una transacción y relectura del detalle

`crear_libro(session, datos)`:

```python
libro = Libro(
    isbn=datos.isbn,
    titulo=datos.titulo,
    precio=datos.precio,
    stock=datos.stock,
    editorial_id=datos.editorial_id,
    genero_id=datos.genero_id,
)
libro.autorias = [
    LibroAutor(autor_id=a.autor_id, rol=a.rol, orden=a.orden)
    for a in datos.autores
]
session.add(libro)
await confirmar(session, "El ISBN ya pertenece a otro libro.")
return await _releer_libro(session, libro.id)
```

- `libro.autorias` se asigna sobre un objeto **transitorio**: la colección está vacía y asignarla no dispara ninguna consulta. La relación tiene la cascada por defecto de SQLModel y las filas de `libro_autor` se insertan después del `INSERT` del libro, cuando la base ya generó `libro.id`.
- No se asigna `LibroAutor.autor`: solo viaja `autor_id` y la clave foránea es la que rechaza un autor inexistente. Asignar la relación obligaría a leer el autor antes, que es exactamente lo que C-04 prohíbe.
- `genero_id=None` funciona sin ramas: la columna es opcional y el DTO lo acepta.
- La relectura reutiliza `_releer_libro()`, que arma `_consulta_libro()` y agrega `populate_existing=True`. Sin `populate_existing`, la entidad ya está en el mapa de identidad con la colección `autorias` que acabamos de asignar y `selectinload` no la reemplazaría; con él, la respuesta sale de la base con editorial, género, autorías y autores cargados.
- `confirmar` traduce el ISBN repetido (`23505`) con el mensaje de la operación y cualquier clave foránea (`23503`) con el mensaje genérico de `errors.py`. El servicio no captura `IntegrityError` ni inspecciona restricciones.

**Alternativas descartadas:** `session.refresh(libro)` (recarga columnas pero no relaciones y puede disparar carga perezosa); devolver el objeto recién creado sin releer (las relaciones `editorial`, `genero` y `autor` quedarían sin cargar y la serialización fallaría con `MissingGreenlet`); precargar editorial y género a mano con `session.get` (dos consultas más y duplica la lógica de `_consulta_libro`).

### 6. Alta de venta: leer los libros, copiar el precio y calcular el total

`crear_venta(session, datos)`:

```python
ids = [r.libro_id for r in datos.renglones]
libros = {
    libro.id: libro
    for libro in (
        await session.execute(select(Libro).where(Libro.id.in_(ids)))
    ).scalars().all()
}
if any(i not in libros for i in ids):
    raise Conflicto("El libro indicado no existe.")

renglones = [
    RenglonVenta(
        libro_id=r.libro_id,
        cantidad=r.cantidad,
        precio_unitario=libros[r.libro_id].precio,
    )
    for r in datos.renglones
]
total = sum(
    (r.precio_unitario * r.cantidad for r in renglones), Decimal("0")
).quantize(Decimal("0.01"))
venta = Venta(
    cliente_id=datos.cliente_id,
    fecha=datetime.now(timezone.utc),
    total=total,
)
venta.renglones = renglones
session.add(venta)
await confirmar(session, "La venta no se pudo registrar.")
return await _releer_venta(session, venta.id)
```

- **Una sola consulta para todos los libros** (`IN`), no una por renglón. La consulta es `select(Libro)` sin opciones: solo se necesita `precio` y cargar `autorias` o `renglones` agregaría consultas innecesarias.
- **La lectura es la de RN-06, no una pre-consulta de existencia.** Copiar el precio obliga a leer el libro; que un `libro_id` no aparezca en el resultado es un efecto de esa lectura y se traduce a `409` con un mensaje propio. Es distinto del alta de libro, donde no hay ningún dato que leer del padre y por eso se escribe a ciegas.
- **No se asigna `renglon.libro`.** Asignar la relación inversa haría que SQLAlchemy cargue `libro.renglones` para mantener la colección, lo que emitiría un `SELECT` por libro y podría fallar con `MissingGreenlet`. El renglón se construye con `libro_id` y el detalle se obtiene de la relectura.
- `total` se calcula con `Decimal` y se cuantiza a dos decimales; el `0` inicial es `Decimal("0")` para no mezclar `int` con `Decimal`. Los precios ya tienen dos decimales, así que la cuantización no cambia el valor, pero deja explícita la regla de RN-07.
- `fecha = datetime.now(timezone.utc)` es el instante del servidor; el DTO no la acepta.
- `confirmar` traduce el `cliente_id` inexistente (`23503`) con el mensaje genérico. El mensaje de `23505` («La venta no se pudo registrar.») es un respaldo: `venta` no tiene restricciones de unicidad y el escenario no ocurre en la práctica.
- **Relectura del detalle:** `obtener_venta` se refactoriza para compartir `_consulta_venta()` (la consulta con `joinedload(Venta.cliente)` y `selectinload(Venta.renglones).joinedload(RenglonVenta.libro)`), y se agrega `_releer_venta()` con `populate_existing=True`, igual que `_releer_libro()`. Sin `populate_existing`, la venta recién creada conservaría la colección asignada en memoria y `selectinload` no reemplazaría los renglones; la relectura garantiza que `titulo` y `subtotal` salgan de la base. `GET /ventas/{id}` sigue usando `obtener_venta` y no cambia su contrato.

**Alternativas descartadas:** leer cada libro con `session.get` dentro del bucle (N+1 y lo que `05` debe evitar); confiar en `expire_on_commit=False` y serializar el objeto en memoria (los renglones no tendrían `libro` cargado); `session.refresh(venta)` (no recarga relaciones); aceptar `precio_unitario` del cuerpo (viola RN-06); calcular el total en el cliente (viola RN-07).

### 7. Mensajes de clave foránea: uno propio y genérico

`app/core/errors.py` no se modifica. El `23503` sigue produciendo «La referencia indicada no existe.», que:

- es un mensaje propio, en español y estable;
- no nombra tablas, restricciones, `SQLSTATE` ni incluye la traza (RN-12);
- cubre por igual `editorial_id`, `genero_id`, `autor_id` y `cliente_id`, que es lo que C-04 y C-05 necesitan: `409` con mensaje propio.

La única excepción es el `libro_id` inexistente en una venta, que el servicio detecta en la lectura obligatoria del precio y responde «El libro indicado no existe.»: ahí el mensaje específico no cuesta ninguna consulta extra y describe con precisión qué falta.

Distinguir por tabla en el `23503` exigiría leer el nombre de la restricción (frágil, generado por `create_all`) o agregar un parámetro a `confirmar` (modificar el módulo compartido que este change debe reutilizar). El código HTTP y la ausencia de texto interno son los que evalúa la consigna; el texto exacto puede especializarse más adelante sin cambiar el contrato.

**Alternativas descartadas:** parsear `exc.orig.diag.constraint_name` para elegir «La editorial indicada no existe.» (acopla el mensaje a nombres generados y puede confundir dos reglas); capturar `IntegrityError` en el servicio (duplica la traducción centralizada); agregar un parámetro opcional a `confirmar` (cambio del módulo compartido fuera del alcance).

### 8. Fecha, importes y serialización

No se agregan serializadores: `VentaRead` y `RenglonRead` ya publican `fecha` en UTC con `Z`, `total`, `precio_unitario` y `subtotal` como cadenas decimales y `cantidad` como entero. El alta solo tiene que producir valores correctos:

- `fecha` con zona horaria (`datetime.now(timezone.utc)`), para que el `field_serializer` no tenga que asumir UTC;
- `total` como `Decimal` cuantizado a dos decimales;
- `precio_unitario` como el `Decimal` que devuelve `NUMERIC(10,2)`.

**Alternativas descartadas:** serializar la fecha con `datetime.utcnow()` (naive y prohibido por el `03`); devolver `float` en el total (rompe la invariante de importes).

### 9. Routers: dos altas y ningún otro cambio

- `app/modules/libros/router.py` agrega `@router.post("/", response_model=LibroRead, status_code=201, summary="Crear un libro")`, que recibe `LibroCreate` y delega en `service.crear_libro`.
- `app/modules/ventas/router.py` agrega `@router.post("/", response_model=VentaRead, status_code=201, summary="Registrar una venta")`, que recibe `VentaCreate` y delega en `service.crear_venta`.
- `app/main.py` no se toca: los dos routers ya están registrados. Tampoco se toca el `lifespan` ni los handlers.
- `PATCH /ventas/{id}` sigue sin declararse; como el path existe con `GET`, FastAPI responde `405` (RN-08).
- Los routers no capturan `IntegrityError` ni construyen cuerpos de error: el `422` lo produce FastAPI y el `409` viaja como `Conflicto` hasta el handler existente.

**Alternativas descartadas:** un router nuevo para las altas (rompe la estructura por módulo); `status_code=200` (la consigna exige `201`); registrar las rutas en `main.py` (ya lo hace cada router con su `prefix`).

### 10. Verificación: qué se actualiza y qué se agrega

| Archivo | Cambio |
|---|---|
| `test/rutas.py` | Pasa de 24 a 26 rutas: agrega `("post", "/libros/")` y `("post", "/ventas/")` a las requeridas y las quita de las ausentes. Sigue exigiendo que no haya `PATCH /ventas/{id}`, `PATCH /generos/{id}`, `GET /autores/`, `PUT` ni `DELETE`. |
| `test/contratos.http` | Reemplaza el bloque que esperaba `405` en `POST /libros/` por un alta real con autorías y un ISBN repetido (`409`), y el bloque que esperaba `405` en `POST /ventas/` por una venta válida con dos renglones (`201`). Conserva el `405` de `PATCH /ventas/{id}`. |
| `test/errores.http` | Agrega C-04 (editorial inexistente y autor inexistente) y C-05 (cliente inexistente y libro inexistente), con `# esperado: 409`, mensaje propio y `# no-contiene: 23503; _key; Traceback`. |
| `test/altas.http` | Nuevo. Contiene los cuerpos literales de la consigna para las dos altas y la matriz de `422`: `precio=0`, `stock=-1`, `rol` inválido, `orden=0`, `id` en el cuerpo, `renglones: []`, `libro_id` repetido, `cantidad=0` y `total`/`precio_unitario` en el cuerpo. |
| `test/altas_relaciones.py` | Nuevo script ejecutable. Registra las sentencias con `before_cursor_execute`, llama a `crear_venta` contra la base real, comprueba que `total` es la suma de `cantidad * libro.precio`, que cada `precio_unitario` coincide con el precio del libro, que cambiar el precio del libro después no altera la venta (restaura el precio en `finally`) y que no hay un `SELECT` por renglón ni consultas después de la lectura final. Limpia sus filas con el prefijo `Prueba 04`. |
| `test/serializacion.py` | Se amplía con las validaciones de `LibroCreate`, `LibroAutorCreate`, `VentaCreate` y `RenglonCreate`, sin tocar la base. |

Los `.http` siguen la convención del `03`: `# esperado:`, `# captura:`, `# contiene:`, `# no-contiene:`, `# es-null:`, `# termina-en-z:`. Los datos de prueba usan el prefijo `Prueba 04` y cada archivo documenta el bloque SQL de limpieza. La venta de `test/contratos.http` usa un cliente `Prueba 04` para que la limpieza sea determinista; la de `test/altas.http` usa el `cliente_id: 2` de la consigna y se limpia por el `id` capturado. Las filas se borran en orden inverso de dependencias porque el change no expone `DELETE`.

**Alternativas descartadas:** `pytest` (dependencia nueva); `TestClient` para la verificación de consultas (no refleja el ciclo de vida real de la sesión); un `.http` nuevo por cada caso (fragmenta la lectura).

### 11. Compatibilidad con Python 3.12

Se usan `typing.Literal`, `typing.Optional`, `list[...]`, `datetime.timezone.utc`, `decimal.Decimal` y `pydantic.model_validator`. No se usan alias `type`, genéricos PEP 695, `Self`, `StrEnum`, `datetime.UTC` ni sintaxis de 3.13/3.14. Los DTO se evalúan en tiempo de definición; no dependen de anotaciones diferidas.

**Alternativas descartadas:** aprovechar características de 3.14 del entorno local (la imagen de entrega es 3.12).

## Risks / Trade-offs

- **Mensaje único para todas las claves foráneas.** `POST /libros/` con editorial inexistente y con autor inexistente devuelven el mismo texto. → Cumple C-04 (`409` con mensaje propio) y RN-12, y evita tocar `errors.py`; si el corrector pide un mensaje por recurso, se especializa en `confirmar` sin cambiar los códigos ni los tests.
- **`orden` repetido responde `422` aunque la base lo permita.** → Es una regla de contrato derivada del significado de `orden`; quitarla es un cambio local en `LibroCreate`. No afecta ningún caso de la consigna.
- **Omitir `autores` responde `422`.** → El campo es parte del contrato declarado; la lista vacía sí se acepta. Si el corrector envía el alta sin la clave, se cambia a `default_factory=list` en una línea.
- **La relectura agrega dos `SELECT` al alta de venta y dos al alta de libro.** → Es un número fijo, no depende de la cantidad de renglones ni de autores, y evita la carga perezosa. `05` medirá ese número y podrá recortarlo si hace falta.
- **`populate_existing=True` reemplaza el estado en memoria.** → Es lo que se busca: la respuesta sale de la base y no de objetos parcialmente armados. No cambia el contrato de `GET`.
- **El ejemplo de la consigna no coincide con la semilla.** → Las verificaciones calculan el total desde `libro.precio` en la base (con la semilla actual, libros 1 y 4 dan `68900.00`, no `77000.00`) y comprueban la forma del cuerpo, no los números literales.
- **Las pruebas escriben filas.** → Prefijo `Prueba 04`, bloque SQL de limpieza documentado y verificación final de los conteos sembrados. Los cambios de precio se restauran en `finally`.
- **Huecos en las secuencias.** Un alta que termina en `409` consume un `id`. → Ninguna verificación asume ids contiguos; se usan los ids devueltos por la API.
- **`expire_on_commit=False` deja relaciones viejas.** → Las dos altas releen con `populate_existing=True` antes de responder.
- **El `422` de Pydantic incluye el mensaje del validador.** → El texto es propio y en español; no contiene SQL, nombres de tablas ni trazas.

## Migration Plan

No hay cambios de esquema ni migraciones. Para aplicar y verificar:

1. Arrancar `pg-libreria` (`docker start pg-libreria`) y confirmar los conteos sembrados.
2. Arrancar `uvicorn app.main:app --port 8000` con el `.env` del proyecto.
3. Ejecutar `test/contratos.http`, `test/altas.http` y `test/errores.http` contrastando cada respuesta con su comentario.
4. Ejecutar `.venv\Scripts\python.exe test\serializacion.py`, `.venv\Scripts\python.exe test\altas_relaciones.py` y `.venv\Scripts\python.exe test\rutas.py`.
5. Repetir el alta de venta con `SQL_ECHO=true` y comprobar en la consola el número fijo de sentencias.
6. Ejecutar el bloque de limpieza y comprobar que la base vuelve a `7, 5, 10, 9, 4, 4, 2, 4`.

Rollback: revertir el commit de implementación deja los `schemas.py`, `service.py` y `router.py` sin las altas y `test/rutas.py` vuelve a exigir las ausencias. La base no cambia; las filas creadas por las pruebas se eliminan con el bloque SQL documentado.

## Open Questions

- Si el corrector espera un mensaje de `409` distinto por cada referencia (`editorial`, `género`, `autor`, `cliente`), el cambio es local en `confirmar` y no afecta los códigos ni la forma de los cuerpos.
- Si el corrector espera que la respuesta del alta de libro repita `autor_id` en lugar de anidar `autor`, se ajusta `LibroAutorRead`; hoy se reutiliza el detalle del `03`, que publica `autor`, `rol` y `orden`.
- La consigna no pide descontar stock al vender. Si la revisión del grupo lo considera parte del registro de una venta, se agrega como una regla nueva con su propio change.

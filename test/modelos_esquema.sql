-- ============================================================================
-- test/modelos_esquema.sql
-- Verificación de solo lectura del esquema del change 02-modelos-relaciones.
--
-- Ejecución:
--   Get-Content test\modelos_esquema.sql | docker exec -i pg-libreria psql -U libreria -d libreria
--
-- Requiere que las nueve tablas del dominio existan (las crea el arranque de
-- la aplicación o scripts/datos_iniciales.py). No escribe datos.
-- ============================================================================

\echo '== 1. Las nueve tablas del dominio =='
-- Esperado: 9 filas con editorial, genero, autor, libro, libro_autor,
-- cliente, perfil_cliente, venta y renglon_venta.
SELECT table_name
FROM information_schema.tables
WHERE table_schema = 'public'
  AND table_name IN (
      'editorial', 'genero', 'autor', 'libro', 'libro_autor',
      'cliente', 'perfil_cliente', 'venta', 'renglon_venta'
  )
ORDER BY table_name;

\echo '== 2. Columnas, tipos y nulabilidad =='
-- Esperado (35 filas):
--   editorial      : id integer NO, nombre varchar NO, pais varchar YES
--   genero         : id integer NO, nombre varchar NO
--   autor          : id integer NO, nombre varchar NO, nacionalidad varchar YES
--   libro          : id integer NO, isbn varchar NO, titulo varchar NO,
--                    precio numeric(10,2) NO, stock integer NO,
--                    editorial_id integer NO, genero_id integer YES
--   libro_autor    : libro_id integer NO, autor_id integer NO,
--                    rol varchar NO, orden integer NO (sin columna id propia)
--   cliente        : id integer NO, nombre varchar NO, email varchar NO
--   perfil_cliente : id integer NO, cliente_id integer NO,
--                    telefono varchar YES, direccion varchar YES
--   venta          : id integer NO, cliente_id integer NO,
--                    fecha timestamp with time zone NO, total numeric(12,2) NO
--   renglon_venta  : id integer NO, venta_id integer NO, libro_id integer NO,
--                    cantidad integer NO, precio_unitario numeric(10,2) NO
SELECT table_name,
       column_name,
       data_type,
       numeric_precision,
       numeric_scale,
       is_nullable
FROM information_schema.columns
WHERE table_schema = 'public'
  AND table_name IN (
      'editorial', 'genero', 'autor', 'libro', 'libro_autor',
      'cliente', 'perfil_cliente', 'venta', 'renglon_venta'
  )
ORDER BY table_name, ordinal_position;

\echo '== 3. Claves primarias =='
-- Esperado: una clave primaria por tabla; la de libro_autor es compuesta
-- (libro_id, autor_id) y el resto es (id).
SELECT c.relname AS tabla,
       con.conname AS restriccion,
       pg_get_constraintdef(con.oid) AS definicion
FROM pg_constraint AS con
JOIN pg_class AS c ON c.oid = con.conrelid
JOIN pg_namespace AS n ON n.oid = c.relnamespace
WHERE n.nspname = 'public'
  AND c.relname IN (
      'editorial', 'genero', 'autor', 'libro', 'libro_autor',
      'cliente', 'perfil_cliente', 'venta', 'renglon_venta'
  )
  AND con.contype = 'p'
ORDER BY c.relname;

\echo '== 4. Restricciones UNIQUE y CHECK =='
-- Esperado (12 filas):
--   cliente        : cliente_email_key (u, email)
--   editorial      : editorial_nombre_key (u, nombre)
--   genero         : genero_nombre_key (u, nombre)
--   libro          : ck_libro_precio_positivo (c, precio > 0)
--                    ck_libro_stock_no_negativo (c, stock >= 0)
--                    libro_isbn_key (u, isbn)
--   libro_autor    : ck_libro_autor_orden_positivo (c, orden >= 1)
--                    ck_libro_autor_rol_valido (c, rol IN (...))
--   perfil_cliente : perfil_cliente_cliente_id_key (u, cliente_id)
--   renglon_venta  : ck_renglon_venta_cantidad_positiva (c, cantidad > 0)
--                    ck_renglon_venta_precio_positivo (c, precio_unitario > 0)
--   venta          : ck_venta_total_no_negativo (c, total >= 0)
SELECT c.relname AS tabla,
       con.conname AS restriccion,
       con.contype AS tipo,
       pg_get_constraintdef(con.oid) AS definicion
FROM pg_constraint AS con
JOIN pg_class AS c ON c.oid = con.conrelid
JOIN pg_namespace AS n ON n.oid = c.relnamespace
WHERE n.nspname = 'public'
  AND c.relname IN (
      'editorial', 'genero', 'autor', 'libro', 'libro_autor',
      'cliente', 'perfil_cliente', 'venta', 'renglon_venta'
  )
  AND con.contype IN ('u', 'c')
ORDER BY c.relname, con.contype, con.conname;

\echo '== 5. Indices de las tablas del dominio =='
-- Esperado (20 filas): claves primarias y unicidades de todas las tablas, más
--   ix_libro_editorial_id, ix_libro_genero_id, ix_libro_autor_autor_id,
--   ix_venta_cliente_id, ix_renglon_venta_venta_id, ix_renglon_venta_libro_id.
-- No debe aparecer un índice simple duplicado sobre perfil_cliente.cliente_id
-- (lo cubre perfil_cliente_cliente_id_key) ni sobre libro_autor.libro_id
-- (lo cubre libro_autor_pkey).
SELECT tablename, indexname, indexdef
FROM pg_indexes
WHERE schemaname = 'public'
  AND tablename IN (
      'editorial', 'genero', 'autor', 'libro', 'libro_autor',
      'cliente', 'perfil_cliente', 'venta', 'renglon_venta'
  )
ORDER BY tablename, indexname;

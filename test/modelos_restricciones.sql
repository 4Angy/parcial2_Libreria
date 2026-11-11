-- ============================================================================
-- test/modelos_restricciones.sql
-- Verificación de las restricciones del change 02-modelos-relaciones.
--
-- Ejecución:
--   Get-Content test\modelos_restricciones.sql | docker exec -i pg-libreria psql -U libreria -d libreria
--
-- Requiere la base sembrada por scripts/datos_iniciales.py: los casos usan
-- filas existentes para provocar duplicados y claves foráneas válidas.
-- Cada caso corre en su propia transacción y termina con ROLLBACK, así que la
-- base queda con los mismos datos que antes de ejecutar el archivo.
-- `VERBOSITY sqlstate` muestra el SQLSTATE esperado en cada error.
-- ============================================================================

\set VERBOSITY sqlstate

\echo '== 1. Unicidad (esperado 23505 en cada caso) =='

\echo '-- 1.1 ISBN repetido'
BEGIN;
INSERT INTO libro (isbn, titulo, precio, stock, editorial_id)
VALUES (
    (SELECT isbn FROM libro ORDER BY id LIMIT 1),
    'Duplicado de ISBN',
    1000.00,
    1,
    (SELECT id FROM editorial ORDER BY id LIMIT 1)
);
ROLLBACK;

\echo '-- 1.2 Nombre de editorial repetido'
BEGIN;
INSERT INTO editorial (nombre)
VALUES ((SELECT nombre FROM editorial ORDER BY id LIMIT 1));
ROLLBACK;

\echo '-- 1.3 Email de cliente repetido'
BEGIN;
INSERT INTO cliente (nombre, email)
VALUES ('Cliente Duplicado', (SELECT email FROM cliente ORDER BY id LIMIT 1));
ROLLBACK;

\echo '-- 1.4 Segundo perfil para el mismo cliente'
BEGIN;
INSERT INTO perfil_cliente (cliente_id)
VALUES ((SELECT cliente_id FROM perfil_cliente ORDER BY id LIMIT 1));
ROLLBACK;

\echo '== 2. CHECK (esperado 23514 en cada caso) =='

\echo '-- 2.1 Libro con precio = 0'
BEGIN;
INSERT INTO libro (isbn, titulo, precio, stock, editorial_id)
VALUES ('0000000000001', 'Precio inválido', 0.00, 1,
        (SELECT id FROM editorial ORDER BY id LIMIT 1));
ROLLBACK;

\echo '-- 2.2 Libro con stock = -1'
BEGIN;
INSERT INTO libro (isbn, titulo, precio, stock, editorial_id)
VALUES ('0000000000002', 'Stock inválido', 100.00, -1,
        (SELECT id FROM editorial ORDER BY id LIMIT 1));
ROLLBACK;

\echo '-- 2.3 Autoria con rol = prologuista'
BEGIN;
INSERT INTO libro_autor (libro_id, autor_id, rol, orden)
VALUES (
    (SELECT id FROM libro ORDER BY id LIMIT 1),
    (SELECT a.id FROM autor AS a
     WHERE NOT EXISTS (
         SELECT 1 FROM libro_autor AS la
         WHERE la.libro_id = (SELECT id FROM libro ORDER BY id LIMIT 1)
           AND la.autor_id = a.id
     )
     ORDER BY a.id LIMIT 1),
    'prologuista',
    1
);
ROLLBACK;

\echo '-- 2.4 Autoria con orden = 0'
BEGIN;
INSERT INTO libro_autor (libro_id, autor_id, rol, orden)
VALUES (
    (SELECT id FROM libro ORDER BY id LIMIT 1),
    (SELECT a.id FROM autor AS a
     WHERE NOT EXISTS (
         SELECT 1 FROM libro_autor AS la
         WHERE la.libro_id = (SELECT id FROM libro ORDER BY id LIMIT 1)
           AND la.autor_id = a.id
     )
     ORDER BY a.id LIMIT 1),
    'autor',
    0
);
ROLLBACK;

\echo '-- 2.5 Venta con total = -1'
BEGIN;
INSERT INTO venta (cliente_id, fecha, total)
VALUES (
    (SELECT id FROM cliente ORDER BY id LIMIT 1),
    '2026-01-01T00:00:00-03:00',
    -1.00
);
ROLLBACK;

\echo '-- 2.6 Renglon con cantidad = 0'
BEGIN;
INSERT INTO renglon_venta (venta_id, libro_id, cantidad, precio_unitario)
VALUES (
    (SELECT id FROM venta ORDER BY id LIMIT 1),
    (SELECT id FROM libro ORDER BY id LIMIT 1),
    0,
    100.00
);
ROLLBACK;

\echo '-- 2.7 Renglon con precio_unitario = 0'
BEGIN;
INSERT INTO renglon_venta (venta_id, libro_id, cantidad, precio_unitario)
VALUES (
    (SELECT id FROM venta ORDER BY id LIMIT 1),
    (SELECT id FROM libro ORDER BY id LIMIT 1),
    1,
    0.00
);
ROLLBACK;

\echo '== 3. Claves foraneas (esperado 23503 en cada caso) =='

\echo '-- 3.1 Renglon con venta_id inexistente'
BEGIN;
INSERT INTO renglon_venta (venta_id, libro_id, cantidad, precio_unitario)
VALUES (999999, (SELECT id FROM libro ORDER BY id LIMIT 1), 1, 100.00);
ROLLBACK;

\echo '-- 3.2 Renglon con libro_id inexistente'
BEGIN;
INSERT INTO renglon_venta (venta_id, libro_id, cantidad, precio_unitario)
VALUES ((SELECT id FROM venta ORDER BY id LIMIT 1), 999999, 1, 100.00);
ROLLBACK;

\echo '-- 3.3 Libro con editorial_id inexistente'
BEGIN;
INSERT INTO libro (isbn, titulo, precio, stock, editorial_id)
VALUES ('0000000000003', 'Editorial inexistente', 100.00, 1, 999999);
ROLLBACK;

\echo '-- 3.4 Libro con genero_id inexistente'
BEGIN;
INSERT INTO libro (isbn, titulo, precio, stock, editorial_id, genero_id)
VALUES ('0000000000004', 'Género inexistente', 100.00, 1,
        (SELECT id FROM editorial ORDER BY id LIMIT 1), 999999);
ROLLBACK;

\echo '-- 3.5 Perfil con cliente_id inexistente'
BEGIN;
INSERT INTO perfil_cliente (cliente_id) VALUES (999999);
ROLLBACK;

\echo '-- 3.6 Venta con cliente_id inexistente'
BEGIN;
INSERT INTO venta (cliente_id, fecha, total)
VALUES (999999, '2026-01-01T00:00:00-03:00', 0.00);
ROLLBACK;

\echo '-- 3.7 Autoria con libro_id inexistente'
BEGIN;
INSERT INTO libro_autor (libro_id, autor_id, rol, orden)
VALUES (999999, (SELECT id FROM autor ORDER BY id LIMIT 1), 'autor', 1);
ROLLBACK;

\echo '-- 3.8 Autoria con autor_id inexistente'
BEGIN;
INSERT INTO libro_autor (libro_id, autor_id, rol, orden)
VALUES ((SELECT id FROM libro ORDER BY id LIMIT 1), 999999, 'autor', 1);
ROLLBACK;

\echo '== 4. Cascada de renglones (esperado 2 -> 0 -> 2) =='
-- Se elige la venta con más renglones, se borra dentro de la transacción y se
-- comprueba que la base eliminó sus renglones sin tocar los de otras ventas.
-- El ROLLBACK restituye el estado inicial.
BEGIN;
SELECT venta_id AS vid
FROM renglon_venta
GROUP BY venta_id
ORDER BY count(*) DESC, venta_id
LIMIT 1 \gset
SELECT count(*) AS antes FROM renglon_venta WHERE venta_id = :vid \gset
SELECT count(*) AS otras_antes FROM renglon_venta WHERE venta_id <> :vid \gset
DELETE FROM venta WHERE id = :vid;
SELECT count(*) AS despues FROM renglon_venta WHERE venta_id = :vid \gset
SELECT count(*) AS otras_despues FROM renglon_venta WHERE venta_id <> :vid \gset
ROLLBACK;
SELECT count(*) AS tras_rollback FROM renglon_venta WHERE venta_id = :vid \gset
SELECT :antes AS antes,
       :despues AS despues,
       :otras_antes AS otras_antes,
       :otras_despues AS otras_despues,
       :tras_rollback AS tras_rollback;

\echo '== 5. Indices de las claves foraneas =='
-- Esperado: un índice para cada columna de clave foránea y ninguno simple
-- duplicado sobre perfil_cliente.cliente_id (lo cubre su UNIQUE) ni sobre
-- libro_autor.libro_id (lo cubre la clave primaria compuesta).
SELECT tablename, indexname, indexdef
FROM pg_indexes
WHERE schemaname = 'public'
  AND tablename IN ('libro', 'libro_autor', 'perfil_cliente', 'venta', 'renglon_venta')
ORDER BY tablename, indexname;

\echo '== 6. Conteos finales (sin cambios respecto de la semilla) =='
SELECT (SELECT count(*) FROM editorial) AS editoriales,
       (SELECT count(*) FROM genero) AS generos,
       (SELECT count(*) FROM autor) AS autores,
       (SELECT count(*) FROM libro) AS libros,
       (SELECT count(*) FROM libro_autor) AS autorias,
       (SELECT count(*) FROM cliente) AS clientes,
       (SELECT count(*) FROM perfil_cliente) AS perfiles,
       (SELECT count(*) FROM venta) AS ventas,
       (SELECT count(*) FROM renglon_venta) AS renglones;

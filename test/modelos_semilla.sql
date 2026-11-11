-- ============================================================================
-- test/modelos_semilla.sql
-- Verificación de contenido de la semilla cargada por scripts/datos_iniciales.py.
--
-- Ejecución:
--   Get-Content test\modelos_semilla.sql | docker exec -i pg-libreria psql -U libreria -d libreria
--
-- Es de solo lectura, salvo el bloque de precio histórico, que actualiza un
-- libro dentro de una transacción y hace ROLLBACK para no alterar la base.
-- ============================================================================

\echo '== 1. Cantidades por tabla =='
-- Esperado: 7 editoriales, 5 generos, 10 autores, 9 libros, 10 autorias,
-- 4 clientes, 4 perfiles, 2 ventas y 4 renglones.
SELECT (SELECT count(*) FROM editorial) AS editoriales,
       (SELECT count(*) FROM genero) AS generos,
       (SELECT count(*) FROM autor) AS autores,
       (SELECT count(*) FROM libro) AS libros,
       (SELECT count(*) FROM libro_autor) AS autorias,
       (SELECT count(*) FROM cliente) AS clientes,
       (SELECT count(*) FROM perfil_cliente) AS perfiles,
       (SELECT count(*) FROM venta) AS ventas,
       (SELECT count(*) FROM renglon_venta) AS renglones;

\echo '== 2. Catalogo traducido =='
-- Esperado: los nueve libros de la semilla con su ISBN y su precio original;
-- "Veinte poemas de amor" queda sin genero.
SELECT l.titulo, l.isbn, l.precio, l.stock, g.nombre AS genero, e.nombre AS editorial
FROM libro AS l
JOIN editorial AS e ON e.id = l.editorial_id
LEFT JOIN genero AS g ON g.id = l.genero_id
ORDER BY l.id;

\echo '== 3. Total de cada venta recalculado desde sus renglones =='
-- Esperado: dos ventas con coincide = true (53700.00 y 89900.00).
SELECT v.id,
       v.total,
       sum(r.cantidad * r.precio_unitario) AS calculado,
       (v.total = sum(r.cantidad * r.precio_unitario)) AS coincide
FROM venta AS v
JOIN renglon_venta AS r ON r.venta_id = v.id
GROUP BY v.id, v.total
ORDER BY v.id;

\echo '== 4. Precio unitario historico del renglon =='
-- Se cambia el precio del libro dentro de una transaccion: el renglon debe
-- conservar el precio unitario con el que se vendio. El ROLLBACK restituye el
-- precio del catalogo.
BEGIN;
SELECT libro_id AS libro_vendido, precio_unitario AS precio_historico
FROM renglon_venta
ORDER BY id
LIMIT 1 \gset
SELECT precio AS precio_catalogo FROM libro WHERE id = :libro_vendido \gset
UPDATE libro SET precio = precio + 1000 WHERE id = :libro_vendido;
SELECT (precio_unitario = :precio_historico) AS conserva_precio
FROM renglon_venta
WHERE libro_id = :libro_vendido;
ROLLBACK;
SELECT (precio = :precio_catalogo) AS precio_restituido
FROM libro
WHERE id = :libro_vendido;

\echo '== 5. Un perfil por cliente =='
-- Esperado: cuatro clientes, cada uno con exactamente un perfil.
SELECT c.id, c.email, count(p.id) AS perfiles, (count(p.id) = 1) AS exactamente_uno
FROM cliente AS c
LEFT JOIN perfil_cliente AS p ON p.cliente_id = c.id
GROUP BY c.id, c.email
ORDER BY c.id;

\echo '== 6. Rol y orden de las autorias =='
-- Esperado: los nueve libros tienen un primer autor con rol = autor y orden = 1.
SELECT l.titulo, a.nombre AS autor, la.rol, la.orden
FROM libro AS l
JOIN libro_autor AS la ON la.libro_id = l.id AND la.orden = 1
JOIN autor AS a ON a.id = la.autor_id
ORDER BY l.id;

\echo '-- 6.1 Freakonomics tiene coautor con orden = 2'
-- Esperado: Steven Levitt como autor (1) y Stephen Dubner como coautor (2).
SELECT l.titulo, a.nombre AS autor, la.rol, la.orden
FROM libro AS l
JOIN libro_autor AS la ON la.libro_id = l.id
JOIN autor AS a ON a.id = la.autor_id
WHERE l.titulo = 'Freakonomics'
ORDER BY la.orden;

\echo '== 7. Libro sin genero =='
-- Esperado: "Veinte poemas de amor" con genero_id nulo.
SELECT titulo, genero_id
FROM libro
WHERE titulo = 'Veinte poemas de amor';

\echo '== 8. Fechas de venta con zona horaria =='
-- Esperado: venta.fecha es timestamp with time zone y los instantes de la
-- semilla (00:00 de Argentina) se guardan como 03:00 UTC.
SELECT column_name, data_type
FROM information_schema.columns
WHERE table_schema = 'public'
  AND table_name = 'venta'
  AND column_name = 'fecha';

SELECT id, fecha, fecha AT TIME ZONE 'UTC' AS en_utc
FROM venta
ORDER BY id;

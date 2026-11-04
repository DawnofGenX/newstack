-- Deterministic sample data: same rows every time, so the tests can assert
-- exact numbers. Delete in child-to-parent order so the cascades stay honest.
PRAGMA foreign_keys = ON;

DELETE FROM order_items;
DELETE FROM orders;
DELETE FROM customers;

INSERT INTO customers (id, name, country) VALUES
    (1, 'Asha', 'IN'),
    (2, 'Bruno', 'DE'),
    (3, 'Chen', 'US'),
    (4, 'Dana', 'IN');

INSERT INTO orders (id, customer_id, placed_on) VALUES
    (10, 1, '2026-01-04'),
    (11, 1, '2026-02-11'),
    (12, 2, '2026-02-12'),
    (13, 3, '2026-03-01'),
    (14, 2, '2026-03-15');

INSERT INTO order_items (order_id, sku, quantity, unit_price_cents) VALUES
    (10, 'TEA-1',  2,  450),
    (10, 'MUG-7',  1, 1200),
    (11, 'TEA-1',  5,  450),
    (12, 'POT-3',  1, 3900),
    (13, 'TEA-1',  1,  450),
    (13, 'POT-3',  2, 3900),
    (14, 'MUG-7',  4, 1200);

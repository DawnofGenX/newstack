-- Everything a report needs, expressed once. The queries below are then a
-- single SELECT each, which keeps the numbers in one place.
PRAGMA foreign_keys = ON;

DROP VIEW IF EXISTS order_totals;
CREATE VIEW order_totals AS
    SELECT o.id                        AS order_id,
           o.customer_id               AS customer_id,
           o.placed_on                 AS placed_on,
           SUM(i.quantity * i.unit_price_cents) AS cents
      FROM orders o
      JOIN order_items i ON i.order_id = o.id
     GROUP BY o.id;

DROP VIEW IF EXISTS customer_revenue;
CREATE VIEW customer_revenue AS
    SELECT c.id                       AS customer_id,
           c.name                     AS name,
           c.country                  AS country,
           COUNT(t.order_id)          AS placed,
           COALESCE(SUM(t.cents), 0)  AS cents
      FROM customers c
      LEFT JOIN order_totals t ON t.customer_id = c.id
     GROUP BY c.id;

-- The tables. Constraints live here, not in the application, so a bad row is
-- refused by SQLite itself.
PRAGMA foreign_keys = ON;

CREATE TABLE customers (
    id      INTEGER PRIMARY KEY,
    name    TEXT NOT NULL,
    country TEXT NOT NULL CHECK (country IN ('IN', 'US', 'DE'))
);

CREATE TABLE orders (
    id          INTEGER PRIMARY KEY,
    customer_id INTEGER NOT NULL REFERENCES customers (id) ON DELETE CASCADE,
    placed_on   TEXT NOT NULL CHECK (placed_on GLOB '[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]')
);

CREATE TABLE order_items (
    order_id         INTEGER NOT NULL REFERENCES orders (id) ON DELETE CASCADE,
    sku              TEXT NOT NULL,
    quantity         INTEGER NOT NULL CHECK (quantity > 0),
    unit_price_cents INTEGER NOT NULL CHECK (unit_price_cents >= 0),
    PRIMARY KEY (order_id, sku)
);

CREATE INDEX orders_by_customer ON orders (customer_id);

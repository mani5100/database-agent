CREATE TABLE customers (
    id INT AUTO_INCREMENT PRIMARY KEY,
    display_name VARCHAR(255) NOT NULL
);

CREATE TABLE orders (
    id INT AUTO_INCREMENT PRIMARY KEY,
    customer_id INT NOT NULL,
    amt DECIMAL(10, 2) NOT NULL,
    ts TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (customer_id) REFERENCES customers(id)
);

INSERT INTO customers (display_name) VALUES
    ('Acme Corp'),
    ('Globex Inc'),
    ('Initech'),
    ('Umbrella LLC'),
    ('Soylent Co'),
    ('Stark Industries'),
    ('Wayne Enterprises'),
    ('Hooli'),
    ('Massive Dynamic'),
    ('Wonka Industries');
    -- Wonka Industries deliberately has no orders below, tests the
    -- no-related-rows edge case for relationship/join handling later.

INSERT INTO orders (customer_id, amt, ts) VALUES
    (1, 150.00, '2026-01-05 10:00:00'),
    (1, 89.99,  '2026-01-12 14:30:00'),
    (1, 210.25, '2026-02-01 09:00:00'),
    (2, 320.50, '2026-01-08 09:15:00'),
    (2, 75.00,  '2026-03-14 11:20:00'),
    (3, 45.00,  '2026-01-20 16:45:00'),
    (3, 99.99,  '2026-02-18 13:00:00'),
    (3, 130.00, '2026-04-02 08:30:00'),
    (4, 500.00, '2026-01-15 12:00:00'),
    (4, 60.75,  '2026-02-22 17:10:00'),
    (5, 25.50,  '2026-01-25 10:45:00'),
    (5, 410.00, '2026-03-05 15:30:00'),
    (5, 15.99,  '2026-04-10 09:00:00'),
    (6, 999.99, '2026-01-30 20:00:00'),
    (6, 249.00, '2026-02-14 11:11:00'),
    (7, 88.88,  '2026-01-10 08:00:00'),
    (7, 176.40, '2026-03-22 14:00:00'),
    (8, 33.33,  '2026-02-05 09:30:00'),
    (8, 720.00, '2026-04-18 16:00:00'),
    (9, 145.60, '2026-01-28 13:45:00');

-- ============================================================
-- SimpleDigitalKhata
-- Complete PostgreSQL Database Setup
-- ============================================================
--
-- Database:
--     simpledigitalkhata
--
-- Includes:
--     1. Database creation
--     2. Extensions
--     3. Tables
--     4. Constraints
--     5. Indexes
--     6. Dummy/Test Data
--     7. Testing Queries
--
-- PostgreSQL
-- ============================================================


-- ============================================================
-- STEP 1: CREATE DATABASE
-- ============================================================

-- Run this part while connected to the default "postgres"
-- database.

-- CREATE DATABASE simpledigitalkhata;


-- ============================================================
-- IMPORTANT
-- ============================================================
-- After creating the database, connect to:
--
--     simpledigitalkhata
--
-- Then run everything below this point.
--
-- If using pgAdmin:
--   Databases
--      → simpledigitalkhata
--          → Query Tool
--
-- If using psql:
--
--     \c simpledigitalkhata
--
-- ============================================================


-- ============================================================
-- STEP 2: EXTENSIONS
-- ============================================================

CREATE EXTENSION IF NOT EXISTS "pgcrypto";
CREATE EXTENSION IF NOT EXISTS pg_trgm;


-- ============================================================
-- STEP 3: PRODUCTS
-- ============================================================

CREATE TABLE products (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    name VARCHAR(255) NOT NULL,

    -- Barcode is text because barcodes may contain leading zeros.
    barcode VARCHAR(100) UNIQUE,

    price NUMERIC(12, 2) NOT NULL
        CHECK (price >= 0),

    stock_quantity INTEGER NOT NULL DEFAULT 0
        CHECK (stock_quantity >= 0)
);


-- ============================================================
-- STEP 4: CUSTOMERS
-- ============================================================

CREATE TABLE customers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    name VARCHAR(255) NOT NULL,

    phone VARCHAR(30)
);


-- Customer names are unique after normalization:
--
-- "Ali Khan"
-- "ali khan"
-- " ALI KHAN "
-- "Ali    Khan"
--
-- are treated as the same name.

CREATE UNIQUE INDEX uq_customers_normalized_name
ON customers (
    LOWER(
        REGEXP_REPLACE(
            TRIM(name),
            '\s+',
            ' ',
            'g'
        )
    )
);


-- ============================================================
-- STEP 5: BILLS
-- ============================================================

CREATE TABLE bills (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    bill_number VARCHAR(50) NOT NULL UNIQUE,

    -- NULL means Walk-in Customer.
    customer_id UUID
        REFERENCES customers(id)
        ON DELETE SET NULL,

    total NUMERIC(12, 2) NOT NULL
        CHECK (total >= 0),

    payment_status VARCHAR(20) NOT NULL DEFAULT 'not_paid'
        CHECK (payment_status IN ('paid', 'not_paid')),

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);


-- ============================================================
-- STEP 6: BILL ITEMS
-- ============================================================

CREATE TABLE bill_items (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    bill_id UUID NOT NULL
        REFERENCES bills(id)
        ON DELETE CASCADE,

    -- Can become NULL if the product is deleted later.
    product_id UUID
        REFERENCES products(id)
        ON DELETE SET NULL,

    -- Snapshot fields.
    -- These preserve historical bill information even if
    -- the original product is edited/deleted later.

    product_name VARCHAR(255) NOT NULL,

    barcode VARCHAR(100),

    quantity INTEGER NOT NULL
        CHECK (quantity > 0),

    unit_price NUMERIC(12, 2) NOT NULL
        CHECK (unit_price >= 0),

    total NUMERIC(12, 2) NOT NULL
        CHECK (total >= 0)
);


-- ============================================================
-- STEP 7: SHOP SETTINGS
-- ============================================================

CREATE TABLE shop_settings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    shop_name VARCHAR(255) NOT NULL,

    phone VARCHAR(30),

    address TEXT,

    logo_url TEXT
);


-- ============================================================
-- STEP 8: SEARCH INDEXES
-- ============================================================

-- Product search
CREATE INDEX idx_products_name_trgm
ON products
USING GIN (name gin_trgm_ops);

CREATE INDEX idx_products_barcode_trgm
ON products
USING GIN (barcode gin_trgm_ops);


-- Customer search
CREATE INDEX idx_customers_name_trgm
ON customers
USING GIN (name gin_trgm_ops);

CREATE INDEX idx_customers_phone_trgm
ON customers
USING GIN (phone gin_trgm_ops);


-- Bill indexes
CREATE INDEX idx_bills_customer_id
ON bills(customer_id);

CREATE INDEX idx_bills_created_at
ON bills(created_at);

CREATE INDEX idx_bills_payment_status
ON bills(payment_status);


-- Bill item indexes
CREATE INDEX idx_bill_items_bill_id
ON bill_items(bill_id);

CREATE INDEX idx_bill_items_product_id
ON bill_items(product_id);


-- ============================================================
-- STEP 9: DUMMY PRODUCTS
-- ============================================================

INSERT INTO products
    (name, barcode, price, stock_quantity)
VALUES
    ('Coca Cola 500ml', '089400123456', 120.00, 50),
    ('Pepsi 500ml', '089400123457', 110.00, 40),
    ('Surf Excel 1kg', '089400123458', 450.00, 25),
    ('Nestle Milk 1L', '089400123459', 280.00, 30),
    ('Lays Classic 50g', '089400123460', 100.00, 60);


-- ============================================================
-- STEP 10: DUMMY CUSTOMERS
-- ============================================================

INSERT INTO customers
    (name, phone)
VALUES
    ('Ali Khan', '03001234567'),
    ('Sara Ahmed', '03111234567'),
    ('Ahmed Raza', '03221234567');


-- ============================================================
-- STEP 11: DUMMY SHOP SETTINGS
-- ============================================================

INSERT INTO shop_settings
    (shop_name, phone, address, logo_url)
VALUES
    (
        'Simple Digital Khata Store',
        '03001234567',
        'Lahore, Pakistan',
        NULL
    );


-- ============================================================
-- STEP 12: DUMMY BILL #1
-- ============================================================

INSERT INTO bills
    (bill_number, customer_id, total, payment_status)
VALUES
    (
        'B-000001',
        (
            SELECT id
            FROM customers
            WHERE name = 'Ali Khan'
        ),
        350.00,
        'paid'
    );


-- Bill #1 items

INSERT INTO bill_items
    (
        bill_id,
        product_id,
        product_name,
        barcode,
        quantity,
        unit_price,
        total
    )
VALUES
    (
        (
            SELECT id
            FROM bills
            WHERE bill_number = 'B-000001'
        ),
        (
            SELECT id
            FROM products
            WHERE barcode = '089400123456'
        ),
        'Coca Cola 500ml',
        '089400123456',
        2,
        120.00,
        240.00
    ),
    (
        (
            SELECT id
            FROM bills
            WHERE bill_number = 'B-000001'
        ),
        (
            SELECT id
            FROM products
            WHERE barcode = '089400123460'
        ),
        'Lays Classic 50g',
        '089400123460',
        1,
        100.00,
        100.00
    ),
    (
        (
            SELECT id
            FROM bills
            WHERE bill_number = 'B-000001'
        ),
        (
            SELECT id
            FROM products
            WHERE barcode = '089400123457'
        ),
        'Pepsi 500ml',
        '089400123457',
        1,
        10.00,
        10.00
    );


-- ============================================================
-- NOTE:
-- The above bill is intentionally simple dummy data.
-- Its bill_items total = 240 + 100 + 10 = 350.
--
-- In the real FastAPI application, product prices and totals
-- will NOT be trusted from the frontend.
-- FastAPI will calculate them from the database.
-- ============================================================


-- ============================================================
-- STEP 13: DUMMY BILL #2
-- ============================================================

INSERT INTO bills
    (bill_number, customer_id, total, payment_status)
VALUES
    (
        'B-000002',
        (
            SELECT id
            FROM customers
            WHERE name = 'Sara Ahmed'
        ),
        730.00,
        'not_paid'
    );


-- Bill #2 items

INSERT INTO bill_items
    (
        bill_id,
        product_id,
        product_name,
        barcode,
        quantity,
        unit_price,
        total
    )
VALUES
    (
        (
            SELECT id
            FROM bills
            WHERE bill_number = 'B-000002'
        ),
        (
            SELECT id
            FROM products
            WHERE barcode = '089400123458'
        ),
        'Surf Excel 1kg',
        '089400123458',
        1,
        450.00,
        450.00
    ),
    (
        (
            SELECT id
            FROM bills
            WHERE bill_number = 'B-000002'
        ),
        (
            SELECT id
            FROM products
            WHERE barcode = '089400123459'
        ),
        'Nestle Milk 1L',
        '089400123459',
        1,
        280.00,
        280.00
    );


-- ============================================================
-- STEP 14: BASIC TESTING
-- ============================================================


-- ----------------------------
-- Check all tables
-- ----------------------------

SELECT table_name
FROM information_schema.tables
WHERE table_schema = 'public'
ORDER BY table_name;


-- ----------------------------
-- Check products
-- ----------------------------

SELECT *
FROM products
ORDER BY name;


-- ----------------------------
-- Check customers
-- ----------------------------

SELECT *
FROM customers
ORDER BY name;


-- ----------------------------
-- Check bills
-- ----------------------------

SELECT
    b.bill_number,
    c.name AS customer,
    b.total,
    b.payment_status,
    b.created_at
FROM bills b
LEFT JOIN customers c
    ON b.customer_id = c.id
ORDER BY b.created_at;


-- ----------------------------
-- Check bill items
-- ----------------------------

SELECT
    b.bill_number,
    bi.product_name,
    bi.quantity,
    bi.unit_price,
    bi.total
FROM bill_items bi
JOIN bills b
    ON bi.bill_id = b.id
ORDER BY b.bill_number, bi.product_name;


-- ============================================================
-- STEP 15: TEST PRODUCT SEARCH
-- ============================================================

-- Should find Coca Cola.

SELECT *
FROM products
WHERE name ILIKE '%cola%';


-- Should find Coca Cola and Pepsi if searching "500ml".

SELECT *
FROM products
WHERE name ILIKE '%500ml%';


-- ============================================================
-- STEP 16: TEST BARCODE SEARCH
-- ============================================================

SELECT *
FROM products
WHERE barcode = '089400123456';


-- ============================================================
-- STEP 17: TEST CUSTOMER SEARCH
-- ============================================================

-- Should find Ali Khan.

SELECT *
FROM customers
WHERE name ILIKE '%ali%';


-- ============================================================
-- STEP 18: TEST CUSTOMER BILL HISTORY
-- ============================================================

SELECT
    b.bill_number,
    b.created_at,
    b.total,
    b.payment_status
FROM bills b
JOIN customers c
    ON b.customer_id = c.id
WHERE c.name = 'Ali Khan'
ORDER BY b.created_at DESC;


-- ============================================================
-- STEP 19: TEST CUSTOMER SUMMARY
-- ============================================================

SELECT
    c.name AS customer,
    COUNT(b.id) AS total_bills,
    COUNT(*) FILTER (
        WHERE b.payment_status = 'paid'
    ) AS paid_bills,
    COUNT(*) FILTER (
        WHERE b.payment_status = 'not_paid'
    ) AS not_paid_bills,
    COALESCE(
        SUM(b.total) FILTER (
            WHERE b.payment_status = 'not_paid'
        ),
        0
    ) AS unpaid_total
FROM customers c
LEFT JOIN bills b
    ON c.id = b.customer_id
GROUP BY c.id, c.name
ORDER BY c.name;


-- ============================================================
-- STEP 20: TEST BILL TOTALS
-- ============================================================

-- Compare stored bill total with the sum of bill items.

SELECT
    b.bill_number,
    b.total AS bill_total,
    COALESCE(SUM(bi.total), 0) AS items_total,
    CASE
        WHEN b.total = COALESCE(SUM(bi.total), 0)
        THEN 'OK'
        ELSE 'MISMATCH'
    END AS validation
FROM bills b
LEFT JOIN bill_items bi
    ON b.id = bi.bill_id
GROUP BY b.id, b.bill_number, b.total
ORDER BY b.bill_number;


-- ============================================================
-- STEP 21: TEST PAYMENT STATUS
-- ============================================================

-- Mark B-000002 as paid.

UPDATE bills
SET
    payment_status = 'paid',
    updated_at = NOW()
WHERE bill_number = 'B-000002';


-- Verify.

SELECT
    bill_number,
    payment_status
FROM bills
WHERE bill_number = 'B-000002';


-- Change it back for testing.

UPDATE bills
SET
    payment_status = 'not_paid',
    updated_at = NOW()
WHERE bill_number = 'B-000002';


-- ============================================================
-- STEP 22: TEST FOREIGN KEY RELATIONSHIP
-- ============================================================

SELECT
    b.bill_number,
    c.name AS customer,
    bi.product_name,
    bi.quantity,
    bi.unit_price,
    bi.total
FROM bills b
LEFT JOIN customers c
    ON b.customer_id = c.id
JOIN bill_items bi
    ON b.id = bi.bill_id
ORDER BY b.bill_number;


-- ============================================================
-- STEP 23: DATABASE SUMMARY
-- ============================================================

SELECT
    'products' AS table_name,
    COUNT(*) AS records
FROM products

UNION ALL

SELECT
    'customers',
    COUNT(*)
FROM customers

UNION ALL

SELECT
    'bills',
    COUNT(*)
FROM bills

UNION ALL

SELECT
    'bill_items',
    COUNT(*)
FROM bill_items

UNION ALL

SELECT
    'shop_settings',
    COUNT(*)
FROM shop_settings;


-- ============================================================
-- END
-- ============================================================


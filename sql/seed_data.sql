.mode csv
.headers on
.import --skip 1 data/customers.csv customers
.import --skip 1 data/products.csv products
.import --skip 1 data/orders.csv orders

UPDATE orders SET discount_pct = NULL WHERE discount_pct = '';
UPDATE orders SET rating = NULL WHERE rating = '';

SELECT 'customers', COUNT(*) FROM customers UNION ALL
SELECT 'products', COUNT(*) FROM products UNION ALL
SELECT 'orders', COUNT(*) FROM orders;

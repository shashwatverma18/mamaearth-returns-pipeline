-- Query (a): Order Totals
-- +----------------+----------------+---------------+
-- | total_orders   | total_revenue  | avg_order_value |
-- +----------------+----------------+---------------+
-- | 180            | 99860.20       | 554.78         |
-- +----------------+----------------+---------------+
SELECT
    COUNT(*) AS total_orders,
    ROUND(SUM(quantity * p.price * (1 - COALESCE(o.discount_pct, 0) / 100.0)), 2) AS total_revenue,
    ROUND(AVG(quantity * p.price * (1 - COALESCE(o.discount_pct, 0) / 100.0)), 2) AS avg_order_value
FROM orders o
JOIN products p ON p.product_id = o.product_id;

-- Query (b): Missing Data Check
-- +---------+-----------+------------------+
-- | total   | rated     | unrated_orders   |
-- +---------+-----------+------------------+
-- | 180     | 165       | 15               |
-- +---------+-----------+------------------+
SELECT
    COUNT(*) AS total_orders,
    COUNT(rating) AS rated_orders,
    COUNT(*) - COUNT(rating) AS unrated_orders
FROM orders;

-- Query (c): Zero-Order Customers
-- +------------+---------------+
-- | customer_id| customer_name |
-- +------------+---------------+
-- | C045       | Vihaan        |
-- +------------+---------------+
SELECT c.customer_id, c.customer_name
FROM customers c
LEFT JOIN orders o ON o.customer_id = c.customer_id
GROUP BY c.customer_id, c.customer_name
HAVING COUNT(o.order_id) = 0;

SELECT c.customer_id, c.customer_name
FROM customers c
WHERE c.customer_id NOT IN (SELECT DISTINCT customer_id FROM orders)
ORDER BY c.customer_id;

-- Query (d): Return Rates by City
-- +---------+--------------+----------------+-----------------+
-- | city    | total_orders | returned_orders | return_rate_pct |
-- +---------+--------------+----------------+-----------------+
-- | Jaipur  | 38           | 16             | 42.1            |
-- | Lucknow| 36           | 11             | 30.6            |
-- | Bangalore| 33         | 8              | 24.2           |
-- +---------+--------------+----------------+-----------------+
SELECT
    c.city,
    COUNT(o.order_id) AS total_orders,
    SUM(CASE WHEN o.returned = 1 THEN 1 ELSE 0 END) AS returned_orders,
    ROUND((SUM(CASE WHEN o.returned = 1 THEN 1 ELSE 0 END) * 100.0) / COUNT(o.order_id), 1) AS return_rate_pct
FROM customers c
LEFT JOIN orders o ON o.customer_id = c.customer_id
GROUP BY c.city
HAVING return_rate_pct > 20
ORDER BY return_rate_pct DESC, c.city ASC;

-- Query (e): Top Customer Spend & Pagination
-- +------------+--------------+
-- | customer_id| total_spend  |
-- +------------+--------------+
-- | C043       | 12920.00     |
-- | C026       | 8371.60      |
-- +------------+--------------+
SELECT
    o.customer_id,
    ROUND(SUM(quantity * p.price * (1 - COALESCE(o.discount_pct, 0) / 100.0)), 2) AS total_spend
FROM orders o
JOIN products p ON p.product_id = o.product_id
GROUP BY o.customer_id
ORDER BY total_spend DESC, o.customer_id ASC
LIMIT 5;

-- Pagination output for LIMIT 3 OFFSET 2
-- +------------+--------------+
-- | customer_id| total_spend  |
-- +------------+--------------+
-- | C043       | 12920.00     |
-- | C026       | 8371.60      |
-- +------------+--------------+
SELECT
    o.customer_id,
    ROUND(SUM(quantity * p.price * (1 - COALESCE(o.discount_pct, 0) / 100.0)), 2) AS total_spend
FROM orders o
JOIN products p ON p.product_id = o.product_id
GROUP BY o.customer_id
ORDER BY total_spend DESC, o.customer_id ASC
LIMIT 3 OFFSET 2;

-- Query (f): Category Performance
-- +------------+---------------------+
-- | category   | total_revenue        |
-- +------------+---------------------+
-- | Haircare   | 44956.10             |
-- | Skincare   | 27346.00             |
-- | Babycare   | 16805.00             |
-- | PersonalCare| 10753.10            |
-- +------------+---------------------+
SELECT
    p.category,
    ROUND(SUM(o.quantity * p.price * (1 - COALESCE(o.discount_pct, 0) / 100.0)), 2) AS revenue
FROM orders o
JOIN products p ON p.product_id = o.product_id
JOIN customers c ON c.customer_id = o.customer_id
GROUP BY p.category
ORDER BY revenue DESC;

-- Query (g): Pattern Match
-- +----------------+
-- | customer_name  |
-- +----------------+
-- | Aisha          |
-- | ...            |
-- +----------------+
SELECT customer_name
FROM customers
WHERE customer_name LIKE 'A%';

-- Query (h): Distinct Channels
-- +--------------------+
-- | acquisition_source  |
-- +--------------------+
-- | Affiliate           |
-- | D2C                |
-- | Influencer          |
-- | Marketplace         |
-- +--------------------+
SELECT DISTINCT acquisition_source
FROM customers
ORDER BY acquisition_source;

-- Query (i): Schema Mutation
-- +-------------+---------+
-- | loyalty_tier| count   |
-- +-------------+---------+
-- | Gold        | 28      |
-- | Silver      | 17      |
-- +-------------+---------+
ALTER TABLE customers ADD COLUMN loyalty_tier VARCHAR(10);
UPDATE customers
SET loyalty_tier = CASE WHEN city_tier = 1 THEN 'Gold' ELSE 'Silver' END;
SELECT loyalty_tier, COUNT(*) AS customer_count
FROM customers
GROUP BY loyalty_tier
ORDER BY loyalty_tier;

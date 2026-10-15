PRAGMA foreign_keys = ON;

CREATE TABLE customers (
    customer_id VARCHAR(10) PRIMARY KEY,
    customer_name VARCHAR(100) NOT NULL,
    city VARCHAR(50) NOT NULL,
    city_tier INTEGER NOT NULL DEFAULT 1,
    acquisition_source VARCHAR(40) NOT NULL DEFAULT 'D2C'
);

CREATE TABLE products (
    product_id VARCHAR(10) PRIMARY KEY,
    product_name VARCHAR(200) NOT NULL,
    category VARCHAR(50) NOT NULL,
    price REAL NOT NULL DEFAULT 0.0
);

CREATE TABLE orders (
    order_id VARCHAR(20) PRIMARY KEY,
    customer_id VARCHAR(10) NOT NULL,
    product_id VARCHAR(10) NOT NULL,
    order_date TEXT NOT NULL DEFAULT '2024-01-01',
    quantity INTEGER NOT NULL DEFAULT 1,
    discount_pct REAL DEFAULT NULL,
    payment_method VARCHAR(20) NOT NULL DEFAULT 'CARD',
    rating REAL DEFAULT NULL,
    returned INTEGER NOT NULL DEFAULT 0,
    FOREIGN KEY (customer_id) REFERENCES customers(customer_id),
    FOREIGN KEY (product_id) REFERENCES products(product_id)
);

CREATE INDEX idx_orders_customer_id ON orders(customer_id);
CREATE INDEX idx_orders_product_id ON orders(product_id);
CREATE INDEX idx_orders_order_date ON orders(order_date);

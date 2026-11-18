CREATE TABLE IF NOT EXISTS customers (
    customer_id VARCHAR(36) PRIMARY KEY ,
    first_name VARCHAR(50) NOT NULL ,
    last_name VARCHAR(50) NOT NULL , 
    email VARCHAR(100) UNIQUE NOT NULL ,
    acquisition_channel VARCHAR(50),
    created_at TIMESTAMP NOT NULL
);

CREATE TABLE IF NOT EXISTS products (
    product_id VARCHAR(36) PRIMARY KEY ,
    product_name VARCHAR(100) NOT NULL ,
    category VARCHAR(50) NOT NULL ,
    unit_price DECIMAL(10,2) NOT NULL ,
    cost_price DECIMAL(10,2) NOT NULL
);

CREATE TABLE IF NOT EXISTS orders (
    order_id VARCHAR(36) PRIMARY KEY ,
    customer_id VARCHAR(36) NOT NULL ,
    order_status VARCHAR(20) NOT NULL ,
    order_timestamp TIMESTAMP NOT NULL ,
    shipping_cost DECIMAL(8,2) DEFAULT 0.00,
    FOREIGN KEY (customer_id) REFERENCES customers(customer_id)

);

CREATE TABLE IF NOT EXISTS order_items (
    order_item_id VARCHAR(36) PRIMARY KEY ,
    order_id VARCHAR(36) NOT NULL ,
    product_id VARCHAR(36) NOT NULL ,
    quantity INT NOT NULL ,
    item_price DECIMAL(10,2) NOT NULL ,
    FOREIGN KEY (order_id) REFERENCES orders(order_id),
    FOREIGN KEY (product_id) REFERENCES products(product_id)
);

CREATE INDEX IF NOT EXISTS idx_orders_customer ON orders(customer_id) ;
CREATE INDEX IF NOT EXISTS idx_orders_timestamp ON orders(order_timestamp) ;
CREATE INDEX IF NOT EXISTS idx_order_items_order ON order_items(order_id);
CREATE INDEX IF NOT EXISTS idx_order_items_product ON order_items(product_id);
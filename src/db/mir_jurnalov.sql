CREATE TABLE roles (
    role_id SERIAL PRIMARY KEY,
    name VARCHAR(50) NOT NULL UNIQUE
);

CREATE TABLE categories (
    category_id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL UNIQUE
);

CREATE TABLE publishers (
    publisher_id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL UNIQUE
);

CREATE TABLE variants (
    variant_id SERIAL PRIMARY KEY,
    variant_name VARCHAR(50) NOT NULL UNIQUE
);

CREATE TABLE users (
    user_id SERIAL PRIMARY KEY,
    login VARCHAR(100) NOT NULL UNIQUE,
    last_name VARCHAR(100) NOT NULL,
    first_name VARCHAR(100) NOT NULL,
    middle_name VARCHAR(100),
    role_id INTEGER REFERENCES roles(role_id)
);

CREATE TABLE models (
    model_id SERIAL PRIMARY KEY,
    name VARCHAR(200) NOT NULL,
    category_id INTEGER REFERENCES categories(category_id),
    publisher_id INTEGER REFERENCES publishers(publisher_id),
    image_path VARCHAR(255),
    base_price NUMERIC(10,2) NOT NULL CHECK (base_price > 0)
);

CREATE TABLE stock_items (
    stock_item_id SERIAL PRIMARY KEY,
    model_id INTEGER REFERENCES models(model_id),
    variant_id INTEGER REFERENCES variants(variant_id),
    quantity INTEGER NOT NULL CHECK (quantity >= 0),
    price NUMERIC(10,2) NOT NULL CHECK (price > 0)
);

CREATE TABLE orders (
    order_id SERIAL PRIMARY KEY,
    order_date DATE NOT NULL DEFAULT CURRENT_DATE,
    user_id INTEGER REFERENCES users(user_id)
);

CREATE TABLE order_items (
    order_item_id SERIAL PRIMARY KEY,
    order_id INTEGER REFERENCES orders(order_id),
    stock_item_id INTEGER REFERENCES stock_items(stock_item_id),
    quantity INTEGER NOT NULL CHECK (quantity > 0),
    price NUMERIC(10,2) NOT NULL CHECK (price > 0)
);

ALTER TABLE models ADD COLUMN description TEXT;
ALTER TABLE models ADD COLUMN composition TEXT;
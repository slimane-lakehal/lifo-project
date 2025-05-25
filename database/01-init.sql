-- LIFO Food Waste Platform Database Schema
-- Designed for PostgreSQL with TimescaleDB extension for time-series data

-- Enable TimescaleDB extension
CREATE EXTENSION IF NOT EXISTS timescaledb;

-- Core business entities
CREATE TABLE stores (
    store_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    store_name VARCHAR(255) NOT NULL,
    store_type VARCHAR(50) NOT NULL, -- 'grocery', 'pet_food', 'convenience'
    address JSONB,
    timezone VARCHAR(50) DEFAULT 'UTC',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Product catalog (master data)
CREATE TABLE products (
    product_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    sku VARCHAR(100) UNIQUE NOT NULL,
    product_name VARCHAR(255) NOT NULL,
    brand VARCHAR(100),
    category VARCHAR(100),
    subcategory VARCHAR(100),
    unit_size VARCHAR(50),
    unit_type VARCHAR(50), -- 'kg', 'lbs', 'pieces', etc.
    shelf_life_days INTEGER,
    temperature_zone VARCHAR(50), -- 'ambient', 'refrigerated', 'frozen'
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Inventory movements (time-series data)
CREATE TABLE inventory_movements (
    movement_id UUID DEFAULT gen_random_uuid(),
    store_id UUID NOT NULL REFERENCES stores(store_id),
    product_id UUID NOT NULL REFERENCES products(product_id),
    movement_type VARCHAR(50) NOT NULL, -- 'receipt', 'sale', 'waste', 'adjustment'
    quantity DECIMAL(10,2) NOT NULL,
    unit_cost DECIMAL(10,2),
    batch_id UUID,
    expiration_date DATE,
    transaction_time TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    PRIMARY KEY (movement_id, transaction_time)
);

-- Create hypertable for time-series data
SELECT create_hypertable('inventory_movements', 'transaction_time');

-- Batch tracking
CREATE TABLE batches (
    batch_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    store_id UUID NOT NULL REFERENCES stores(store_id),
    product_id UUID NOT NULL REFERENCES products(product_id),
    supplier_id UUID,
    received_date TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    expiration_date DATE NOT NULL,
    quantity DECIMAL(10,2) NOT NULL,
    unit_cost DECIMAL(10,2),
    status VARCHAR(50) DEFAULT 'active', -- 'active', 'depleted', 'expired', 'discarded'
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Supplier information
CREATE TABLE suppliers (
    supplier_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    supplier_name VARCHAR(255) NOT NULL,
    contact_info JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Current inventory view (materialized)
CREATE TABLE current_inventory (
    store_id UUID NOT NULL REFERENCES stores(store_id),
    product_id UUID NOT NULL REFERENCES products(product_id),
    batch_id UUID REFERENCES batches(batch_id),
    quantity DECIMAL(10,2) NOT NULL DEFAULT 0,
    last_updated TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    PRIMARY KEY (store_id, product_id, batch_id)
);

-- Indexes for performance
CREATE INDEX idx_movements_store ON inventory_movements(store_id, transaction_time DESC);
CREATE INDEX idx_movements_product ON inventory_movements(product_id, transaction_time DESC);
CREATE INDEX idx_movements_batch ON inventory_movements(batch_id, transaction_time DESC);
CREATE INDEX idx_movements_type ON inventory_movements(movement_type, transaction_time DESC);

CREATE INDEX idx_batches_store ON batches(store_id);
CREATE INDEX idx_batches_product ON batches(product_id);
CREATE INDEX idx_batches_expiration ON batches(expiration_date);

CREATE INDEX idx_current_inv_store ON current_inventory(store_id);
CREATE INDEX idx_current_inv_product ON current_inventory(product_id);

-- Views
CREATE VIEW inventory_status AS
SELECT 
    ci.store_id,
    s.store_name,
    ci.product_id,
    p.product_name,
    p.category,
    SUM(ci.quantity) as total_quantity,
    b.expiration_date,
    b.batch_id
FROM current_inventory ci
JOIN stores s ON ci.store_id = s.store_id
JOIN products p ON ci.product_id = p.product_id
LEFT JOIN batches b ON ci.batch_id = b.batch_id
GROUP BY ci.store_id, s.store_name, ci.product_id, p.product_name, p.category, b.expiration_date, b.batch_id;

CREATE VIEW inventory_age AS
SELECT 
    store_id,
    product_id,
    batch_id,
    quantity,
    expiration_date,
    NOW() as current_time,
    expiration_date - NOW() as days_until_expiry
FROM current_inventory ci
JOIN batches b ON ci.batch_id = b.batch_id
WHERE quantity > 0;

-- Functions
CREATE OR REPLACE FUNCTION update_inventory_on_movement()
RETURNS TRIGGER AS $$
BEGIN
    -- Update or insert into current_inventory
    INSERT INTO current_inventory (store_id, product_id, batch_id, quantity)
    VALUES (NEW.store_id, NEW.product_id, NEW.batch_id, 
            CASE WHEN NEW.movement_type IN ('receipt') THEN NEW.quantity
                 ELSE -NEW.quantity END)
    ON CONFLICT (store_id, product_id, batch_id)
    DO UPDATE SET 
        quantity = current_inventory.quantity + 
            CASE WHEN NEW.movement_type IN ('receipt') THEN NEW.quantity
                 ELSE -NEW.quantity END,
        last_updated = NOW();
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger for inventory movements
CREATE TRIGGER trg_inventory_movement
AFTER INSERT ON inventory_movements
FOR EACH ROW
EXECUTE FUNCTION update_inventory_on_movement();

-- Function to auto-update timestamps
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Function to calculate LIFO cost
CREATE OR REPLACE FUNCTION calculate_lifo_cost(p_store_id UUID, p_product_id UUID, p_quantity DECIMAL)
RETURNS DECIMAL AS $$
DECLARE
    v_total_cost DECIMAL := 0;
    v_remaining_quantity DECIMAL := p_quantity;
    v_batch_quantity DECIMAL;
    v_unit_cost DECIMAL;
BEGIN
    FOR v_batch_quantity, v_unit_cost IN
        SELECT ci.quantity, b.unit_cost
        FROM current_inventory ci
        JOIN batches b ON ci.batch_id = b.batch_id
        WHERE ci.store_id = p_store_id 
        AND ci.product_id = p_product_id
        AND ci.quantity > 0
        ORDER BY b.received_date DESC
    LOOP
        IF v_remaining_quantity <= 0 THEN
            EXIT;
        END IF;
        
        IF v_batch_quantity >= v_remaining_quantity THEN
            v_total_cost := v_total_cost + (v_remaining_quantity * v_unit_cost);
            v_remaining_quantity := 0;
        ELSE
            v_total_cost := v_total_cost + (v_batch_quantity * v_unit_cost);
            v_remaining_quantity := v_remaining_quantity - v_batch_quantity;
        END IF;
    END LOOP;
    
    RETURN v_total_cost;
END;
$$ LANGUAGE plpgsql;

-- Triggers for updating timestamps
CREATE TRIGGER set_timestamp
BEFORE UPDATE ON stores
FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER set_timestamp
BEFORE UPDATE ON products
FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER set_timestamp
BEFORE UPDATE ON batches
FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER set_timestamp
BEFORE UPDATE ON suppliers
FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column();

-- LIFO Food Waste Platform Database Schema
-- Designed for PostgreSQL with TimescaleDB extension for time-series data


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
    category VARCHAR(100) NOT NULL, -- 'dairy', 'meat', 'produce', 'dry_goods', etc.
    subcategory VARCHAR(100),
    unit_size VARCHAR(50), -- '1kg', '500ml', '12-pack'
    unit_type VARCHAR(20), -- 'weight', 'volume', 'count'
    
    -- Shelf life characteristics
    typical_shelf_life_days INTEGER,
    storage_requirements VARCHAR(100), -- 'refrigerated', 'frozen', 'dry'
    product_type VARCHAR(50), -- 'perishable', 'semi_perishable', 'non_perishable'
    
    -- Business rules
    discount_rules JSONB, -- Flexible discount logic
    minimum_shelf_life_days INTEGER DEFAULT 1,
    
    metadata JSONB, -- Additional product attributes
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Suppliers information
CREATE TABLE suppliers (
    supplier_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    supplier_name VARCHAR(255) NOT NULL,
    contact_info JSONB,
    default_lead_time_days INTEGER,
    reliability_score DECIMAL(3,2), -- 0.00 to 1.00
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Product batches (core inventory unit)
CREATE TABLE product_batches (
    batch_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    store_id UUID REFERENCES stores(store_id),
    product_id UUID REFERENCES products(product_id),
    supplier_id UUID REFERENCES suppliers(supplier_id),
    
    -- Batch identifiers
    supplier_lot_code VARCHAR(100),
    internal_batch_code VARCHAR(100),
    
    -- Quantities
    initial_quantity INTEGER NOT NULL,
    current_quantity INTEGER NOT NULL,
    reserved_quantity INTEGER DEFAULT 0, -- Items held for orders
    
    -- Dates
    received_date DATE NOT NULL,
    expiry_date DATE NOT NULL,
    best_before_date DATE, -- Different from expiry for some products
    
    -- Financial
    cost_per_unit DECIMAL(10,3) NOT NULL,
    current_price DECIMAL(10,2) NOT NULL,
    original_price DECIMAL(10,2) NOT NULL,
    
    -- Location
    storage_location VARCHAR(100), -- 'aisle-3', 'freezer-A', 'backroom'
    display_location VARCHAR(100), -- Where customers see it
    
    -- Status tracking
    status VARCHAR(50) DEFAULT 'active', -- 'active', 'marked_down', 'expired', 'disposed'
    last_movement_date DATE,
    
    -- Computed fields (updated by triggers)
    days_until_expiry INTEGER,
    turnover_days INTEGER, -- How quickly this batch typically sells
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    CONSTRAINT positive_quantities CHECK (current_quantity >= 0),
    CONSTRAINT valid_dates CHECK (expiry_date >= received_date)
);
-- Time-series table for inventory movements
CREATE TABLE inventory_movements (
    movement_id UUID DEFAULT gen_random_uuid(),
    batch_id UUID REFERENCES product_batches(batch_id),
    store_id UUID REFERENCES stores(store_id),
    
    movement_type TEXT NOT NULL, -- 'sale', 'waste', 'return', 'adjustment', 'markdown'
    quantity_change INTEGER NOT NULL, -- Negative for outbound
    unit_price DECIMAL(10,2), -- Price at time of movement
    
    -- Movement context
    reason TEXT, -- 'expired', 'damaged', 'customer_return', 'inventory_count'
    reference_id TEXT, -- Transaction ID, adjustment reference, etc.
    notes TEXT,
    
    movement_timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    recorded_by TEXT, -- User or system that recorded movement
    
    -- Metadata for analytics
    customer_segment TEXT, -- If applicable for sales
    discount_applied DECIMAL(5,2), -- Percentage discount if any
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

	PRIMARY KEY (movement_id, movement_timestamp)
);

-- Convert inventory_movements to time-series table
SELECT create_hypertable('inventory_movements', 'movement_timestamp');

-- Scoring snapshots (pre-calculated scores for performance)
CREATE TABLE batch_scores (
    score_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    batch_id UUID REFERENCES product_batches(batch_id),
    store_id UUID REFERENCES stores(store_id),
    
    -- Calculated scores (0-100)
    urgency_score DECIMAL(5,2) NOT NULL,
    economic_risk_score DECIMAL(5,2) NOT NULL,
    velocity_score DECIMAL(5,2) NOT NULL,
    composite_score DECIMAL(5,2) NOT NULL,
    
    -- Supporting metrics
    days_until_expiry INTEGER,
    revenue_at_risk DECIMAL(10,2),
    recommended_action VARCHAR(100), -- 'display_prominently', 'mark_down', 'bulk_discount'
    suggested_discount_percent DECIMAL(5,2),
    
    -- Forecasting
    predicted_waste_quantity INTEGER,
    predicted_waste_value DECIMAL(10,2),
    confidence_level DECIMAL(3,2),
    
    scored_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    valid_until TIMESTAMP WITH TIME ZONE, -- When score should be recalculated
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Historical turnover rates for products
CREATE TABLE product_turnover_history (
    turnover_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    store_id UUID REFERENCES stores(store_id),
    product_id UUID REFERENCES products(product_id),
    
    -- Time period
    period_start DATE NOT NULL,
    period_end DATE NOT NULL,
    
    -- Turnover metrics
    units_sold INTEGER DEFAULT 0,
    units_wasted INTEGER DEFAULT 0,
    average_days_to_sell DECIMAL(5,2),
    waste_percentage DECIMAL(5,2),
    
    -- Financial impact
    revenue_generated DECIMAL(10,2),
    cost_of_waste DECIMAL(10,2),
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Alerts and notifications
CREATE TABLE waste_alerts (
    alert_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    store_id UUID REFERENCES stores(store_id),
    batch_id UUID REFERENCES product_batches(batch_id),
    
    alert_type VARCHAR(50) NOT NULL, -- 'expiring_soon', 'high_waste_risk', 'pricing_opportunity'
    severity VARCHAR(20) NOT NULL, -- 'low', 'medium', 'high', 'critical'
    message TEXT NOT NULL,
    
    -- Alert metadata
    trigger_conditions JSONB, -- What conditions caused this alert
    recommended_actions JSONB, -- Suggested next steps
    
    -- Status tracking
    status VARCHAR(50) DEFAULT 'active', -- 'active', 'acknowledged', 'resolved', 'dismissed'
    acknowledged_by VARCHAR(100),
    acknowledged_at TIMESTAMP WITH TIME ZONE,
    resolved_at TIMESTAMP WITH TIME ZONE,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    expires_at TIMESTAMP WITH TIME ZONE -- When alert becomes irrelevant
);

-- User management and roles
CREATE TABLE users (
    user_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    username VARCHAR(100) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(50) NOT NULL, -- 'store_manager', 'brand_manager', 'admin', 'consumer'
    
    -- Multi-tenancy
    store_access UUID[] DEFAULT '{}', -- Array of store IDs user can access
    permissions JSONB,
    
    last_login TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes for performance
CREATE INDEX idx_product_batches_store_product ON product_batches(store_id, product_id);
CREATE INDEX idx_product_batches_expiry ON product_batches(expiry_date) WHERE status = 'active';
CREATE INDEX idx_product_batches_days_until_expiry ON product_batches(days_until_expiry) WHERE status = 'active';
CREATE INDEX idx_inventory_movements_timestamp ON inventory_movements(movement_timestamp);
CREATE INDEX idx_inventory_movements_batch ON inventory_movements(batch_id, movement_timestamp);
CREATE INDEX idx_batch_scores_composite ON batch_scores(composite_score DESC, scored_at);
CREATE INDEX idx_waste_alerts_store_status ON waste_alerts(store_id, status, created_at);

-- Views for common queries
CREATE OR REPLACE VIEW active_batches AS
SELECT 
    pb.batch_id,
    pb.store_id,
    pb.product_id,
    pb.initial_quantity,
    pb.current_quantity,
    pb.reserved_quantity,
    pb.received_date,
    pb.expiry_date,
    pb.best_before_date,
    pb.cost_per_unit,
    pb.current_price,
    pb.original_price,
    pb.storage_location,
    pb.display_location,
    pb.status,
    pb.last_movement_date,
    pb.turnover_days,
    pb.created_at,
    pb.updated_at,
    p.product_name,
    p.category,
    s.store_name,
    (pb.expiry_date - CURRENT_DATE) as days_until_expiry,
    CASE 
        WHEN (pb.expiry_date - CURRENT_DATE) <= 1 THEN 'critical'
        WHEN (pb.expiry_date - CURRENT_DATE) <= 3 THEN 'urgent'
        WHEN (pb.expiry_date - CURRENT_DATE) <= 7 THEN 'attention'
        ELSE 'normal'
    END as urgency_level
FROM product_batches pb
JOIN products p ON pb.product_id = p.product_id
JOIN stores s ON pb.store_id = s.store_id
WHERE pb.status = 'active' AND pb.current_quantity > 0;

CREATE VIEW batch_performance AS
SELECT 
    pb.batch_id,
    pb.store_id,
    pb.product_id,
    pb.initial_quantity,
    pb.current_quantity,
    pb.initial_quantity - pb.current_quantity as units_moved,
    ROUND((pb.initial_quantity - pb.current_quantity)::decimal / pb.initial_quantity * 100, 2) as turnover_percentage,
    pb.days_until_expiry,
    (pb.current_quantity * pb.current_price) as revenue_at_risk,
    CURRENT_DATE - pb.received_date as days_in_store
FROM product_batches pb
WHERE pb.status = 'active';


CREATE OR REPLACE FUNCTION calculate_days_until_expiry(expiry_date DATE)
RETURNS INTEGER AS $$
BEGIN
    RETURN expiry_date - CURRENT_DATE;
END;
$$ LANGUAGE plpgsql;


-- Functions for score calculation (example)
CREATE OR REPLACE FUNCTION calculate_urgency_score(days_until_expiry INTEGER, product_category VARCHAR)
RETURNS DECIMAL(5,2) AS $$
BEGIN
    -- Example scoring logic - can be customized per category
    CASE 
        WHEN product_category IN ('dairy', 'meat', 'produce') THEN
            RETURN GREATEST(0, 100 - (days_until_expiry * 15));
        WHEN product_category IN ('bakery', 'prepared_foods') THEN
            RETURN GREATEST(0, 100 - (days_until_expiry * 25));
        ELSE
            RETURN GREATEST(0, 100 - (days_until_expiry * 10));
    END CASE;
END;
$$ LANGUAGE plpgsql;

-- Triggers for automatic updates
CREATE OR REPLACE FUNCTION update_batch_score()
RETURNS TRIGGER AS $$
BEGIN
    -- Trigger to recalculate scores when batch quantity changes
    INSERT INTO batch_scores (batch_id, store_id, urgency_score, economic_risk_score, velocity_score, composite_score)
    SELECT 
        NEW.batch_id,
        NEW.store_id,
        calculate_urgency_score(NEW.days_until_expiry, p.category),
        (NEW.current_quantity * NEW.current_price) / 100, -- Simplified economic risk
        50, -- Placeholder velocity score
        50  -- Placeholder composite score
    FROM products p 
    WHERE p.product_id = NEW.product_id
    ON CONFLICT (batch_id) DO UPDATE SET
        urgency_score = EXCLUDED.urgency_score,
        economic_risk_score = EXCLUDED.economic_risk_score,
        scored_at = NOW();
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_batch_score
    AFTER UPDATE OF current_quantity ON product_batches
    FOR EACH ROW
    EXECUTE FUNCTION update_batch_score();
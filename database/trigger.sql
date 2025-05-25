-- Recreate the trigger function
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

-- Recreate the trigger
DROP TRIGGER IF EXISTS trg_inventory_movement ON inventory_movements;
CREATE TRIGGER trg_inventory_movement
AFTER INSERT ON inventory_movements
FOR EACH ROW
EXECUTE FUNCTION update_inventory_on_movement();

"""
Movement model and data generation for inventory movements.
"""

from datetime import date, datetime, timedelta
from typing import Dict, List, Any, Optional
from uuid import UUID
import random

from app.utils.data_generator import generate_uuid, format_date, weighted_choice

class Movement:
    def __init__(
        self,
        movement_id: UUID,
        batch_id: UUID,
        store_id: UUID,
        movement_type: str,
        quantity_change: int,
        unit_price: float,
        reason: Optional[str] = None,
        reference_id: Optional[str] = None,
        notes: Optional[str] = None,
        customer_segment: Optional[str] = None,
        discount_applied: Optional[float] = None,
        movement_timestamp: datetime = None,
        created_at: datetime = None
    ):
        self.movement_id = movement_id
        self.batch_id = batch_id
        self.store_id = store_id
        self.movement_type = movement_type
        self.quantity_change = quantity_change
        self.unit_price = unit_price
        self.reason = reason
        self.reference_id = reference_id
        self.notes = notes
        self.customer_segment = customer_segment
        self.discount_applied = discount_applied
        self.movement_timestamp = movement_timestamp or datetime.now()
        self.created_at = created_at or datetime.now()

class MovementGenerator:
    def __init__(self, batches: List[Dict], stores: List[Dict], products: List[Dict]):
        self.batches = batches
        self.stores = stores
        self.products = products
        self.movements: List[Dict[str, Any]] = []
        
        # Create product lookup for quick access
        self.product_lookup = {p['product_id']: p for p in products}
        
        # Movement types and their weights
        self.movement_types = [
            ('sale', 75),
            ('waste_expired', 10),
            ('waste_damaged', 3),
            ('return', 2),
            ('adjustment', 4),
            ('markdown', 6)
        ]
    
    def generate_movements_for_batch(self, batch: Dict[str, Any], start_date: date, end_date: date) -> List[Dict[str, Any]]:
        """Generate movement records for a single batch."""
        batch_movements = []
        product = self.product_lookup[batch['product_id']]
        
        # Skip if the batch was received after our end date
        if batch['received_date'] > end_date:
            return batch_movements
        
        # Adjust start date if batch was received after start date
        start_date = max(start_date, batch['received_date'])
        
        # Calculate how many items were moved
        items_moved = batch['initial_quantity'] - batch['current_quantity']
        
        # If nothing was moved, we might still generate some movements
        if items_moved == 0 and random.random() < 0.2:
            items_moved = int(batch['initial_quantity'] * random.uniform(0.1, 0.3))
        
        # If still nothing moved, skip this batch
        if items_moved == 0:
            return batch_movements
        
        # Generate movements until we account for all moved items
        remaining_items = items_moved
        current_date = start_date
        
        while remaining_items > 0 and current_date <= end_date:
            movement_type = weighted_choice(self.movement_types)
            
            # Determine quantity for this movement
            max_qty = min(remaining_items, int(items_moved * 0.5))
            qty = random.randint(1, max_qty)
            
            # Determine price based on movement type
            if movement_type == 'sale':
                price = batch['current_price']
                discount = None
                if batch['current_price'] < batch['original_price']:
                    discount = round((1 - batch['current_price'] / batch['original_price']) * 100, 2)
                reason = None
                reference_id = f"SALE-{generate_uuid()}"
            
            elif movement_type in ['waste_expired', 'waste_damaged']:
                price = batch['cost_per_unit']  # Use cost for waste calculations
                discount = None
                reason = 'expired' if movement_type == 'waste_expired' else 'damaged'
                reference_id = f"WASTE-{generate_uuid()}"
            
            elif movement_type == 'return':
                price = batch['current_price']
                discount = None
                reason = random.choice(['customer_dissatisfied', 'quality_issue', 'wrong_item'])
                reference_id = f"RETURN-{generate_uuid()}"
            
            elif movement_type == 'adjustment':
                price = batch['cost_per_unit']
                discount = None
                reason = random.choice(['inventory_count', 'system_adjustment', 'quality_control'])
                reference_id = f"ADJ-{generate_uuid()}"
            
            else:  # markdown
                old_price = batch['current_price']
                price = old_price * 0.7  # 30% markdown
                discount = 30.0
                reason = 'price_reduction'
                reference_id = f"MARK-{generate_uuid()}"
            
            # Create movement record
            movement = {
                "movement_id": generate_uuid(),
                "batch_id": batch['batch_id'],
                "store_id": batch['store_id'],
                "movement_type": movement_type,
                "quantity_change": -qty if movement_type in ['sale', 'waste_expired', 'waste_damaged'] else qty,
                "unit_price": round(price, 2),
                "reason": reason,
                "reference_id": reference_id,
                "movement_timestamp": datetime.combine(current_date, datetime.now().time()),
                "recorded_by": random.choice(['system', 'manager', 'employee', 'inventory_system']),
                "customer_segment": random.choice(['regular', 'member', 'new', 'online']) if movement_type == 'sale' else None,
                "discount_applied": discount
            }
            
            batch_movements.append(movement)
            remaining_items -= qty
            current_date += timedelta(days=random.randint(0, 2))
        
        return batch_movements
    
    def generate(self, start_date: date, end_date: date) -> List[Dict[str, Any]]:
        """Generate all movement records for all batches."""
        for batch in self.batches:
            batch_movements = self.generate_movements_for_batch(batch, start_date, end_date)
            self.movements.extend(batch_movements)
        
        return self.movements
    
    def get_sql(self) -> str:
        """Generate SQL insert statements for movements."""
        sql = "-- Movement Data\n"
        for movement in self.movements:
            sql += f"""INSERT INTO inventory_movements (
                movement_id, batch_id, store_id, movement_type, quantity_change,
                unit_price, movement_timestamp, discount_applied
            ) VALUES (
                '{movement['movement_id']}', '{movement['batch_id']}', '{movement['store_id']}',
                '{movement['movement_type']}', {movement['quantity_change']}, {movement['unit_price']},
                '{movement['movement_timestamp']}', {movement['discount_applied'] or 'NULL'}
                );\n"""
        return sql

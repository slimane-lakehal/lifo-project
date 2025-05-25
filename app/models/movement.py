"""
Movement model and data generation for inventory movements.
"""

from datetime import date, datetime, timedelta
from typing import Dict, List, Any, Optional
from uuid import UUID
import random

from app.utils.data_generator import generate_uuid, format_date, weighted_choice

class MovementGenerator:
    def __init__(self, batches: List[Dict], stores: List[Dict], products: List[Dict]):
        self.batches = batches
        self.stores = stores
        self.products = products
        self.movements: List[Dict[str, Any]] = []
        
        # Valid movement types from schema
        self.movement_types = ['receipt', 'sale', 'waste', 'adjustment']
    
    def generate_movements_for_batch(self, batch: Dict) -> List[Dict[str, Any]]:
        """Generate movements for a batch matching inventory_movements schema."""
        movements = []
        
        # Receipt movement (when batch was received)
        receipt_movement = {
            "movement_id": generate_uuid(),
            "store_id": batch['store_id'],
            "product_id": batch['product_id'],
            "movement_type": "receipt",
            "quantity": batch['quantity'],
            "unit_cost": batch['unit_cost'],
            "batch_id": batch['batch_id'],
            "expiration_date": batch['expiration_date'],
            "transaction_time": batch['received_date']
        }
        movements.append(receipt_movement)
        
        # Generate some sales/waste movements
        remaining_qty = batch['quantity']
        
        # Sales movements
        num_sales = random.randint(1, 5)
        for _ in range(num_sales):
            if remaining_qty <= 0:
                break
            # Ensure we have a valid range for random selection
            max_sale = max(1, int(remaining_qty * 0.3))
            sale_qty = min(remaining_qty, random.randint(1, max_sale))
            sale_price = batch['unit_cost'] * random.uniform(1.3, 2.0)  # Markup
            
            sale_movement = {
                "movement_id": generate_uuid(),
                "store_id": batch['store_id'],
                "product_id": batch['product_id'],
                "movement_type": "sale",
                "quantity": -sale_qty,  # Negative for outbound
                "unit_cost": sale_price,
                "batch_id": batch['batch_id'],
                "expiration_date": batch['expiration_date'],
                "transaction_time": (datetime.fromisoformat(batch['received_date']) + 
                                   timedelta(days=random.randint(1, 7))).isoformat()
            }
            movements.append(sale_movement)
            remaining_qty -= sale_qty
        
        # Possible waste movement
        if remaining_qty > 0 and random.random() < 0.1:  # 10% chance of waste
            waste_qty = min(remaining_qty, random.randint(1, remaining_qty))
            
            waste_movement = {
                "movement_id": generate_uuid(),
                "store_id": batch['store_id'],
                "product_id": batch['product_id'],
                "movement_type": "waste",
                "quantity": -waste_qty,  # Negative for outbound
                "unit_cost": batch['unit_cost'],
                "batch_id": batch['batch_id'],
                "expiration_date": batch['expiration_date'],
                "transaction_time": (datetime.fromisoformat(batch['received_date']) +
                                     timedelta(days=random.randint(5, 14))).isoformat()
                }
            movements.append(waste_movement)
        
        return movements
    
    def generate(self) -> List[Dict[str, Any]]:
        """Generate all movements for all batches."""
        for batch in self.batches:
            batch_movements = self.generate_movements_for_batch(batch)
            self.movements.extend(batch_movements)
        
        return self.movements
    
    def get_sql(self) -> str:
        """Generate SQL insert statements for movements."""
        sql = "-- Movement Data\n"
        for movement in self.movements:
            sql += f"""INSERT INTO inventory_movements (
                movement_id, store_id, product_id, movement_type, quantity,
                unit_cost, batch_id, expiration_date, transaction_time, created_at
            ) VALUES (
                '{movement['movement_id']}',
                '{movement['store_id']}',
                '{movement['product_id']}',
                '{movement['movement_type']}',
                {movement['quantity']},
                {movement['unit_cost']},
                '{movement['batch_id']}',
                '{movement['expiration_date']}',
                '{movement['transaction_time']}',
                '{movement['created_at']}'
            );\n"""
        return sql


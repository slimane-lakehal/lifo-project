"""
Batch model and data generation.

This module handles all batch-related operations including:
- Batch creation and validation
- Batch status management
- Price calculations and markdowns
- Expiry tracking
- Location management
"""

from datetime import datetime, date, timedelta
import random
import json
from typing import Optional, Dict, Any, List
from uuid import UUID, uuid4
from pydantic import BaseModel, Field, validator

from app.utils.data_generator import generate_uuid, random_date


class BatchGenerator:
    def __init__(self, stores: List[Dict], products: List[Dict], suppliers: List[Dict]):
        self.stores = {store['store_id']: store for store in stores}  # Create lookup dict
        self.products = products
        self.suppliers = suppliers
        self.batches: List[Dict[str, Any]] = []
    
    def generate_batch(self, store_id: str, product: Dict, current_date: date = date.today()) -> Dict[str, Any]:
        """Generate a batch matching the batches table schema."""
        store = self.stores.get(store_id)
        if not store:
            raise ValueError(f"Invalid store_id: {store_id}")
            
        supplier = random.choice(self.suppliers)
        
        # Generate realistic quantities
        if product['category'] in ['dairy', 'bakery']:
            quantity = random.randint(50, 200)
        elif product['category'] in ['meat', 'produce']:
            quantity = random.randint(20, 100)
        else:
            quantity = random.randint(10, 50)
        
        # Adjust for store type
        if store['store_type'] == 'convenience':
            quantity = max(5, int(quantity * 0.5))
        
        # Generate dates
        days_ago = random.randint(1, 14)
        received_date = current_date - timedelta(days=days_ago)
        expiration_date = received_date + timedelta(days=product['shelf_life_days'])
        
        # Generate cost
        base_cost = random.uniform(2.0, 20.0)
        if 'kg' in product['unit_size']:
            size_factor = float(product['unit_size'].replace('kg', ''))
            base_cost *= size_factor
        elif 'lb' in product['unit_size']:
            size_factor = float(product['unit_size'].replace('lb', ''))
            base_cost *= size_factor * 0.45  # Convert to kg equivalent
        
        unit_cost = round(base_cost, 2)
        
        batch = {
            "batch_id": str(uuid4()),  # Using uuid4 directly for consistency
            "store_id": store_id,
            "product_id": product['product_id'],
            "supplier_id": supplier['supplier_id'],
            "received_date": received_date.isoformat(),
            "expiration_date": expiration_date.isoformat(),
            "quantity": quantity,
            "unit_cost": unit_cost,
            "status": 'active'
        }
        
        return batch
    
    def generate(self, count: int = 100, current_date: date = date.today()) -> List[Dict[str, Any]]:
        """Generate multiple batches."""
        if not self.stores:
            raise ValueError("No stores available for batch generation")
            
        store_ids = list(self.stores.keys())
        
        for _ in range(count):
            store_id = random.choice(store_ids)
            product = random.choice(self.products)
            try:
                batch = self.generate_batch(store_id, product, current_date)
                self.batches.append(batch)
            except ValueError as e:
                logger.warning(f"Skipping batch generation: {e}")
                continue
        
        return self.batches

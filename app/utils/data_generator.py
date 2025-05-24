"""
Data generation utilities for testing and development.
"""

import random
from datetime import datetime, date, timedelta
from typing import List, Dict, Any
from uuid import uuid4

class DataGenerator:
    @staticmethod
    def generate_store_data(count: int = 5) -> List[Dict[str, Any]]:
        """Generate sample store data."""
        store_types = ['grocery', 'convenience', 'supermarket', 'specialty']
        stores = []
        
        for _ in range(count):
            store = {
                'store_id': uuid4(),
                'store_name': f'Store {random.randint(1000, 9999)}',
                'store_type': random.choice(store_types),
                'address': {
                    'street': f'{random.randint(1, 999)} Main St',
                    'city': 'Sample City',
                    'state': 'ST',
                    'zip': f'{random.randint(10000, 99999)}'
                },
                'timezone': 'UTC'
            }
            stores.append(store)
        
        return stores

    @staticmethod
    def generate_product_data(count: int = 20) -> List[Dict[str, Any]]:
        """Generate sample product data."""
        categories = ['dairy', 'meat', 'produce', 'bakery', 'dry_goods']
        storage_types = ['refrigerated', 'frozen', 'dry']
        products = []
        
        for i in range(count):
            category = random.choice(categories)
            product = {
                'product_id': uuid4(),
                'sku': f'SKU{random.randint(10000, 99999)}',
                'product_name': f'Product {i+1}',
                'category': category,
                'storage_requirements': random.choice(storage_types),
                'typical_shelf_life_days': random.randint(7, 90)
            }
            products.append(product)
        
        return products

    @staticmethod
    def generate_batch_data(
        product_id: uuid4,
        store_id: uuid4,
        count: int = 1
    ) -> List[Dict[str, Any]]:
        """Generate sample batch data for a product."""
        batches = []
        
        for _ in range(count):
            quantity = random.randint(50, 200)
            cost = random.uniform(1.0, 50.0)
            price = cost * 1.3  # 30% markup
            
            batch = {
                'batch_id': uuid4(),
                'product_id': product_id,
                'store_id': store_id,
                'initial_quantity': quantity,
                'current_quantity': quantity,
                'received_date': date.today(),
                'expiry_date': date.today() + timedelta(days=random.randint(7, 30)),
                'cost_per_unit': round(cost, 2),
                'current_price': round(price, 2),
                'original_price': round(price, 2)
            }
            batches.append(batch)
        
        return batches

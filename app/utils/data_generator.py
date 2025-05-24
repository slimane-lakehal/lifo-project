"""
Data generation utilities for testing and development.
"""

import random
import json
from datetime import datetime, date, timedelta
from typing import List, Dict, Any, Tuple, Union
from uuid import uuid4

def generate_uuid() -> str:
    """Generate a UUID string."""
    return str(uuid4())

def random_date(start_date: date, end_date: date) -> date:
    """Generate a random date between start_date and end_date."""
    time_between_dates = end_date - start_date
    days_between_dates = time_between_dates.days
    random_number_of_days = random.randrange(days_between_dates)
    return start_date + timedelta(days=random_number_of_days)

def weighted_choice(choices: List[Tuple[Any, Union[int, float]]]) -> Any:
    """Choose an item from a list of (item, weight) tuples."""
    total = sum(w for _, w in choices)
    r = random.uniform(0, total)
    upto = 0
    for choice, weight in choices:
        upto += weight
        if upto > r:
            return choice
    return choices[0][0]  # Fallback to first choice

def format_date(date_obj: date) -> str:
    """Format a date object as YYYY-MM-DD string."""
    return date_obj.strftime("%Y-%m-%d")

def get_seasonal_factor(date_obj: date, product_category: str, subcategory: str) -> float:
    """Return a seasonal multiplier (0.5-1.5) based on date and product type."""
    month = date_obj.month
    
    # Summer products (higher in summer months)
    summer_products = {
        'dairy': ['ice cream', 'yogurt drinks'],
        'produce': ['berries', 'melons', 'summer vegetables'],
        'beverages': ['soda', 'juice', 'water']
    }
    
    # Winter products (higher in winter months)
    winter_products = {
        'canned': ['soup'],
        'dry_goods': ['hot chocolate', 'tea'],
        'bakery': ['holiday treats']
    }
    
    # Check if product is seasonal
    is_summer_product = False
    is_winter_product = False
    
    if product_category in summer_products and subcategory in summer_products[product_category]:
        is_summer_product = True
    
    if product_category in winter_products and subcategory in winter_products[product_category]:
        is_winter_product = True
    
    # Summer months: 6-8
    if 6 <= month <= 8:
        if is_summer_product:
            return random.uniform(1.2, 1.5)
        elif is_winter_product:
            return random.uniform(0.5, 0.8)
    
    # Winter months: 12, 1-2
    if month == 12 or 1 <= month <= 2:
        if is_winter_product:
            return random.uniform(1.2, 1.5)
        elif is_summer_product:
            return random.uniform(0.5, 0.8)
    
    # Holiday season: November-December
    if 11 <= month <= 12:
        if product_category in ['bakery', 'meat']:
            return random.uniform(1.1, 1.3)
    
    # Default - slight randomization
    return random.uniform(0.9, 1.1)

def get_day_of_week_factor(date_obj: date, store_type: str) -> float:
    """Return a day-of-week multiplier for sales volume."""
    day_of_week = date_obj.weekday()  # 0=Monday, 6=Sunday
    
    if store_type == 'convenience':
        # Convenience stores have more consistent traffic
        if day_of_week < 5:  # Weekday
            return random.uniform(0.9, 1.1)
        else:  # Weekend
            return random.uniform(1.0, 1.2)
    else:  # Grocery and pet stores
        if day_of_week < 2:  # Monday-Tuesday
            return random.uniform(0.7, 0.9)
        elif day_of_week < 5:  # Wednesday-Thursday
            return random.uniform(0.9, 1.1)
        else:  # Friday-Sunday
            return random.uniform(1.2, 1.5)
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

"""
Product model and data generation.
"""

import random
import json
from datetime import datetime
from typing import Optional, Dict, Any, List, Tuple
from uuid import UUID, uuid4
from pydantic import BaseModel, Field

from app.utils.data_generator import generate_uuid

class ProductGenerator:
    def __init__(self):
        self.products: List[Dict[str, Any]] = []
        self.categories = {
            'dairy': {
                'subcategories': ['milk', 'yogurt', 'cheese', 'butter', 'ice cream'],
                'shelf_life': (7, 14),
                'temperature_zone': 'refrigerated',
                'unit_types': ['kg', 'lbs'],
                'brands': ['Dairy Fresh', 'Organic Valley', 'Horizon', 'Chobani', 'Tillamook']
            },
            'meat': {
                'subcategories': ['beef', 'chicken', 'pork', 'fish', 'ground meat'],
                'shelf_life': (3, 7),
                'temperature_zone': 'refrigerated',
                'unit_types': ['kg', 'lbs'],
                'brands': ['Premium Meats', 'Organic Farms', 'Butcher\'s Choice', 'Sea Harvest']
            },
            'produce': {
                'subcategories': ['fruits', 'vegetables', 'berries', 'leafy greens'],
                'shelf_life': (3, 10),
                'temperature_zone': 'refrigerated',
                'unit_types': ['kg', 'lbs', 'pieces'],
                'brands': ['Farm Fresh', 'Organic Harvest', 'Local Farms', 'Nature\'s Best']
            },
            'bakery': {
                'subcategories': ['bread', 'pastries', 'cakes', 'cookies'],
                'shelf_life': (1, 3),
                'temperature_zone': 'ambient',
                'unit_types': ['pieces'],
                'brands': ['Artisan Bakery', 'Fresh Baked', 'Morning Delights', 'Sweet Treats']
            },
            'dry_goods': {
                'subcategories': ['pasta', 'rice', 'cereal', 'canned goods', 'snacks'],
                'shelf_life': (365, 730),
                'temperature_zone': 'ambient',
                'unit_types': ['kg', 'lbs', 'pieces'],
                'brands': ['Pantry Essentials', 'Organic Staples', 'Kitchen Basics']
            },
            'frozen': {
                'subcategories': ['frozen meals', 'ice cream', 'frozen vegetables'],
                'shelf_life': (30, 90),
                'temperature_zone': 'frozen',
                'unit_types': ['kg', 'lbs', 'pieces'],
                'brands': ['Frozen Fresh', 'Quick Meals', 'Premium Frozen']
            }
        }
        
        self.unit_sizes = {
            'kg': ['0.5kg', '1kg', '2kg', '5kg'],
            'lbs': ['1lb', '2lb', '5lb', '10lb'],
            'pieces': ['1', '6', '12', '24']
        }
    
    def generate(self) -> List[Dict[str, Any]]:
        """Generate product data matching the products table schema."""
        product_id = 1000
        
        for category, info in self.categories.items():
            count = random.randint(10, 20)
            
            for _ in range(count):
                subcategory = random.choice(info['subcategories'])
                brand = random.choice(info['brands'])
                unit_type = random.choice(info['unit_types'])
                unit_size = random.choice(self.unit_sizes[unit_type])
                
                product_name = f"{brand} {subcategory.title()}"
                if unit_type != 'pieces':
                    product_name += f" {unit_size}"
                
                shelf_life = random.randint(*info['shelf_life'])
                
                product = {
                    "product_id": generate_uuid(),
                    "sku": f"P{product_id}",
                    "product_name": product_name,
                    "brand": brand,
                    "category": category,
                    "subcategory": subcategory,
                    "unit_size": unit_size,
                    "unit_type": unit_type,
                    "shelf_life_days": shelf_life,
                    "temperature_zone": info['temperature_zone']
                }
                
                self.products.append(product)
                product_id += 1
        
        return self.products
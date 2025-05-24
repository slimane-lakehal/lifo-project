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

class Product(BaseModel):
    product_id: UUID = Field(default_factory=uuid4)
    sku: str
    product_name: str
    brand: Optional[str] = None
    category: str
    subcategory: Optional[str] = None
    unit_size: Optional[str] = None
    unit_type: Optional[str] = None
    
    # Shelf life characteristics
    typical_shelf_life_days: Optional[int] = None
    storage_requirements: Optional[str] = None
    product_type: Optional[str] = None
    
    # Business rules
    discount_rules: Dict[str, Any] = Field(default_factory=dict)
    minimum_shelf_life_days: int = 1
    
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

class ProductGenerator:
    def __init__(self):
        self.products: List[Dict[str, Any]] = []
        self.categories = {
            'dairy': {
                'subcategories': ['milk', 'yogurt', 'cheese', 'butter', 'ice cream'],
                'shelf_life': (7, 14),
                'storage': 'refrigerated',
                'product_type': 'perishable',
                'unit_types': ['volume', 'weight'],
                'brands': ['Dairy Fresh', 'Organic Valley', 'Horizon', 'Chobani', 'Tillamook']
            },
            'meat': {
                'subcategories': ['beef', 'chicken', 'pork', 'fish', 'ground meat'],
                'shelf_life': (3, 7),
                'storage': 'refrigerated',
                'product_type': 'perishable',
                'unit_types': ['weight'],
                'brands': ['Premium Meats', 'Organic Farms', 'Butcher\'s Choice', 'Sea Harvest', 'Farm Fresh']
            },
            'produce': {
                'subcategories': ['fruits', 'vegetables', 'berries', 'melons', 'leafy greens', 'root vegetables', 'summer vegetables'],
                'shelf_life': (3, 10),
                'storage': 'refrigerated',
                'product_type': 'perishable',
                'unit_types': ['weight', 'count'],
                'brands': ['Farm Fresh', 'Organic Harvest', 'Local Farms', 'Nature\'s Best', 'Valley Grown']
            },
            'bakery': {
                'subcategories': ['bread', 'pastries', 'cakes', 'cookies', 'holiday treats'],
                'shelf_life': (1, 3),
                'storage': 'dry',
                'product_type': 'perishable',
                'unit_types': ['count', 'weight'],
                'brands': ['Artisan Bakery', 'Fresh Baked', 'Morning Delights', 'Sweet Treats', 'Hometown Bakery']
            },
            'dry_goods': {
                'subcategories': ['pasta', 'rice', 'cereal', 'canned goods', 'snacks', 'hot chocolate', 'tea'],
                'shelf_life': (365, 730),
                'storage': 'dry',
                'product_type': 'non_perishable',
                'unit_types': ['weight', 'count'],
                'brands': ['Pantry Essentials', 'Organic Staples', 'Kitchen Basics', 'Premium Select', 'Value Choice']
            },
            'pet_food': {
                'subcategories': ['dog food', 'cat food', 'pet treats', 'specialty pet food'],
                'shelf_life': (180, 365),
                'storage': 'dry',
                'product_type': 'semi_perishable',
                'unit_types': ['weight'],
                'brands': ['Pet Nutrition', 'Happy Pets', 'Natural Choice', 'Premium Pet', 'Healthy Companion']
            },
            'frozen': {
                'subcategories': ['frozen meals', 'ice cream', 'frozen vegetables', 'frozen pizza'],
                'shelf_life': (30, 90),
                'storage': 'frozen',
                'product_type': 'semi_perishable',
                'unit_types': ['weight', 'count'],
                'brands': ['Frozen Fresh', 'Quick Meals', 'Premium Frozen', 'Frosty Delights', 'Frozen Harvest']
            },
            'beverages': {
                'subcategories': ['soda', 'juice', 'water', 'coffee', 'tea', 'energy drinks'],
                'shelf_life': (90, 365),
                'storage': 'dry',
                'product_type': 'semi_perishable',
                'unit_types': ['volume', 'count'],
                'brands': ['Refreshing Drinks', 'Natural Beverages', 'Thirst Quencher', 'Premium Drinks', 'Hydration Plus']
            }
        }
        
        # Product counts per category
        self.category_counts = {
            'dairy': (15, 20),
            'meat': (20, 25),
            'produce': (25, 30),
            'bakery': (10, 15),
            'dry_goods': (15, 20),
            'pet_food': (15, 20),
            'frozen': (10, 15),
            'beverages': (10, 15)
        }
        
        # Unit sizes by unit type
        self.unit_sizes = {
            'weight': ['100g', '250g', '500g', '1kg', '2kg', '5kg'],
            'volume': ['100ml', '250ml', '500ml', '1L', '2L'],
            'count': ['1-pack', '4-pack', '6-pack', '12-pack', '24-pack']
        }
    
    def _generate_product_name(self, category: str, subcategory: str) -> str:
        """Generate a product name based on category and subcategory."""
        if subcategory in ['milk', 'yogurt']:
            variants = ['Whole', '2%', 'Skim', 'Organic', 'Lactose-Free']
            return f"{random.choice(variants)} {subcategory.title()}"
        elif subcategory == 'cheese':
            cheese_types = ['Cheddar', 'Swiss', 'Mozzarella', 'Parmesan', 'Gouda', 'Brie']
            return f"{random.choice(cheese_types)} Cheese"
        elif category == 'produce':
            if subcategory == 'fruits':
                fruits = ['Apples', 'Oranges', 'Bananas', 'Pears', 'Peaches']
                return random.choice(fruits)
            elif subcategory == 'vegetables':
                vegetables = ['Carrots', 'Broccoli', 'Cauliflower', 'Bell Peppers', 'Onions']
                return random.choice(vegetables)
            elif subcategory == 'berries':
                berries = ['Strawberries', 'Blueberries', 'Raspberries', 'Blackberries']
                return random.choice(berries)
            elif subcategory == 'leafy greens':
                greens = ['Spinach', 'Kale', 'Lettuce', 'Arugula', 'Mixed Greens']
                return random.choice(greens)
        return f"{subcategory.title()}"

    def _generate_discount_rules(self, category: str) -> Dict[str, Any]:
        """Generate discount rules based on product category."""
        if category in ['dairy', 'meat', 'produce', 'bakery']:
            return {
                "days_until_expiry": [
                    {"days": 1, "discount": 0.5},
                    {"days": 2, "discount": 0.3},
                    {"days": 3, "discount": 0.2}
                ]
            }
        else:
            return {
                "days_until_expiry": [
                    {"days": 7, "discount": 0.3},
                    {"days": 14, "discount": 0.2},
                    {"days": 30, "discount": 0.1}
                ]
            }

    def generate(self) -> List[Dict[str, Any]]:
        """Generate sample product data."""
        product_id = 1000  # Starting SKU number
        
        for category, count_range in self.category_counts.items():
            category_info = self.categories[category]
            count = random.randint(*count_range)
            
            for _ in range(count):
                subcategory = random.choice(category_info['subcategories'])
                brand = random.choice(category_info['brands'])
                unit_type = random.choice(category_info['unit_types'])
                unit_size = random.choice(self.unit_sizes[unit_type])
                
                # Create product name
                product_name = self._generate_product_name(category, subcategory)
                
                # Add unit size to name for certain categories
                if category in ['dairy', 'beverages']:
                    product_name = f"{product_name} {unit_size}"
                
                # Generate shelf life with some variation
                base_shelf_life = random.randint(*category_info['shelf_life'])
                shelf_life = max(1, int(base_shelf_life * random.uniform(0.9, 1.1)))
                
                # Generate minimum shelf life requirement
                if category in ['dairy', 'meat', 'produce']:
                    min_shelf_life = max(1, int(shelf_life * 0.2))  # 20% of typical shelf life
                elif category == 'bakery':
                    min_shelf_life = 1  # Bakery items need at least 1 day
                else:
                    min_shelf_life = max(1, int(shelf_life * 0.1))  # 10% of typical shelf life
                
                product = {
                    "product_id": generate_uuid(),
                    "sku": f"P{product_id}",
                    "product_name": product_name,
                    "brand": brand,
                    "category": category,
                    "subcategory": subcategory,
                    "unit_size": unit_size,
                    "unit_type": unit_type,
                    "typical_shelf_life_days": shelf_life,
                    "storage_requirements": category_info['storage'],
                    "product_type": category_info['product_type'],
                    "discount_rules": json.dumps(self._generate_discount_rules(category)),
                    "minimum_shelf_life_days": min_shelf_life
                }
                
                self.products.append(product)
                product_id += 1
        
        return self.products
    
    def get_sql(self) -> str:
        """Generate SQL insert statements for products."""
        sql = "-- Product Data\n"
        for product in self.products:
            sql += f"""INSERT INTO products (
                product_id, sku, product_name, brand, category, subcategory, 
                unit_size, unit_type, typical_shelf_life_days, storage_requirements, 
                product_type, discount_rules, minimum_shelf_life_days
            ) VALUES (
                '{product['product_id']}', '{product['sku']}', '{product['product_name']}', 
                '{product['brand']}', '{product['category']}', '{product['subcategory']}', 
                '{product['unit_size']}', '{product['unit_type']}', {product['typical_shelf_life_days']}, 
                '{product['storage_requirements']}', '{product['product_type']}', 
                '{product['discount_rules']}', {product['minimum_shelf_life_days']}
                );\n"""
        return sql

"""
LIFO Food Waste Platform initialization and database setup.
Handles database initialization and synthetic data generation.
"""

import asyncio
from datetime import timedelta, date
import random
import uuid
import json

from app.database.connection import DatabaseConnection
from app.utils.data_generator import DataGenerator

# Configuration
START_DATE = date(2023, 1, 1)  # Base date for historical data
END_DATE = date(2023, 3, 1)    # Current date for the simulation
DAYS_OF_HISTORY = (END_DATE - START_DATE).days

# Preserve existing helper functions
def generate_uuid():
    return str(uuid.uuid4())

def random_date(start_date, end_date):
    time_between_dates = end_date - start_date
    days_between_dates = time_between_dates.days
    random_number_of_days = random.randrange(days_between_dates)
    return start_date + timedelta(days=random_number_of_days)

def weighted_choice(choices):
    total = sum(w for _, w in choices)
    r = random.uniform(0, total)
    upto = 0
    for choice, weight in choices:
        upto += weight
        if upto > r:
            return choice
    return choices[0][0]  # Fallback to first choice

def format_date(date_obj):
    return date_obj.strftime("%Y-%m-%d")

def get_seasonal_factor(date_obj, product_category, subcategory):
    """Return a seasonal multiplier (0.5-1.5) based on date and product type"""
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

def get_day_of_week_factor(date_obj, store_type):
    """Return a day-of-week multiplier for sales volume"""
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

# Data generation classes
class StoreGenerator:
    def __init__(self):
        self.stores = []
        self.store_types = ['grocery', 'pet_food', 'convenience']
        self.store_names = {
            'grocery': ["Fresh Market", "Organic Grocer", "Family Foods", "City Market", "Neighborhood Grocery"],
            'pet_food': ["PetCo Supplies", "Animal Nutrition", "Pet Pantry", "Furry Friends Food", "Pet Provisions"],
            'convenience': ["QuickStop", "Corner Market", "Express Mart", "24/7 Shop", "Mini Mart"]
        }
        self.locations = [
            {"city": "Seattle", "state": "WA", "zip": "98101", "timezone": "America/Los_Angeles"},
            {"city": "Portland", "state": "OR", "zip": "97201", "timezone": "America/Los_Angeles"},
            {"city": "San Francisco", "state": "CA", "zip": "94105", "timezone": "America/Los_Angeles"},
            {"city": "Denver", "state": "CO", "zip": "80202", "timezone": "America/Denver"},
            {"city": "Chicago", "state": "IL", "zip": "60601", "timezone": "America/Chicago"},
            {"city": "New York", "state": "NY", "zip": "10001", "timezone": "America/New_York"},
            {"city": "Boston", "state": "MA", "zip": "02108", "timezone": "America/New_York"},
            {"city": "Miami", "state": "FL", "zip": "33101", "timezone": "America/New_York"}
        ]
    
    def generate(self, count=5):
        for i in range(count):
            store_type = random.choice(self.store_types)
            location = random.choice(self.locations)
            
            # Create a more specific name based on location
            base_name = random.choice(self.store_names[store_type])
            store_name = f"{base_name} {location['city']}"
            
            store_id = generate_uuid()
            
            address = {
                "street": f"{random.randint(100, 999)} {random.choice(['Main', 'Oak', 'Maple', 'Pine', 'Cedar'])} St",
                "city": location['city'],
                "state": location['state'],
                "zip": location['zip'],
                "country": "USA"
            }
            
            store = {
                "store_id": store_id,
                "store_name": store_name,
                "store_type": store_type,
                "address": json.dumps(address),
                "timezone": location['timezone']
            }
            
            self.stores.append(store)
        
        return self.stores
    
    def get_sql(self):
        sql = "-- Store Data\n"
        for store in self.stores:
            sql += f"""INSERT INTO stores (store_id, store_name, store_type, address, timezone)
VALUES ('{store['store_id']}', '{store['store_name']}', '{store['store_type']}', '{store['address']}', '{store['timezone']}');\n"""
        return sql

class ProductGenerator:
    def __init__(self):
        self.products = []
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
    
    def generate(self):
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
                if subcategory in ['milk', 'yogurt']:
                    variants = ['Whole', '2%', 'Skim', 'Organic', 'Lactose-Free']
                    product_name = f"{random.choice(variants)} {subcategory.title()}"
                elif subcategory == 'cheese':
                    cheese_types = ['Cheddar', 'Swiss', 'Mozzarella', 'Parmesan', 'Gouda', 'Brie']
                    product_name = f"{random.choice(cheese_types)} Cheese"
                elif category == 'produce':
                    if subcategory == 'fruits':
                        fruits = ['Apples', 'Oranges', 'Bananas', 'Pears', 'Peaches']
                        product_name = random.choice(fruits)
                    elif subcategory == 'vegetables':
                        vegetables = ['Carrots', 'Broccoli', 'Cauliflower', 'Bell Peppers', 'Onions']
                        product_name = random.choice(vegetables)
                    elif subcategory == 'berries':
                        berries = ['Strawberries', 'Blueberries', 'Raspberries', 'Blackberries']
                        product_name = random.choice(berries)
                    elif subcategory == 'leafy greens':
                        greens = ['Spinach', 'Kale', 'Lettuce', 'Arugula', 'Mixed Greens']
                        product_name = random.choice(greens)
                    else:
                        product_name = subcategory.title()
                else:
                    product_name = f"{brand} {subcategory.title()}"
                
                # Add unit size to name for certain categories
                if category in ['dairy', 'beverages']:
                    product_name = f"{product_name} {unit_size}"
                
                # Generate shelf life with some variation
                base_shelf_life = random.randint(*category_info['shelf_life'])
                shelf_life = max(1, int(base_shelf_life * random.uniform(0.9, 1.1)))
                
                # Generate discount rules based on category
                if category in ['dairy', 'meat', 'produce', 'bakery']:
                    # Perishables get steeper discounts as they approach expiry
                    discount_rules = {
                        "days_until_expiry": [
                            {"days": 1, "discount": 0.5},
                            {"days": 2, "discount": 0.3},
                            {"days": 3, "discount": 0.2}
                        ]
                    }
                else:
                    # Non-perishables get milder discounts
                    discount_rules = {
                        "days_until_expiry": [
                            {"days": 7, "discount": 0.3},
                            {"days": 14, "discount": 0.2},
                            {"days": 30, "discount": 0.1}
                        ]
                    }
                
                # Generate minimum shelf life requirement
                if category in ['dairy', 'meat', 'produce']:
                    min_shelf_life = max(1, int(shelf_life * 0.2))  # 20% of typical shelf life
                elif category == 'bakery':
                    min_shelf_life = 1  # Bakery items need at least 1 day
                else:
                    min_shelf_life = max(1, int(shelf_life * 0.1))  # 10% of typical shelf life
                
                # Create product
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
                    "discount_rules": json.dumps(discount_rules),
                    "minimum_shelf_life_days": min_shelf_life
                }
                
                self.products.append(product)
                product_id += 1
        
        return self.products
    
    def get_sql(self):
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

class SupplierGenerator:
    def __init__(self):
        self.suppliers = []
        self.supplier_types = [
            {
                'type': 'local_farm',
                'name_format': '{} Family Farms',
                'first_names': ['Johnson', 'Smith', 'Garcia', 'Wilson', 'Chen', 'Martinez'],
                'reliability': (0.85, 0.95),
                'lead_time': (1, 2)
            },
            {
                'type': 'regional_distributor',
                'name_format': '{} Regional Foods',
                'first_names': ['Pacific', 'Mountain', 'Midwest', 'Southern', 'Eastern', 'Northwest'],
                'reliability': (0.80, 0.90),
                'lead_time': (2, 4)
            },
            {
                'type': 'national_brand',
                'name_format': '{} National Brands',
                'first_names': ['American', 'United', 'National', 'Premium', 'Quality', 'Standard'],
                'reliability': (0.75, 0.85),
                'lead_time': (3, 7)
            },
            {
                'type': 'specialty_supplier',
                'name_format': '{} Specialty Foods',
                'first_names': ['Organic', 'Gourmet', 'Artisan', 'Premium', 'Select', 'Natural'],
                'reliability': (0.80, 0.95),
                'lead_time': (3, 5)
            }
        ]
    
    def generate(self, count=10):
        for i in range(count):
            supplier_type = random.choice(self.supplier_types)
            first_name = random.choice(supplier_type['first_names'])
            supplier_name = supplier_type['name_format'].format(first_name)
            
            # Add some uniqueness to avoid duplicate names
            if random.random() < 0.3:
                supplier_name += f" {random.choice(['Inc.', 'LLC', 'Co.', 'Group'])}"
            
            reliability = round(random.uniform(*supplier_type['reliability']), 2)
            lead_time = random.randint(*supplier_type['lead_time'])
            
            contact_info = {
                "contact_name": f"{random.choice(['John', 'Jane', 'David', 'Sarah', 'Michael', 'Emily'])} {random.choice(['Smith', 'Johnson', 'Williams', 'Brown', 'Jones', 'Garcia'])}",
                "email": f"contact@{supplier_name.lower().replace(' ', '')}.com".replace('.', ''),
                "phone": f"555-{random.randint(100, 999)}-{random.randint(1000, 9999)}"
            }
            
            supplier = {
                "supplier_id": generate_uuid(),
                "supplier_name": supplier_name,
                "contact_info": json.dumps(contact_info),
                "default_lead_time_days": lead_time,
                "reliability_score": reliability
            }
            
            self.suppliers.append(supplier)
        
        return self.suppliers
    
    def get_sql(self):
        sql = "-- Supplier Data\n"
        for supplier in self.suppliers:
            sql += f"""INSERT INTO suppliers (
    supplier_id, supplier_name, contact_info, default_lead_time_days, reliability_score
) VALUES (
    '{supplier['supplier_id']}', '{supplier['supplier_name']}', 
    '{supplier['contact_info']}', {supplier['default_lead_time_days']}, 
    {supplier['reliability_score']}
);\n"""
        return sql

class BatchGenerator:
    def __init__(self, stores, products, suppliers):
        self.stores = stores
        self.products = products
        self.suppliers = suppliers
        self.batches = []
        
        # Map products to appropriate suppliers
        self.product_supplier_map = {}
        for product in products:
            suitable_suppliers = []
            
            # Local farms for produce
            if product['category'] == 'produce':
                suitable_suppliers.extend([s for s in suppliers if 'Family Farms' in s['supplier_name']])
            
            # Specialty suppliers for organic/premium
            if 'Organic' in product['product_name'] or 'Premium' in product['product_name']:
                suitable_suppliers.extend([s for s in suppliers if 'Specialty' in s['supplier_name']])
            
            # National brands for packaged goods
            if product['category'] in ['dry_goods', 'pet_food', 'beverages']:
                suitable_suppliers.extend([s for s in suppliers if 'National' in s['supplier_name']])
            
            # Regional distributors for everything else
            if not suitable_suppliers:
                suitable_suppliers.extend([s for s in suppliers if 'Regional' in s['supplier_name']])
            
            # If still no suitable suppliers, use any supplier
            if not suitable_suppliers:
                suitable_suppliers = suppliers
            
            self.product_supplier_map[product['product_id']] = suitable_suppliers
    
    def generate_batch(self, store, product, current_date, is_problem_case=False):
        # Select appropriate supplier
        suitable_suppliers = self.product_supplier_map[product['product_id']]
        supplier = random.choice(suitable_suppliers)
        
        # Generate batch quantities based on product category and turnover
        if product['category'] in ['dairy', 'bakery'] and product['subcategory'] in ['milk', 'bread']:
            # High turnover items
            initial_quantity = random.randint(50, 200)
        elif product['category'] in ['meat', 'produce', 'dairy']:
            # Medium turnover items
            initial_quantity = random.randint(20, 100)
        else:
            # Low turnover items
            initial_quantity = random.randint(5, 50)
        
        # Adjust quantity based on store type
        if store['store_type'] == 'convenience':
            initial_quantity = max(5, int(initial_quantity * 0.5))  # Smaller quantities for convenience stores
        elif store['store_type'] == 'pet_food' and product['category'] != 'pet_food':
            initial_quantity = max(5, int(initial_quantity * 0.3))  # Much smaller for non-pet items in pet stores
        
        # Generate received date (in the past)
        if is_problem_case:
            # For problem cases, make the batch older
            days_ago = product['typical_shelf_life_days'] - random.randint(1, 3)
            received_date = current_date - timedelta(days=days_ago)
        else:
            max_days_ago = min(30, product['typical_shelf_life_days'] * 0.7)
            days_ago = random.randint(1, int(max_days_ago))
            received_date = current_date - timedelta(days=days_ago)
        
        # Generate expiry date based on shelf life
        shelf_life_variation = random.uniform(0.9, 1.1)  # ±10% variation in shelf life
        
        # Adjust shelf life based on supplier reliability
        # Less reliable suppliers might deliver products with shorter shelf life
        supplier_factor = 0.8 + (supplier['reliability_score'] * 0.2)
        
        shelf_life_days = int(product['typical_shelf_life_days'] * shelf_life_variation * supplier_factor)
        expiry_date = received_date + timedelta(days=shelf_life_days)
        
        # For problem cases, make sure they're very close to expiry
        if is_problem_case:
            days_until_expiry = random.randint(1, 3)
            expiry_date = current_date + timedelta(days=days_until_expiry)
        
        # Generate best before date (slightly before expiry for some products)
        if product['category'] in ['dairy', 'produce']:
            best_before_days = int(shelf_life_days * 0.9)
            best_before_date = received_date + timedelta(days=best_before_days)
        else:
            best_before_date = expiry_date  # Same as expiry for other products
        
        # Generate pricing
        base_cost = 0
        if product['category'] == 'meat':
            base_cost = random.uniform(5.0, 15.0)
        elif product['category'] == 'dairy':
            base_cost = random.uniform(2.0, 6.0)
        elif product['category'] == 'produce':
            base_cost = random.uniform(1.0, 4.0)
        elif product['category'] == 'bakery':
            base_cost = random.uniform(2.0, 5.0)
        elif product['category'] == 'pet_food':
            base_cost = random.uniform(8.0, 20.0)
        else:
            base_cost = random.uniform(3.0, 8.0)
        
        # Adjust cost based on unit size
        if 'kg' in product['unit_size']:
            size_factor = float(product['unit_size'].replace('kg', ''))
            base_cost *= size_factor
        elif 'g' in product['unit_size']:
            size_factor = float(product['unit_size'].replace('g', '')) / 1000
            base_cost *= size_factor
        elif 'L' in product['unit_size']:
            size_factor = float(product['unit_size'].replace('L', ''))
            base_cost *= size_factor
        elif 'ml' in product['unit_size']:
            size_factor = float(product['unit_size'].replace('ml', '')) / 1000
            base_cost *= size_factor
        elif 'pack' in product['unit_size']:
            size_factor = float(product['unit_size'].split('-')[0])
            base_cost *= size_factor / 6  # Normalize to a 6-pack
        
        # Add supplier variation to cost
        supplier_variation = random.uniform(0.9, 1.1)
        cost_per_unit = round(base_cost * supplier_variation, 3)
        
        # Calculate markup based on category
        if product['category'] == 'meat':
            markup = random.uniform(1.8, 2.5)  # Higher markup for meat
        elif product['category'] in ['produce', 'bakery']:
            markup = random.uniform(1.5, 2.0)  # Medium markup for produce and bakery
        else:
            markup = random.uniform(1.3, 1.8)  # Lower markup for other categories
        
        original_price = round(cost_per_unit * markup, 2)
        
        # Apply markdown if close to expiry
        days_until_expiry = (expiry_date - current_date).days
        current_price = original_price
        
        if days_until_expiry <= 1:
            current_price = round(original_price * 0.5, 2)  # 50% off if expiring tomorrow
        elif days_until_expiry <= 3:
            current_price = round(original_price * 0.7, 2)  # 30% off if expiring in 2-3 days
        elif days_until_expiry <= 7:
            current_price = round(original_price * 0.9, 2)  # 10% off if expiring in 4-7 days
        
        # Generate current quantity (some has been sold)
        if days_until_expiry < 0:
            # Expired batches should have 0 quantity
            current_quantity = 0
            status = 'expired'
        else:
            # Calculate how much has been sold based on days since received
            days_on_shelf = (current_date - received_date).days
            
            # Different sell-through rates based on product category
            if product['category'] in ['dairy', 'bakery'] and product['subcategory'] in ['milk', 'bread']:
                daily_sell_rate = random.uniform(0.15, 0.25)  # 15-25% daily for high turnover
            elif product['category'] in ['meat', 'produce']:
                daily_sell_rate = random.uniform(0.1, 0.2)  # 10-20% daily for medium turnover
            else:
                daily_sell_rate = random.uniform(0.05, 0.1)  # 5-10% daily for low turnover
            
            # Adjust for problem cases
            if is_problem_case:
                daily_sell_rate *= 0.5  # Problem cases sell slower
            
            # Calculate remaining quantity
            remaining_percent = max(0, 1 - (days_on_shelf * daily_sell_rate))
            current_quantity = int(initial_quantity * remaining_percent)
            
            # Status based on price and expiry
            if current_price < original_price:
                status = 'marked_down'
            else:
                status = 'active'
        
        # Generate locations
        if product['storage_requirements'] == 'refrigerated':
            storage_location = f"Cooler-{random.choice(['A', 'B', 'C'])}"
            display_location = f"Refrigerated-Section-{random.randint(1, 5)}"
        elif product['storage_requirements'] == 'frozen':
            storage_location = f"Freezer-{random.choice(['A', 'B'])}"
            display_location = f"Frozen-Section-{random.randint(1, 3)}"
        else:
            storage_location = f"Aisle-{random.randint(1, 10)}-Shelf-{random.randint(1, 5)}"
            display_location = f"Aisle-{random.randint(1, 10)}"
        
        # Generate batch codes
        supplier_lot_code = f"LOT-{random.choice(['A', 'B', 'C', 'D', 'E', 'F'])}{random.randint(1000, 9999)}"
        internal_batch_code = f"B{random.randint(10000, 99999)}"
        
        # Create batch
        batch = {
            "batch_id": generate_uuid(),
            "store_id": store['store_id'],
            "product_id": product['product_id'],
            "supplier_id": supplier['supplier_id'],
            "supplier_lot_code": supplier_lot_code,
            "internal_batch_code": internal_batch_code,
            "initial_quantity": initial_quantity,
            "current_quantity": current_quantity,
            "reserved_quantity": 0,
            "received_date": received_date,
            "expiry_date": expiry_date,
            "best_before_date": best_before_date,
            "cost_per_unit": cost_per_unit,
            "current_price": current_price,
            "original_price": original_price,
            "storage_location": storage_location,
            "display_location": display_location,
            "status": status,
            "last_movement_date": current_date - timedelta(days=random.randint(0, min(5, days_on_shelf)))
        }
        
        return batch
    
    def generate(self, count=600, current_date=END_DATE):
        # Distribute batches across stores and products
        for store in self.stores:
            # Determine which products this store carries
            if store['store_type'] == 'grocery':
                # Grocery stores carry all products
                store_products = self.products
            elif store['store_type'] == 'pet_food':
                # Pet stores primarily carry pet food, but some other items
                pet_products = [p for p in self.products if p['category'] == 'pet_food']
                other_products = [p for p in self.products if p['category'] != 'pet_food']
                store_products = pet_products + random.sample(other_products, min(20, len(other_products)))
            else:  # convenience
                # Convenience stores carry a limited selection
                high_turnover = [p for p in self.products if p['category'] in ['dairy', 'bakery', 'beverages']]
                other_products = [p for p in self.products if p['category'] not in ['dairy', 'bakery', 'beverages']]
                store_products = high_turnover + random.sample(other_products, min(30, len(other_products)))
            
            # Generate batches for this store
            store_batch_count = count // len(self.stores)
            
            # Create some problem cases (5-10% of batches)
            problem_case_count = int(store_batch_count * random.uniform(0.05, 0.1))
            
            for i in range(store_batch_count):
                is_problem_case = i < problem_case_count
                product = random.choice(store_products)
                
                # For problem cases, focus on perishable items
                if is_problem_case:
                    perishable_products = [p for p in store_products if p['category'] in ['dairy', 'meat', 'produce', 'bakery']]
                    if perishable_products:
                        product = random.choice(perishable_products)
                
                batch = self.generate_batch(store, product, current_date, is_problem_case)
                self.batches.append(batch)
        
        return self.batches
    
    def get_sql(self):
        sql = "-- Product Batch Data\n"
        for batch in self.batches:
            sql += f"""INSERT INTO product_batches (
    batch_id, store_id, product_id, supplier_id, supplier_lot_code, internal_batch_code,
    initial_quantity, current_quantity, reserved_quantity, received_date, expiry_date,
    best_before_date, cost_per_unit, current_price, original_price, storage_location,
    display_location, status, last_movement_date
) VALUES (
    '{batch['batch_id']}', '{batch['store_id']}', '{batch['product_id']}', '{batch['supplier_id']}',
    '{batch['supplier_lot_code']}', '{batch['internal_batch_code']}', {batch['initial_quantity']},
    {batch['current_quantity']}, {batch['reserved_quantity']}, '{format_date(batch['received_date'])}',
    '{format_date(batch['expiry_date'])}', '{format_date(batch['best_before_date'])}', {batch['cost_per_unit']},
    {batch['current_price']}, {batch['original_price']}, '{batch['storage_location']}',
    '{batch['display_location']}', '{batch['status']}', '{format_date(batch['last_movement_date'])}'
);\n"""
        return sql

class MovementGenerator:
    def __init__(self, batches, stores, products):
        self.batches = batches
        self.stores = stores
        self.products = products
        self.movements = []
        
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
    
    def generate_movements_for_batch(self, batch, start_date, end_date):
        product = self.product_lookup[batch['product_id']]
        
        # Skip if the batch was received after our end date
        if batch['received_date'] > end_date:
            return []
        
        # Adjust start date if batch was received after start date
        start_date = max(start_date, batch['received_date'])
        
        # Calculate how many items were sold/wasted
        items_moved = batch['initial_quantity'] - batch['current_quantity']
        
        # If nothing was moved, we might still generate some movements
        if items_moved == 0 and random.random() < 0.2:
            items_moved = random.randint(1, min(5, batch['initial_quantity']))
        
        # If still nothing moved, skip this batch
        if items_moved == 0:
            return []
        
        # Determine how many movement records to generate
        if product['category'] in ['dairy', 'bakery'] and product['subcategory'] in ['milk', 'bread']:
            # High turnover items have more frequent, smaller movements
            avg_items_per_movement = random.randint(1, 3)
        elif product['category'] in ['meat', 'produce']:
            # Medium turnover
            avg_items_per_movement = random.randint(2, 5)
        else:
            # Low turnover
            avg_items_per_movement = random.randint(3, 10)
        
        # Ensure we have at least one movement
        num_movements = max(1, items_moved // avg_items_per_movement)
        
        # Generate the movements
        batch_movements = []
        remaining_items = items_moved
        
        for i in range(num_movements):
            # For the last movement, use all remaining items
            if i == num_movements - 1:
                quantity = remaining_items
            else:
                # Otherwise, use a random portion of remaining items
                quantity = random.randint(1, max(1, remaining_items // 2))
            
            remaining_items -= quantity
            
            # Skip if we've allocated all items
            if quantity <= 0:
                continue
            
            # Determine movement date
            days_range = (end_date - start_date).days
            if days_range <= 0:
                movement_date = start_date
            else:
                days_offset = random.randint(0, days_range)
                movement_date = start_date + timedelta(days=days_offset)
            
            # Add time of day
            hour = random.randint(8, 21)  # Store hours 8am-10pm
            minute = random.randint(0, 59)
            second = random.randint(0, 59)
            movement_timestamp = datetime.datetime.combine(
                movement_date, 
                datetime.time(hour, minute, second)
            )
            
            # Adjust for day of week and time of day patterns
            day_of_week = movement_date.weekday()
            
            # Weekends have more sales
            if day_of_week >= 5:  # Saturday and Sunday
                sale_weight = 85
            else:
                sale_weight = 70
            
            # Morning hours have more dairy/breakfast sales
            if hour < 12 and product['category'] in ['dairy', 'bakery']:
                sale_weight += 10
            
            # Evening hours have more dinner item sales
            if hour >= 16 and product['category'] in ['meat', 'produce']:
                sale_weight += 10
            
            # Update movement types with adjusted weights
            movement_types = self.movement_types.copy()
            movement_types[0] = ('sale', sale_weight)
            
            # Determine movement type
            movement_type = weighted_choice(movement_types)
            
            # For expired items, use waste_expired
            if batch['expiry_date'] <= movement_date and movement_type != 'markdown':
                movement_type = 'waste_expired'
                reason = 'expired'
            elif movement_type == 'waste_expired':
                reason = 'expired'
            elif movement_type == 'waste_damaged':
                reason = random.choice(['damaged', 'spoiled', 'contaminated', 'packaging_issue'])
            elif movement_type == 'return':
                reason = random.choice(['customer_return', 'quality_issue', 'recall'])
            elif movement_type == 'adjustment':
                reason = random.choice(['inventory_count', 'system_correction', 'transfer'])
            elif movement_type == 'markdown':
                reason = 'approaching_expiry'
            else:  # sale
                reason = None
            
            # Determine price
            if movement_date < batch['received_date'] + timedelta(days=3):
                # First 3 days, use original price
                unit_price = batch['original_price']
            else:
                # After that, might use current price (which could be marked down)
                unit_price = batch['current_price']
            
            # For sales, sometimes apply additional discount
            discount_applied = 0
            if movement_type == 'sale':
                # 10% chance of additional discount
                if random.random() < 0.1:
                    discount_applied = random.choice([5, 10, 15, 20])
                    unit_price = round(unit_price * (1 - discount_applied / 100), 2)
            
            # Quantity is negative for outbound movements
            if movement_type in ['sale', 'waste_expired', 'waste_damaged', 'return']:
                quantity_change = -quantity
            else:
                quantity_change = quantity
            
            # Generate reference ID
            if movement_type == 'sale':
                reference_id = f"SALE-{random.randint(10000, 99999)}"
            elif movement_type.startswith('waste'):
                reference_id = f"WASTE-{random.randint(10000, 99999)}"
            elif movement_type == 'return':
                reference_id = f"RET-{random.randint(10000, 99999)}"
            elif movement_type == 'adjustment':
                reference_id = f"ADJ-{random.randint(10000, 99999)}"
            else:  # markdown
                reference_id = f"MARK-{random.randint(10000, 99999)}"
            
            # Create movement record
            movement = {
                "movement_id": generate_uuid(),
                "batch_id": batch['batch_id'],
                "store_id": batch['store_id'],
                "movement_type": movement_type,
                "quantity_change": quantity_change,
                "unit_price": unit_price,
                "reason": reason,
                "reference_id": reference_id,
                "movement_timestamp": movement_timestamp,
                "recorded_by": random.choice(['system', 'manager', 'employee', 'inventory_system']),
                "customer_segment": random.choice(['regular', 'member', 'new', 'online']) if movement_type == 'sale' else None,
                "discount_applied": discount_applied
            }
            
            batch_movements.append(movement)
        
        return batch_movements
    
    def generate(self, start_date=START_DATE, end_date=END_DATE):
        for batch in self.batches:
            batch_movements = self.generate_movements_for_batch(batch, start_date, end_date)
            self.movements.extend(batch_movements)
        
        return self.movements
    
    def get_sql(self):
        sql = "-- Inventory Movement Data\n"
        for movement in self.movements:
            # Format timestamp for PostgreSQL
            timestamp = movement['movement_timestamp'].strftime("%Y-%m-%d %H:%M:%S")
            
            # Handle NULL values
            reason = f"'{movement['reason']}'" if movement['reason'] else "NULL"
            customer_segment = f"'{movement['customer_segment']}'" if movement['customer_segment'] else "NULL"
            
            sql += f"""INSERT INTO inventory_movements (
    movement_id, batch_id, store_id, movement_type, quantity_change, unit_price,
    reason, reference_id, movement_timestamp, recorded_by, customer_segment, discount_applied
) VALUES (
    '{movement['movement_id']}', '{movement['batch_id']}', '{movement['store_id']}',
    '{movement['movement_type']}', {movement['quantity_change']}, {movement['unit_price']},
    {reason}, '{movement['reference_id']}', '{timestamp}',
    '{movement['recorded_by']}', {customer_segment}, {movement['discount_applied']}
);\n"""
        return sql

class ScoreGenerator:
    def __init__(self, batches, stores, products):
        self.batches = batches
        self.stores = stores
        self.products = products
        self.scores = []
        
        # Create product lookup for quick access
        self.product_lookup = {p['product_id']: p for p in products}
    
    def calculate_urgency_score(self, days_until_expiry, product_category):
        """Calculate urgency score based on days until expiry and product category"""
        if days_until_expiry <= 0:
            return 100  # Already expired
        
        if product_category in ['dairy', 'meat', 'produce']:
            # Perishables have higher urgency
            return max(0, 100 - (days_until_expiry * 15))
        elif product_category == 'bakery':
            # Bakery items have highest urgency
            return max(0, 100 - (days_until_expiry * 25))
        else:
            # Other items have lower urgency
            return max(0, 100 - (days_until_expiry * 10))
    
    def calculate_economic_risk_score(self, current_quantity, current_price, days_until_expiry, product_category):
        """Calculate economic risk based on value and likelihood of waste"""
        value_at_risk = current_quantity * current_price
        
        # Base score on value
        if value_at_risk > 500:
            base_score = 90
        elif value_at_risk > 200:
            base_score = 75
        elif value_at_risk > 100:
            base_score = 60
        elif value_at_risk > 50:
            base_score = 45
        elif value_at_risk > 20:
            base_score = 30
        else:
            base_score = 15
        
        # Adjust for days until expiry
        if days_until_expiry <= 1:
            expiry_factor = 1.2
        elif days_until_expiry <= 3:
            expiry_factor = 1.1
        elif days_until_expiry <= 7:
            expiry_factor = 1.0
        else:
            expiry_factor = 0.8
        
        # Adjust for product category
        if product_category in ['meat', 'seafood']:
            category_factor = 1.2  # Higher value items
        elif product_category in ['dairy', 'produce']:
            category_factor = 1.1  # Medium value items
        else:
            category_factor = 1.0  # Standard value
        
        score = base_score * expiry_factor * category_factor
        return min(100, score)
    
    def calculate_velocity_score(self, initial_quantity, current_quantity, days_on_shelf, product_category):
        """Calculate velocity score based on how quickly the product is selling"""
        if days_on_shelf <= 0:
            return 50  # Default for new items
        
        sold_quantity = initial_quantity - current_quantity
        daily_sell_rate = sold_quantity / days_on_shelf
        
        # Expected daily sell rates by category
        if product_category in ['dairy', 'bakery'] and product_category in ['milk', 'bread']:
            expected_rate = initial_quantity * 0.2  # 20% daily for high turnover
        elif product_category in ['meat', 'produce']:
            expected_rate = initial_quantity * 0.15  # 15% daily for medium turnover
        else:
            expected_rate = initial_quantity * 0.1  # 10% daily for low turnover
        
        # Score based on actual vs expected
        if expected_rate == 0:
            velocity_ratio = 1  # Avoid division by zero
        else:
            velocity_ratio = daily_sell_rate / expected_rate
        
        if velocity_ratio >= 1.5:
            return 90  # Selling much faster than expected
        elif velocity_ratio >= 1.0:
            return 75  # Selling as expected or slightly faster
        elif velocity_ratio >= 0.7:
            return 60  # Selling a bit slower than expected
        elif velocity_ratio >= 0.4:
            return 40  # Selling much slower than expected
        else:
            return 20  # Barely selling
    
    def generate_score(self, batch, current_date):
        product = self.product_lookup[batch['product_id']]
        
        # Calculate days until expiry
        days_until_expiry = (batch['expiry_date'] - current_date).days
        
        # Calculate days on shelf
        days_on_shelf = (current_date - batch['received_date']).days
        
        # Calculate scores
        urgency_score = self.calculate_urgency_score(days_until_expiry, product['category'])
        economic_risk_score = self.calculate_economic_risk_score(
            batch['current_quantity'], 
            batch['current_price'], 
            days_until_expiry, 
            product['category']
        )
        velocity_score = self.calculate_velocity_score(
            batch['initial_quantity'], 
            batch['current_quantity'], 
            days_on_shelf, 
            product['category']
        )
        
        # Calculate composite score (weighted average)
        composite_score = (urgency_score * 0.4) + (economic_risk_score * 0.4) + (velocity_score * 0.2)
        
        # Determine recommended action
        if urgency_score >= 90:
            recommended_action = 'immediate_markdown'
            suggested_discount = 50
        elif urgency_score >= 70:
            recommended_action = 'mark_down'
            suggested_discount = 30
        elif urgency_score >= 50:
            recommended_action = 'display_prominently'
            suggested_discount = 20
        elif velocity_score <= 30:
            recommended_action = 'promotional_bundle'
            suggested_discount = 15
        else:
            recommended_action = 'monitor'
            suggested_discount = 0
        
        # Calculate waste predictions
        if days_until_expiry <= 0:
            predicted_waste_quantity = batch['current_quantity']
            confidence_level = 0.95
        elif days_until_expiry <= 3:
            if product['category'] in ['bakery', 'produce']:
                waste_percent = random.uniform(0.7, 0.9)
            elif product['category'] in ['dairy', 'meat']:
                waste_percent = random.uniform(0.5, 0.7)
            else:
                waste_percent = random.uniform(0.3, 0.5)
            
            predicted_waste_quantity = int(batch['current_quantity'] * waste_percent)
            confidence_level = random.uniform(0.8, 0.9)
        elif days_until_expiry <= 7:
            if product['category'] in ['bakery', 'produce']:
                waste_percent = random.uniform(0.4, 0.6)
            elif product['category'] in ['dairy', 'meat']:
                waste_percent = random.uniform(0.2, 0.4)
            else:
                waste_percent = random.uniform(0.1, 0.2)
            
            predicted_waste_quantity = int(batch['current_quantity'] * waste_percent)
            confidence_level = random.uniform(0.7, 0.8)
        else:
            waste_percent = random.uniform(0.05, 0.15)
            predicted_waste_quantity = int(batch['current_quantity'] * waste_percent)
            confidence_level = random.uniform(0.6, 0.7)
        
        # Calculate revenue at risk
        predicted_waste_value = round(predicted_waste_quantity * batch['current_price'], 2)
        revenue_at_risk = round(batch['current_quantity'] * batch['current_price'], 2)
        
        # Create score record
        score = {
            "score_id": generate_uuid(),
            "batch_id": batch['batch_id'],
            "store_id": batch['store_id'],
            "urgency_score": round(urgency_score, 2),
            "economic_risk_score": round(economic_risk_score, 2),
            "velocity_score": round(velocity_score, 2),
            "composite_score": round(composite_score, 2),
            "days_until_expiry": days_until_expiry,
            "revenue_at_risk": revenue_at_risk,
            "recommended_action": recommended_action,
            "suggested_discount_percent": suggested_discount,
            "predicted_waste_quantity": predicted_waste_quantity,
            "predicted_waste_value": predicted_waste_value,
            "confidence_level": round(confidence_level, 2),
            "scored_at": current_date,
            "valid_until": current_date + timedelta(days=1)  # Scores valid for 1 day
        }
        
        return score
    
    def generate(self, current_date=END_DATE):
        for batch in self.batches:
            # Only generate scores for active batches with quantity > 0
            if batch['status'] == 'active' and batch['current_quantity'] > 0:
                score = self.generate_score(batch, current_date)
                self.scores.append(score)
        
        return self.scores
    
    def get_sql(self):
        sql = "-- Batch Score Data\n"
        for score in self.scores:
            sql += f"""INSERT INTO batch_scores (
    score_id, batch_id, store_id, urgency_score, economic_risk_score, velocity_score,
    composite_score, days_until_expiry, revenue_at_risk, recommended_action,
    suggested_discount_percent, predicted_waste_quantity, predicted_waste_value,
    confidence_level, scored_at, valid_until
) VALUES (
    '{score['score_id']}', '{score['batch_id']}', '{score['store_id']}',
    {score['urgency_score']}, {score['economic_risk_score']}, {score['velocity_score']},
    {score['composite_score']}, {score['days_until_expiry']}, {score['revenue_at_risk']},
    '{score['recommended_action']}', {score['suggested_discount_percent']},
    {score['predicted_waste_quantity']}, {score['predicted_waste_value']},
    {score['confidence_level']}, '{format_date(score['scored_at'])}', '{format_date(score['valid_until'])}'
);\n"""
        return sql

class AlertGenerator:
    def __init__(self, batches, scores, stores, products):
        self.batches = batches
        self.scores = scores
        self.stores = stores
        self.products = products
        self.alerts = []
        
        # Create lookups for quick access
        self.batch_lookup = {b['batch_id']: b for b in batches}
        self.product_lookup = {p['product_id']: p for p in products}
        self.score_lookup = {s['batch_id']: s for s in scores}
    
    def generate_alerts(self, current_date=END_DATE):
        # Generate alerts based on scores
        for score in self.scores:
            batch = self.batch_lookup[score['batch_id']]
            product = self.product_lookup[batch['product_id']]
            
            # Determine if we should generate an alert
            generate_alert = False
            alert_type = None
            severity = None
            message = None
            
            # Expiring soon alerts
            if score['days_until_expiry'] <= 1:
                generate_alert = True
                alert_type = 'expiring_soon'
                severity = 'critical'
                message = f"CRITICAL: {product['product_name']} expires TOMORROW. {batch['current_quantity']} units at risk worth ${score['revenue_at_risk']}."
            elif score['days_until_expiry'] <= 3:
                generate_alert = True
                alert_type = 'expiring_soon'
                severity = 'high'
                message = f"URGENT: {product['product_name']} expires in {score['days_until_expiry']} days. {batch['current_quantity']} units at risk."
            
            # High waste risk alerts
            elif score['predicted_waste_quantity'] > 10 and score['predicted_waste_value'] > 100:
                generate_alert = True
                alert_type = 'high_waste_risk'
                severity = 'high'
                message = f"High waste risk: Predicted to waste {score['predicted_waste_quantity']} units of {product['product_name']} worth ${score['predicted_waste_value']}."
            elif score['predicted_waste_quantity'] > 5 and score['predicted_waste_value'] > 50:
                generate_alert = True
                alert_type = 'high_waste_risk'
                severity = 'medium'
                message = f"Waste risk: May waste {score['predicted_waste_quantity']} units of {product['product_name']} worth ${score['predicted_waste_value']}."
            
            # Pricing opportunity alerts
            elif score['velocity_score'] < 40 and batch['current_price'] == batch['original_price'] and batch['current_quantity'] > 10:
                generate_alert = True
                alert_type = 'pricing_opportunity'
                severity = 'medium'
                message = f"Slow seller: {product['product_name']} is selling slower than expected. Consider {score['suggested_discount_percent']}% discount."
            
            # Skip if no alert needed
            if not generate_alert:
                continue
            
            # Create trigger conditions
            trigger_conditions = {
                "urgency_score": score['urgency_score'],
                "days_until_expiry": score['days_until_expiry'],
                "velocity_score": score['velocity_score'],
                "current_quantity": batch['current_quantity'],
                "revenue_at_risk": score['revenue_at_risk']
            }
            
            # Create recommended actions
            recommended_actions = {
                "primary_action": score['recommended_action'],
                "suggested_discount": score['suggested_discount_percent'],
                "alternative_actions": []
            }
            
            if score['recommended_action'] == 'mark_down':
                recommended_actions['alternative_actions'].append('transfer_to_other_store')
            elif score['recommended_action'] == 'display_prominently':
                recommended_actions['alternative_actions'].append('bundle_promotion')
            
            # Create alert
            alert = {
                "alert_id": generate_uuid(),
                "store_id": batch['store_id'],
                "batch_id": batch['batch_id'],
                "alert_type": alert_type,
                "severity": severity,
                "message": message,
                "trigger_conditions": json.dumps(trigger_conditions),
                "recommended_actions": json.dumps(recommended_actions),
                "status": 'active',
                "created_at": current_date,
                "expires_at": current_date + timedelta(days=score['days_until_expiry'] + 1)
            }
            
            # Randomly acknowledge some alerts
            if random.random() < 0.3:
                alert['status'] = 'acknowledged'
                alert['acknowledged_by'] = random.choice(['store_manager', 'inventory_manager', 'system'])
                alert['acknowledged_at'] = current_date
            
            # Randomly resolve some acknowledged alerts
            if alert.get('status') == 'acknowledged' and random.random() < 0.5:
                alert['status'] = 'resolved'
                alert['resolved_at'] = current_date
            
            self.alerts.append(alert)
        
        return self.alerts
    
    def get_sql(self):
        sql = "-- Waste Alert Data\n"
        for alert in self.alerts:
            # Handle NULL values
            acknowledged_by = f"'{alert.get('acknowledged_by')}'" if alert.get('acknowledged_by') else "NULL"
            acknowledged_at = f"'{format_date(alert.get('acknowledged_at'))}'" if alert.get('acknowledged_at') else "NULL"
            resolved_at = f"'{format_date(alert.get('resolved_at'))}'" if alert.get('resolved_at') else "NULL"
            
            sql += f"""INSERT INTO waste_alerts (
    alert_id, store_id, batch_id, alert_type, severity, message,
    trigger_conditions, recommended_actions, status, acknowledged_by,
    acknowledged_at, resolved_at, created_at, expires_at
) VALUES (
    '{alert['alert_id']}', '{alert['store_id']}', '{alert['batch_id']}',
    '{alert['alert_type']}', '{alert['severity']}', '{alert['message']}',
    '{alert['trigger_conditions']}', '{alert['recommended_actions']}', '{alert['status']}',
    {acknowledged_by}, {acknowledged_at}, {resolved_at},
    '{format_date(alert['created_at'])}', '{format_date(alert['expires_at'])}'
);\n"""
        return sql

class UserGenerator:
    def __init__(self, stores):
        self.stores = stores
        self.users = []
        
        self.roles = ['store_manager', 'brand_manager', 'admin', 'inventory_specialist']
        self.first_names = ['John', 'Jane', 'Michael', 'Sarah', 'David', 'Emily', 'Robert', 'Maria', 'James', 'Lisa']
        self.last_names = ['Smith', 'Johnson', 'Williams', 'Brown', 'Jones', 'Garcia', 'Miller', 'Davis', 'Rodriguez', 'Martinez']
    
    def generate(self, count=15):
        # Create admin user
        admin_user = {
            "user_id": generate_uuid(),
            "username": "admin",
            "email": "admin@lifofoodwaste.com",
            "password_hash": "$2a$10$rM7xU0XJsHJ8MYw.75VnUeRBe/RnzTQWxqgGY9gYzOTnL6tNn2pSa",  # hashed 'admin123'
            "role": "admin",
            "store_access": json.dumps([s['store_id'] for s in self.stores]),
            "permissions": json.dumps({"full_access": True}),
            "last_login": datetime.datetime.now() - timedelta(days=random.randint(0, 5))
        }
        self.users.append(admin_user)
        
        # Create store managers (one per store)
        for store in self.stores:
            first_name = random.choice(self.first_names)
            last_name = random.choice(self.last_names)
            username = f"{first_name.lower()}.{last_name.lower()}"
            email = f"{username}@lifofoodwaste.com"
            
            store_manager = {
                "user_id": generate_uuid(),
                "username": username,
                "email": email,
                "password_hash": "$2a$10$rM7xU0XJsHJ8MYw.75VnUeRBe/RnzTQWxqgGY9gYzOTnL6tNn2pSa",  # hashed 'password123'
                "role": "store_manager",
                "store_access": json.dumps([store['store_id']]),
                "permissions": json.dumps({
                    "manage_inventory": True,
                    "approve_markdowns": True,
                    "view_reports": True,
                    "manage_users": False
                }),
                "last_login": datetime.datetime.now() - timedelta(days=random.randint(0, 10))
            }
            self.users.append(store_manager)
        
        # Create additional users with various roles
        remaining_count = count - len(self.users)
        for i in range(remaining_count):
            first_name = random.choice(self.first_names)
            last_name = random.choice(self.last_names)
            username = f"{first_name.lower()}.{last_name.lower()}{random.randint(1, 99)}"
            email = f"{username}@lifofoodwaste.com"
            role = random.choice(self.roles)
            
            # Determine store access based on role
            if role == 'admin' or role == 'brand_manager':
                # Access to all stores
                store_access = [s['store_id'] for s in self.stores]
            else:
                # Access to 1-3 random stores
                num_stores = random.randint(1, min(3, len(self.stores)))
                store_access = [s['store_id'] for s in random.sample(self.stores, num_stores)]
            
            # Determine permissions based on role
            if role == 'admin':
                permissions = {"full_access": True}
            elif role == 'store_manager':
                permissions = {
                    "manage_inventory": True,
                    "approve_markdowns": True,
                    "view_reports": True,
                    "manage_users": False
                }
            elif role == 'brand_manager':
                permissions = {
                    "manage_inventory": False,
                    "approve_markdowns": False,
                    "view_reports": True,
                    "view_analytics": True
                }
            else:  # inventory_specialist
                permissions = {
                    "manage_inventory": True,
                    "approve_markdowns": False,
                    "view_reports": True,
                    "manage_users": False
                }
            
            user = {
                "user_id": generate_uuid(),
                "username": username,
                "email": email,
                "password_hash": "$2a$10$rM7xU0XJsHJ8MYw.75VnUeRBe/RnzTQWxqgGY9gYzOTnL6tNn2pSa",  # hashed 'password123'
                "role": role,
                "store_access": json.dumps(store_access),
                "permissions": json.dumps(permissions),
                "last_login": datetime.datetime.now() - timedelta(days=random.randint(0, 30))
            }
            self.users.append(user)
        
        return self.users
    
    def get_sql(self):
        sql = "-- User Data\n"
        for user in self.users:
            # Format datetime for PostgreSQL
            last_login = user.get('last_login')
            if last_login:
                last_login = last_login.strftime("%Y-%m-%d %H:%M:%S")
                last_login = f"'{last_login}'"
            else:
                last_login = "NULL"
            
            sql += f"""INSERT INTO users (
    user_id, username, email, password_hash, role, store_access, permissions, last_login
) VALUES (
    '{user['user_id']}', '{user['username']}', '{user['email']}', '{user['password_hash']}',
    '{user['role']}', '{user['store_access']}', '{user['permissions']}', {last_login}
);\n"""
        return sql

class TurnoverHistoryGenerator:
    def __init__(self, batches, products, stores):
        self.batches = batches
        self.products = products
        self.stores = stores
        self.history = []
        
        # Create lookups
        self.product_lookup = {p['product_id']: p for p in products}
    
    def generate(self, start_date=START_DATE, end_date=END_DATE):
        # Group batches by store and product
        store_product_batches = {}
        
        for batch in self.batches:
            key = (batch['store_id'], batch['product_id'])
            if key not in store_product_batches:
                store_product_batches[key] = []
            store_product_batches[key].append(batch)
        
        # Generate weekly turnover history
        current_date = start_date
        while current_date < end_date:
            period_start = current_date
            period_end = min(current_date + timedelta(days=7), end_date)
            
            for (store_id, product_id), batches in store_product_batches.items():
                product = self.product_lookup[product_id]
                
                # Filter batches that were active during this period
                active_batches = [
                    b for b in batches 
                    if b['received_date'] <= period_end and 
                    (b['expiry_date'] >= period_start or b['status'] == 'expired')
                ]
                
                if not active_batches:
                    continue
                
                # Calculate metrics
                units_sold = 0
                units_wasted = 0
                revenue_generated = 0
                cost_of_waste = 0
                days_to_sell_list = []
                
                for batch in active_batches:
                    # Estimate sold and wasted based on initial and current quantities
                    initial_qty = batch['initial_quantity']
                    current_qty = batch['current_quantity']
                    moved_qty = initial_qty - current_qty
                    
                    # Estimate how much was sold vs wasted based on product category
                    if product['category'] in ['bakery', 'produce']:
                        waste_rate = random.uniform(0.15, 0.3)
                    elif product['category'] in ['dairy', 'meat']:
                        waste_rate = random.uniform(0.08, 0.15)
                    else:
                        waste_rate = random.uniform(0.01, 0.05)
                    
                    # Adjust waste rate for expired batches
                    if batch['status'] == 'expired':
                        waste_rate = random.uniform(0.7, 1.0)
                    
                    # Calculate sold and wasted
                    batch_wasted = int(moved_qty * waste_rate)
                    batch_sold = moved_qty - batch_wasted
                    
                    units_sold += batch_sold
                    units_wasted += batch_wasted
                    
                    # Calculate revenue and cost
                    revenue_generated += batch_sold * batch['current_price']
                    cost_of_waste += batch_wasted * batch['cost_per_unit']
                    
                    # Calculate days to sell
                    if batch_sold > 0:
                        days_on_shelf = (period_end - batch['received_date']).days
                        days_to_sell = days_on_shelf * (initial_qty / batch_sold)
                        days_to_sell_list.append(days_to_sell)
                
                # Calculate average days to sell
                if days_to_sell_list:
                    average_days_to_sell = sum(days_to_sell_list) / len(days_to_sell_list)
                else:
                    average_days_to_sell = 0
                
                # Calculate waste percentage
                total_units = units_sold + units_wasted
                if total_units > 0:
                    waste_percentage = (units_wasted / total_units) * 100
                else:
                    waste_percentage = 0
                
                # Create turnover history record
                turnover = {
                    "turnover_id": generate_uuid(),
                    "store_id": store_id,
                    "product_id": product_id,
                    "period_start": period_start,
                    "period_end": period_end,
                    "units_sold": units_sold,
                    "units_wasted": units_wasted,
                    "average_days_to_sell": round(average_days_to_sell, 2),
                    "waste_percentage": round(waste_percentage, 2),
                    "revenue_generated": round(revenue_generated, 2),
                    "cost_of_waste": round(cost_of_waste, 2)
                }
                
                self.history.append(turnover)
            
            # Move to next week
            current_date = period_end
        
        return self.history
    
    def get_sql(self):
        sql = "-- Product Turnover History Data\n"
        for turnover in self.history:
            sql += f"""INSERT INTO product_turnover_history (
    turnover_id, store_id, product_id, period_start, period_end,
    units_sold, units_wasted, average_days_to_sell, waste_percentage,
    revenue_generated, cost_of_waste
) VALUES (
    '{turnover['turnover_id']}', '{turnover['store_id']}', '{turnover['product_id']}',
    '{format_date(turnover['period_start'])}', '{format_date(turnover['period_end'])}',
    {turnover['units_sold']}, {turnover['units_wasted']}, {turnover['average_days_to_sell']},
    {turnover['waste_percentage']}, {turnover['revenue_generated']}, {turnover['cost_of_waste']}
);\n"""
        return sql

def main():
    print("Generating LIFO Food Waste Platform synthetic data...")
    
    # Generate stores
    store_gen = StoreGenerator()
    stores = store_gen.generate(count=5)
    print(f"Generated {len(stores)} stores")
    
    # Generate products
    product_gen = ProductGenerator()
    products = product_gen.generate()
    print(f"Generated {len(products)} products")
    
    # Generate suppliers
    supplier_gen = SupplierGenerator()
    suppliers = supplier_gen.generate(count=10)
    print(f"Generated {len(suppliers)} suppliers")
    
    # Generate batches
    batch_gen = BatchGenerator(stores, products, suppliers)
    batches = batch_gen.generate(count=600)
    print(f"Generated {len(batches)} product batches")
    
    # Generate inventory movements
    movement_gen = MovementGenerator(batches, stores, products)
    movements = movement_gen.generate()
    print(f"Generated {len(movements)} inventory movements")
    
    # Generate batch scores
    score_gen = ScoreGenerator(batches, stores, products)
    scores = score_gen.generate()
    print(f"Generated {len(scores)} batch scores")
    
    # Generate alerts
    alert_gen = AlertGenerator(batches, scores, stores, products)
    alerts = alert_gen.generate_alerts()
    print(f"Generated {len(alerts)} waste alerts")
    
    # Generate users
    user_gen = UserGenerator(stores)
    users = user_gen.generate()
    print(f"Generated {len(users)} users")
    
    # Generate turnover history
    turnover_gen = TurnoverHistoryGenerator(batches, products, stores)
    turnover_history = turnover_gen.generate()
    print(f"Generated {len(turnover_history)} turnover history records")
    
    # Write SQL to file
    with open(OUTPUT_FILE, 'w') as f:
        f.write("-- LIFO Food Waste Platform Synthetic Data\n")
        f.write("-- Generated on " + datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S") + "\n\n")
        
        f.write(store_gen.get_sql() + "\n")
        f.write(product_gen.get_sql() + "\n")
        f.write(supplier_gen.get_sql() + "\n")
        f.write(batch_gen.get_sql() + "\n")
        f.write(movement_gen.get_sql() + "\n")
        f.write(score_gen.get_sql() + "\n")
        f.write(alert_gen.get_sql() + "\n")
        f.write(user_gen.get_sql() + "\n")
        f.write(turnover_gen.get_sql() + "\n")
    
    print(f"SQL data written to {OUTPUT_FILE}")

if __name__ == "__main__":
    main()

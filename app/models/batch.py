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


class ProductBatch(BaseModel):
    """
    Represents a batch of products in inventory.
    
    A batch is a specific quantity of a product received at a particular time,
    with its own expiry date, pricing, and location information.
    """
    batch_id: UUID = Field(default_factory=uuid4)
    store_id: UUID
    product_id: UUID
    supplier_id: UUID
    
    # Batch identifiers
    supplier_lot_code: Optional[str] = None
    internal_batch_code: Optional[str] = None
    
    # Quantities
    initial_quantity: int
    current_quantity: int
    reserved_quantity: int = 0
    
    # Dates
    received_date: date
    expiry_date: date
    best_before_date: Optional[date] = None
    
    # Financial
    cost_per_unit: float
    current_price: float
    original_price: float
    
    # Location
    storage_location: Optional[str] = None
    display_location: Optional[str] = None
    
    # Status tracking
    status: str = 'active'
    last_movement_date: Optional[date] = None
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

    @validator('current_quantity')
    def current_quantity_must_be_valid(cls, v: int, values: Dict[str, Any]) -> int:
        """Validate that current quantity is not greater than initial quantity."""
        if 'initial_quantity' in values and v > values['initial_quantity']:
            raise ValueError('Current quantity cannot be greater than initial quantity')
        return v

    @validator('expiry_date')
    def expiry_date_must_be_after_received(cls, v: date, values: Dict[str, Any]) -> date:
        """Validate that expiry date is after received date."""
        if 'received_date' in values and v <= values['received_date']:
            raise ValueError('Expiry date must be after received date')
        return v

    @validator('current_price')
    def current_price_must_be_valid(cls, v: float, values: Dict[str, Any]) -> float:
        """Validate that current price is not higher than original price."""
        if 'original_price' in values and v > values['original_price']:
            raise ValueError('Current price cannot be higher than original price')
        return v

    @validator('status')
    def status_must_be_valid(cls, v: str) -> str:
        """Validate that status is one of the allowed values."""
        valid_statuses = ['active', 'marked_down', 'expired', 'out_of_stock', 'recalled']
        if v not in valid_statuses:
            raise ValueError(f'Status must be one of: {", ".join(valid_statuses)}')
        return v

    class Config:
        """Pydantic model configuration."""
        json_encoders = {
            UUID: str,
            datetime: lambda v: v.isoformat(),
            date: lambda v: v.isoformat()
        }


class BatchGenerator:
    """
    Generates synthetic batch data for inventory simulation.
    
    This class handles the creation of product batches with realistic:
    - Quantities based on store type and product category
    - Pricing including markdowns
    - Expiry dates and shelf life
    - Storage locations
    - Problem cases for testing waste prevention
    """
    
    def __init__(self, stores: List[Dict[str, Any]], products: List[Dict[str, Any]], suppliers: List[Dict[str, Any]]):
        """Initialize the batch generator with store, product, and supplier data."""
        self.stores = stores
        self.products = products
        self.suppliers = suppliers
        self.batches: List[Dict[str, Any]] = []
        
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

    def generate_batch(self, store: Dict[str, Any], product: Dict[str, Any], 
                      current_date: date, is_problem_case: bool = False) -> Dict[str, Any]:
        """Generate a single product batch with realistic attributes."""
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

    def generate(self, count: int = 600, current_date: date = date(2025, 5, 24)) -> List[Dict[str, Any]]:
        """Generate multiple product batches across stores."""
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

    def get_sql(self) -> str:
        """Generate SQL insert statements for batches."""
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
    {batch['current_quantity']}, {batch['reserved_quantity']}, '{batch['received_date']}',
    '{batch['expiry_date']}', '{batch['best_before_date']}', {batch['cost_per_unit']},
    {batch['current_price']}, {batch['original_price']}, '{batch['storage_location']}',
    '{batch['display_location']}', '{batch['status']}', '{batch['last_movement_date']}'
);\n"""
        return sql

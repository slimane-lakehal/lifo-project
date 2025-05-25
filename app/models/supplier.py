"""
Supplier model and data generation.
"""

import random
import json
from datetime import datetime
from typing import Optional, Dict, Any, List
from uuid import UUID, uuid4
from pydantic import BaseModel, Field

from app.utils.data_generator import generate_uuid


class SupplierGenerator:
    def __init__(self):
        self.suppliers: List[Dict[str, Any]] = []
        self.supplier_names = [
            "Johnson Family Farms", "Pacific Regional Foods", "Mountain Distributors",
            "Organic Specialty Foods", "National Food Brands", "Fresh Local Produce",
            "Premium Meat Suppliers", "Dairy Cooperative", "Bakery Wholesale"
        ]
    
    def generate(self, count: int = 10) -> List[Dict[str, Any]]:
        """Generate supplier data matching the suppliers table schema."""
        for i in range(count):
            supplier_name = random.choice(self.supplier_names)
            if i > 0:  # Add variation to avoid duplicates
                supplier_name += f" {random.choice(['Inc.', 'LLC', 'Co.', 'Group'])}"
            
            contact_info = {
                "contact_name": f"{random.choice(['John', 'Jane', 'David', 'Sarah'])} {random.choice(['Smith', 'Johnson', 'Williams', 'Brown'])}",
                "email": f"contact@{supplier_name.lower().replace(' ', '').replace('.', '')}.com",
                "phone": f"555-{random.randint(100, 999)}-{random.randint(1000, 9999)}"
            }
            
            supplier = {
                "supplier_id": generate_uuid(),
                "supplier_name": supplier_name,
                "contact_info": json.dumps(contact_info)  # JSONB field
            }
            
            self.suppliers.append(supplier)
        
        return self.suppliers
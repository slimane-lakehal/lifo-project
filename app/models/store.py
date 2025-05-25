"""
Store model and data generation.
"""

import random
import json
from datetime import datetime
from typing import Dict, List, Any, Optional
from uuid import UUID, uuid4
from pydantic import BaseModel, Field

from app.utils.data_generator import generate_uuid

class StoreGenerator:
    def __init__(self):
        self.stores: List[Dict[str, Any]] = []
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
        ]
    
    def generate(self, count: int = 5) -> List[Dict[str, Any]]:
        """Generate store data matching the stores table schema."""
        for i in range(count):
            store_type = random.choice(self.store_types)
            location = random.choice(self.locations)
            
            base_name = random.choice(self.store_names[store_type])
            store_name = f"{base_name} {location['city']}"
            
            address = {
                "street": f"{random.randint(100, 999)} {random.choice(['Main', 'Oak', 'Maple', 'Pine', 'Cedar'])} St",
                "city": location['city'],
                "state": location['state'],
                "zip": location['zip'],
                "country": "USA"
            }
            store = {
            "store_id": str(uuid4()),  # Using uuid4 directly to ensure consistent UUID generation
            "store_name": store_name,
            "store_type": store_type,
            "address": json.dumps(address),  # JSONB field
            "timezone": location['timezone']
            }
            
            self.stores.append(store)
        
        return self.stores

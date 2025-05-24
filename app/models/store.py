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

class Store(BaseModel):
    store_id: UUID = Field(default_factory=uuid4)
    store_name: str
    store_type: str
    address: Dict[str, str]
    timezone: str = Field(default="UTC")
    store_name: str
    store_type: str
    address: Dict[str, Any]
    timezone: str = 'UTC'
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

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
            {"city": "New York", "state": "NY", "zip": "10001", "timezone": "America/New_York"},
            {"city": "Boston", "state": "MA", "zip": "02108", "timezone": "America/New_York"},
            {"city": "Miami", "state": "FL", "zip": "33101", "timezone": "America/New_York"}
        ]
    
    def generate(self, count: int = 5) -> List[Dict[str, Any]]:
        """Generate sample store data."""
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
    
    def get_sql(self) -> str:
        """Generate SQL insert statements for stores."""
        sql = "-- Store Data\n"
        for store in self.stores:
            sql += f"""INSERT INTO stores (store_id, store_name, store_type, address, timezone)
            VALUES ('{store['store_id']}', '{store['store_name']}', '{store['store_type']}', '{store['address']}', '{store['timezone']}');\n"""
        return sql

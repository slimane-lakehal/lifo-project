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

class Supplier(BaseModel):
    supplier_id: UUID = Field(default_factory=uuid4)
    supplier_name: str
    contact_info: Dict[str, Any] = Field(default_factory=dict)
    default_lead_time_days: Optional[int] = None
    reliability_score: Optional[float] = None
    created_at: datetime = Field(default_factory=datetime.now)

class SupplierGenerator:
    def __init__(self):
        self.suppliers: List[Dict[str, Any]] = []
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
    
    def generate(self, count: int = 10) -> List[Dict[str, Any]]:
        """Generate sample supplier data."""
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
    
    def get_sql(self) -> str:
        """Generate SQL insert statements for suppliers."""
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

"""
Product model and database operations.
"""

from datetime import datetime
from typing import Optional, Dict, Any
from uuid import UUID, uuid4
from pydantic import BaseModel, Field

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
    discount_rules: Optional[Dict[str, Any]] = None
    minimum_shelf_life_days: int = 1
    
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

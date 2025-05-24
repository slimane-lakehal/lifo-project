"""
ProductBatch model and database operations.
"""

from datetime import datetime, date
from typing import Optional, Dict, Any
from uuid import UUID, uuid4
from pydantic import BaseModel, Field

class ProductBatch(BaseModel):
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

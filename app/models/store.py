"""
Store model and database operations.
"""

from datetime import datetime
from typing import Optional, Dict, Any
from uuid import UUID, uuid4
from pydantic import BaseModel

class Store(BaseModel):
    store_id: UUID = Field(default_factory=uuid4)
    store_name: str
    store_type: str
    address: Dict[str, Any]
    timezone: str = 'UTC'
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

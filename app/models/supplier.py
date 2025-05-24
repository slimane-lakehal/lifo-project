"""
Supplier model and database operations.
"""

from datetime import datetime
from typing import Optional, Dict, Any
from uuid import UUID, uuid4
from pydantic import BaseModel, Field

class Supplier(BaseModel):
    supplier_id: UUID = Field(default_factory=uuid4)
    supplier_name: str
    contact_info: Dict[str, Any] = Field(default_factory=dict)
    default_lead_time_days: Optional[int] = None
    reliability_score: Optional[float] = None
    created_at: datetime = Field(default_factory=datetime.now)

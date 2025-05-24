"""
Scoring models and calculation logic.
"""

from datetime import datetime
from typing import Optional
from uuid import UUID, uuid4
from pydantic import BaseModel, Field

class BatchScore(BaseModel):
    score_id: UUID = Field(default_factory=uuid4)
    batch_id: UUID
    store_id: UUID
    
    # Calculated scores
    urgency_score: float
    economic_risk_score: float
    velocity_score: float
    composite_score: float
    
    # Supporting metrics
    days_until_expiry: Optional[int] = None
    revenue_at_risk: Optional[float] = None
    recommended_action: Optional[str] = None
    suggested_discount_percent: Optional[float] = None
    
    # Forecasting
    predicted_waste_quantity: Optional[int] = None
    predicted_waste_value: Optional[float] = None
    confidence_level: Optional[float] = None
    
    scored_at: datetime = Field(default_factory=datetime.now)
    valid_until: Optional[datetime] = None
    created_at: datetime = Field(default_factory=datetime.now)

    @classmethod
    def calculate_urgency_score(cls, days_until_expiry: int, product_category: str) -> float:
        """Calculate urgency score based on days until expiry and product category."""
        if product_category in ['dairy', 'meat', 'produce']:
            return max(0, 100 - (days_until_expiry * 15))
        elif product_category in ['bakery', 'prepared_foods']:
            return max(0, 100 - (days_until_expiry * 25))
        else:
            return max(0, 100 - (days_until_expiry * 10))

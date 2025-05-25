"""
Scoring models and calculation logic.
"""

from datetime import datetime, date
from typing import Optional, List, Dict, Any
from uuid import UUID, uuid4
from pydantic import BaseModel, Field
import random

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

class ScoreGenerator:
    """Generates batch scores for products."""
    def __init__(self, batches: List[Dict[str, Any]], stores: List[Dict[str, Any]], products: List[Dict[str, Any]]):
        """Initialize the score generator with batch, store, and product data."""
        self.batches = batches
        self.stores = stores
        self.products = products
        self.category_weights = {
            'dairy': 1.2,
            'meat': 1.3,
            'produce': 1.1,
            'bakery': 0.9,
            'prepared_foods': 1.0,
            'shelf_stable': 0.7
        }
        # Create lookup maps for quick access
        self.product_lookup = {p['product_id']: p for p in products}
        self.store_lookup = {s['store_id']: s for s in stores}
    def generate_batch_scores(self, current_date: datetime) -> List[BatchScore]:
        """Generate scores for all batches based on their current state."""
        scores = []
        for batch in self.batches:
            store = self.store_lookup[batch['store_id']]
            product = self.product_lookup[batch['product_id']]
            
            # Calculate days until expiry
            days_until_expiry = (batch['expiry_date'] - current_date.date()).days
            
            # Calculate urgency score based on days until expiry and category
            urgency = BatchScore.calculate_urgency_score(days_until_expiry, product['category'])
            
            # Calculate economic risk based on current quantity and price
            revenue_at_risk = batch['current_quantity'] * batch['current_price']
            economic = min(100, (revenue_at_risk / 1000) * 100)  # Scale based on revenue at risk
            
            # Calculate velocity score based on movement history
            initial_delta = batch['initial_quantity'] - batch['current_quantity']
            days_since_received = (current_date.date() - batch['received_date']).days
            velocity = min(100, (initial_delta / max(1, days_since_received)) * 20)  # Scale for reasonable values
            
            # Apply category weights
            category_weight = self.category_weights.get(product['category'], 1.0)
            composite = (urgency * 0.4 + economic * 0.3 + velocity * 0.3) * category_weight
            
            # Calculate predicted waste
            if composite > 70:
                predicted_waste_ratio = min(1.0, composite / 100)
                predicted_quantity = int(batch['current_quantity'] * predicted_waste_ratio)
                predicted_value = predicted_quantity * batch['current_price']
            else:
                predicted_quantity = 0
                predicted_value = 0
            
            score = BatchScore(
                batch_id=batch['batch_id'],
                store_id=batch['store_id'],
                urgency_score=urgency,
                economic_risk_score=economic,
                velocity_score=velocity,
                composite_score=composite,
                days_until_expiry=days_until_expiry,
                revenue_at_risk=revenue_at_risk,
                recommended_action='DISCOUNT' if composite > 70 else 'MONITOR',
                suggested_discount_percent=int(min(50, composite - 20)) if composite > 70 else None,
                predicted_waste_quantity=predicted_quantity,
                predicted_waste_value=predicted_value,
                confidence_level=0.8 + (store['accuracy_score'] * 0.15)  # Base confidence on store accuracy
            )
            scores.append(score)
        
        return scores

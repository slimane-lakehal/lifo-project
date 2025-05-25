"""
Data generation utilities for testing and development.
"""

import random
import json
from datetime import datetime, date, timedelta
from typing import List, Dict, Any, Tuple, Union
from uuid import uuid4

def generate_uuid() -> str:
    """Generate a UUID string."""
    return str(uuid4())

def random_date(start_date: date, end_date: date) -> date:
    """Generate a random date between start_date and end_date."""
    time_between_dates = end_date - start_date
    days_between_dates = time_between_dates.days
    random_number_of_days = random.randrange(days_between_dates)
    return start_date + timedelta(days=random_number_of_days)

def weighted_choice(choices: List[Tuple[Any, Union[int, float]]]) -> Any:
    """Choose an item from a list of (item, weight) tuples."""
    total = sum(w for _, w in choices)
    r = random.uniform(0, total)
    upto = 0
    for choice, weight in choices:
        upto += weight
        if upto > r:
            return choice
    return choices[0][0]  # Fallback to first choice

def format_date(date_obj: date) -> str:
    """Format a date object as YYYY-MM-DD string."""
    return date_obj.strftime("%Y-%m-%d")

def get_seasonal_factor(date_obj: date, product_category: str, subcategory: str) -> float:
    """Return a seasonal multiplier (0.5-1.5) based on date and product type."""
    month = date_obj.month
    
    # Summer products (higher in summer months)
    summer_products = {
        'dairy': ['ice cream', 'yogurt drinks'],
        'produce': ['berries', 'melons', 'summer vegetables'],
        'beverages': ['soda', 'juice', 'water']
    }
    
    # Winter products (higher in winter months)
    winter_products = {
        'canned': ['soup'],
        'dry_goods': ['hot chocolate', 'tea'],
        'bakery': ['holiday treats']
    }
    
    # Check if product is seasonal
    is_summer_product = False
    is_winter_product = False
    
    if product_category in summer_products and subcategory in summer_products[product_category]:
        is_summer_product = True
    
    if product_category in winter_products and subcategory in winter_products[product_category]:
        is_winter_product = True
    
    # Summer months: 6-8
    if 6 <= month <= 8:
        if is_summer_product:
            return random.uniform(1.2, 1.5)
        elif is_winter_product:
            return random.uniform(0.5, 0.8)
    
    # Winter months: 12, 1-2
    if month == 12 or 1 <= month <= 2:
        if is_winter_product:
            return random.uniform(1.2, 1.5)
        elif is_summer_product:
            return random.uniform(0.5, 0.8)
    
    # Holiday season: November-December
    if 11 <= month <= 12:
        if product_category in ['bakery', 'meat']:
            return random.uniform(1.1, 1.3)
    
    # Default - slight randomization
    return random.uniform(0.9, 1.1)

def get_day_of_week_factor(date_obj: date, store_type: str) -> float:
    """Return a day-of-week multiplier for sales volume."""
    day_of_week = date_obj.weekday()  # 0=Monday, 6=Sunday
    
    if store_type == 'convenience':
        # Convenience stores have more consistent traffic
        if day_of_week < 5:  # Weekday
            return random.uniform(0.9, 1.1)
        else:  # Weekend
            return random.uniform(1.0, 1.2)
    else:  # Grocery and pet stores
        if day_of_week < 2:  # Monday-Tuesday
            return random.uniform(0.7, 0.9)
        elif day_of_week < 5:  # Wednesday-Thursday
            return random.uniform(0.9, 1.1)
        else:  # Friday-Sunday
            return random.uniform(1.2, 1.5)
        
        
if __name__ == "__main__":
    # Example usage
    print("Random UUID:", generate_uuid())
    print("Random Date:", random_date(date(2023, 1, 1), date(2023, 12, 31)))
    print("Weighted Choice:", weighted_choice([("A", 1), ("B", 2), ("C", 3)]))
    print("Formatted Date:", format_date(date(2023, 10, 5)))
    print("Seasonal Factor:", get_seasonal_factor(date(2023, 7, 15), 'produce', 'berries'))
    print("Day of Week Factor:", get_day_of_week_factor(date(2023, 10, 5), 'grocery'))
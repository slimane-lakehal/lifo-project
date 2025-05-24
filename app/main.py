"""
LIFO Food Waste Platform initialization and database setup.
Handles database initialization and synthetic data generation.
"""

import asyncio
from datetime import timedelta, date
import random
import logging
from pathlib import Path

from app.database.connection import DatabaseConnection
from app.models.store import StoreGenerator
from app.models.product import ProductGenerator
from app.models.supplier import SupplierGenerator
from app.models.batch import BatchGenerator
from app.models.movement import MovementGenerator
from app.models.scoring import ScoreGenerator
from app.utils.data_generator import generate_uuid, random_date, weighted_choice, format_date
from app.utils.data_generator import get_seasonal_factor, get_day_of_week_factor

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configuration
START_DATE = date(2023, 1, 1)  # Base date for historical data
END_DATE = date(2023, 3, 1)    # Current date for the simulation
DAYS_OF_HISTORY = (END_DATE - START_DATE).days

async def generate_sample_data():
    """Generate sample data for the LIFO platform."""
    logger.info("Starting sample data generation...")
    
    # Initialize generators
    store_gen = StoreGenerator()
    product_gen = ProductGenerator()
    supplier_gen = SupplierGenerator()
    
    # Generate base data
    logger.info("Generating stores...")
    stores = store_gen.generate(count=8)  # 8 stores across different regions
    
    logger.info("Generating products...")
    products = product_gen.generate()  # This will generate based on category counts
    
    logger.info("Generating suppliers...")
    suppliers = supplier_gen.generate(count=15)  # 15 suppliers of different types
    
    # Generate batches with historical data
    logger.info("Generating product batches...")
    batch_gen = BatchGenerator(stores, products, suppliers)
    batches = batch_gen.generate(count=800, current_date=END_DATE)  # ~100 batches per store
    
    # Generate movements
    logger.info("Generating inventory movements...")
    movement_gen = MovementGenerator(batches, stores, products)
    movements = movement_gen.generate(start_date=START_DATE, end_date=END_DATE)
    
    # Generate scores
    logger.info("Generating batch scores...")
    score_gen = ScoreGenerator(batches, stores, products)
    scores = score_gen.generate(current_date=END_DATE)
    
    # Generate SQL
    output_dir = Path("database")
    output_dir.mkdir(exist_ok=True)
    
    logger.info("Generating SQL files...")
    sample_data_path = output_dir / "sample_data.sql"
    with open(sample_data_path, "w", encoding="utf-8") as f:
        f.write("-- LIFO Platform Sample Data\n\n")
        f.write(store_gen.get_sql())
        f.write("\n")
        f.write(product_gen.get_sql())
        f.write("\n")
        f.write(supplier_gen.get_sql())
        f.write("\n")
        f.write(batch_gen.get_sql())
        f.write("\n")
        f.write(movement_gen.get_sql())
        f.write("\n")
        f.write(score_gen.get_sql())
    
    logger.info(f"Sample data SQL written to {sample_data_path}")
    
    # Output statistics
    logger.info("\nGenerated Data Statistics:")
    logger.info(f"Stores: {len(stores)}")
    logger.info(f"Products: {len(products)}")
    logger.info(f"Suppliers: {len(suppliers)}")
    logger.info(f"Batches: {len(batches)}")
    logger.info(f"Movements: {len(movements)}")
    logger.info(f"Scores: {len(scores)}")

async def main():
    """Main entry point for data generation."""
    try:
        await generate_sample_data()
        logger.info("Data generation completed successfully!")
    except Exception as e:
        logger.error(f"Error during data generation: {e}", exc_info=True)
        raise

if __name__ == "__main__":
    asyncio.run(main())

"""
LIFO Food Waste Platform initialization and database setup.
Handles synthetic data generation.
"""

from datetime import timedelta, date
import random
import logging
from pathlib import Path
import sys
import os

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database.connection import DatabaseConnection
from app.models.store import StoreGenerator
from app.models.product import ProductGenerator
from app.models.supplier import SupplierGenerator
from app.models.batch import BatchGenerator
from app.models.movement import MovementGenerator
from app.models.scoring import ScoreGenerator
from app.utils.data_generator import generate_uuid, random_date, weighted_choice, format_date
from app.utils.data_generator import get_seasonal_factor, get_day_of_week_factor

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configuration
START_DATE = date(2023, 1, 1)  # Base date for historical data
END_DATE = date(2023, 3, 1)    # Current date for the simulation
DAYS_OF_HISTORY = (END_DATE - START_DATE).days

def execute_sql_statements(sql_statements):
    """Execute a series of SQL statements using the synchronous connection."""
    conn = None
    try:
        conn = DatabaseConnection.get_connection()
        cursor = conn.cursor()
        
        # Split the statements by type using the comment markers
        sections = sql_statements.split('\n-- ')
        for section in sections:
            if not section.strip():
                continue
                
            # Get the section type from the first line
            first_line = section.split('\n')[0]
            if 'Store Data' in first_line:
                logger.info("Executing store inserts...")
            elif 'Product Data' in first_line:
                logger.info("Executing product inserts...")
            elif 'Supplier Data' in first_line:
                logger.info("Executing supplier inserts...")
            elif 'Batch Data' in first_line:
                logger.info("Executing batch inserts...")
            elif 'Movement Data' in first_line:
                logger.info("Executing movement inserts...")            # Skip the first line (section header) and get actual statements
            statements = section.split('\n')[1:]  # Skip the header line
            for statement in ('\n'.join(statements)).split(';'):
                statement = statement.strip()
                if statement:
                    try:
                        cursor.execute(statement)
                    except Exception as e:
                        logger.error(f"Error executing statement: {e}")
                        logger.error(f"Failed statement: {statement}")
                        raise
                        
            # Commit after each section
            conn.commit()
            logger.info("Section executed successfully")
        
        cursor.close()
        logger.info("All SQL statements executed successfully")
        
    except Exception as e:
        if conn:
            conn.rollback()
        logger.error(f"Error executing SQL: {e}")
        raise
    finally:
        if conn:
            DatabaseConnection.return_connection(conn)

def generate_sql_inserts(stores, products, suppliers, batches, movements):
    """Generate SQL INSERT statements for all data."""
    sql = []
    # Stores
    sql.append("-- Store Data")
    store_lookup = {}  # Keep track of store IDs
    store_inserts = []
    for store in stores:
        # Escape single quotes in strings
        store_name = store['store_name'].replace("'", "''")
        address = store['address'].replace("'", "''")
        store_id = store['store_id']
        store_lookup[store_id] = True
        store_inserts.append(f"""INSERT INTO stores (store_id, store_name, store_type, address, timezone)
VALUES ('{store_id}', '{store_name}', '{store['store_type']}', 
        '{address}', '{store['timezone']}')""")
    sql.append(';\n'.join(store_inserts) + ';')
      # Products
    sql.append("\n-- Product Data")
    product_inserts = []
    for product in products:
        # Escape single quotes in strings
        product_name = product['product_name'].replace("'", "''")
        brand = product['brand'].replace("'", "''")
        product_inserts.append(f"""INSERT INTO products (product_id, sku, product_name, brand, category, 
                      subcategory, unit_size, unit_type, shelf_life_days, temperature_zone)
VALUES ('{product['product_id']}', '{product['sku']}', '{product_name}', 
        '{brand}', '{product['category']}', '{product['subcategory']}',
        '{product['unit_size']}', '{product['unit_type']}', {product['shelf_life_days']}, 
        '{product['temperature_zone']}'""")
    sql.append(';\n'.join(p + ')' for p in product_inserts) + ';')
      # Suppliers
    sql.append("\n-- Supplier Data")
    supplier_inserts = []
    for supplier in suppliers:
        # Escape single quotes in strings
        supplier_name = supplier['supplier_name'].replace("'", "''")
        contact_info = supplier['contact_info'].replace("'", "''")
        supplier_inserts.append(f"""INSERT INTO suppliers (supplier_id, supplier_name, contact_info)
VALUES ('{supplier['supplier_id']}', '{supplier_name}', 
        '{contact_info}'""")
    sql.append(';\n'.join(s + ')' for s in supplier_inserts) + ';')    # Batches
    sql.append("\n-- Batch Data")
    batch_inserts = []
    for batch in batches:
        # Validate store_id exists
        store_id = batch['store_id']
        if store_id not in store_lookup:
            logger.warning(f"Skipping batch with invalid store_id: {store_id}")
            continue
            
        batch_inserts.append(f"""INSERT INTO batches (batch_id, store_id, product_id, supplier_id, 
                      received_date, expiration_date, quantity, unit_cost, status)
VALUES ('{batch['batch_id']}', '{store_id}', '{batch['product_id']}', 
        '{batch['supplier_id']}', '{batch['received_date']}', '{batch['expiration_date']}',
        {batch['quantity']}, {batch['unit_cost']}, '{batch['status']}'""")
    sql.append(';\n'.join(b + ')' for b in batch_inserts) + ';')
      # Movements
    sql.append("\n-- Movement Data")
    movement_inserts = []
    for movement in movements:
        expiry_clause = f"'{movement['expiration_date']}'" if movement.get('expiration_date') else 'NULL'
        batch_clause = f"'{movement['batch_id']}'" if movement.get('batch_id') else 'NULL'
        
        movement_inserts.append(f"""INSERT INTO inventory_movements (movement_id, store_id, product_id, 
                      movement_type, quantity, unit_cost, batch_id, expiration_date, transaction_time)
VALUES ('{movement['movement_id']}', '{movement['store_id']}', '{movement['product_id']}', 
        '{movement['movement_type']}', {movement['quantity']}, {movement['unit_cost']},
        {batch_clause}, {expiry_clause}, '{movement['transaction_time']}'""")
    sql.append(';\n'.join(m + ')' for m in movement_inserts) + ';')
    
    return '\n'.join(sql)

def generate_all_data():
    """Generate all sample data aligned with the database schema."""
    logger.info("Generating stores...")
    store_gen = StoreGenerator()
    stores = store_gen.generate(5)
    
    logger.info("Generating products...")
    product_gen = ProductGenerator()
    products = product_gen.generate()
    
    logger.info("Generating suppliers...")
    supplier_gen = SupplierGenerator()
    suppliers = supplier_gen.generate(8)
    
    logger.info("Generating batches...")
    batch_gen = BatchGenerator(stores, products, suppliers)
    batches = batch_gen.generate(200)
    
    logger.info("Generating movements...")
    movement_gen = MovementGenerator(batches, stores, products)
    movements = movement_gen.generate()
    
    logger.info("Generating SQL...")
    sql = generate_sql_inserts(stores, products, suppliers, batches, movements)
    
    logger.info(f"Generated {len(stores)} stores, {len(products)} products, "
          f"{len(suppliers)} suppliers, {len(batches)} batches, "
          f"and {len(movements)} movements")
    
    return {
        'stores': stores,
        'products': products,
        'suppliers': suppliers,
        'batches': batches,
        'movements': movements,
        'sql': sql
    }

def insert_sample_data():
    """Insert sample data into database."""
    try:
        logger.info("Inserting data into database...")
        data = generate_all_data()
        execute_sql_statements(data['sql'])
        logger.info("Sample data inserted into database successfully")
        return True
    except Exception as e:
        logger.error(f"Error inserting sample data: {e}", exc_info=True)
        return False

def check_existing_data():
    """Check if data already exists in the database."""
    conn = None
    try:
        conn = DatabaseConnection.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM stores")
        result = cursor.fetchone()
        cursor.close()
        return result[0] if result else 0
    except Exception as e:
        logger.error(f"Error checking existing data: {e}")
        return -1
    finally:
        if conn:
            DatabaseConnection.return_connection(conn)

def main():
    """Main entry point for data generation."""
    try:
        # Test database connection first
        if not DatabaseConnection.test_connection():
            logger.error("Database connection failed. Please check your configuration.")
            return
        
        # Check if data already exists
        store_count = check_existing_data()
        
        if store_count == -1:
            logger.error("Could not check existing data. Database may not be initialized.")
            return
        elif store_count == 0:
            logger.info("No existing data found, generating sample data...")
            if insert_sample_data():
                logger.info("Sample data generation completed successfully.")
            else:
                logger.error("Sample data generation failed.")
        else:
            logger.info(f"Found existing data ({store_count} stores), skipping sample data generation.")
            
    except Exception as e:
        logger.error(f"Error during data generation: {e}", exc_info=True)
        raise
    finally:
        # Clean up connection pool
        DatabaseConnection.close_pool()

if __name__ == "__main__":
    main()
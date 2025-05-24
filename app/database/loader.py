"""
Database loader module for LIFO platform.
Handles database connection and data loading.
"""

import os
import logging
from pathlib import Path
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class DatabaseLoader:
    def __init__(
        self,        host: str = "localhost",
        port: int = 5432,
        user: str = "postgres",
        password: str = "postgres",
        database: str = "lifo_db"
    ):
        self.host = host
        self.port = port
        self.user = user
        self.password = password
        self.database = database

    def create_database(self):
        """Create the database if it doesn't exist."""
        try:
            # Connect to default postgres database to create our database
            conn = psycopg2.connect(
                host=self.host,
                port=self.port,
                user=self.user,
                password=self.password,
                database="postgres"
            )
            conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
            
            with conn.cursor() as cur:
                # Check if database exists
                cur.execute("SELECT 1 FROM pg_database WHERE datname = %s;", (self.database,))
                if not cur.fetchone():
                    logger.info(f"Creating database {self.database}...")
                    cur.execute(f'CREATE DATABASE {self.database};')
                    logger.info("Database created successfully")
                else:
                    logger.info(f"Database {self.database} already exists")
        except Exception as e:
            logger.error(f"Error creating database: {e}")
            raise
        finally:
            if conn:
                conn.close()

    def init_database(self):
        """Initialize database schema."""
        try:
            conn = psycopg2.connect(
                host=self.host,
                port=self.port,
                user=self.user,
                password=self.password,
                database=self.database
            )
            
            # Read and execute initialization script
            init_script_path = Path(__file__).parent.parent.parent / "database" / "init_database.sql"
            with open(init_script_path, 'r', encoding='utf-8') as f:
                init_script = f.read()
            
            with conn.cursor() as cur:
                logger.info("Initializing database schema...")
                cur.execute(init_script)
            
            conn.commit()
            logger.info("Database schema initialized successfully")
        except Exception as e:
            logger.error(f"Error initializing database: {e}")
            raise
        finally:
            if conn:
                conn.close()

    def load_sample_data(self, sample_data_path: Path):
        """Load sample data from SQL file."""
        try:
            conn = psycopg2.connect(
                host=self.host,
                port=self.port,
                user=self.user,
                password=self.password,
                database=self.database
            )
            
            with open(sample_data_path, 'r', encoding='utf-8') as f:
                sample_data = f.read()
            
            with conn.cursor() as cur:
                logger.info("Loading sample data...")
                cur.execute(sample_data)
            
            conn.commit()
            logger.info("Sample data loaded successfully")
        except Exception as e:
            logger.error(f"Error loading sample data: {e}")
            raise
        finally:
            if conn:
                conn.close()

    def verify_data(self):
        """Verify data counts in all tables."""
        try:
            conn = psycopg2.connect(
                host=self.host,
                port=self.port,
                user=self.user,
                password=self.password,
                database=self.database
            )
            
            tables = [
                'stores', 'products', 'suppliers', 
                'product_batches', 'inventory_movements', 
                'batch_scores'
            ]
            
            with conn.cursor() as cur:
                for table in tables:
                    cur.execute(f"SELECT COUNT(*) FROM {table}")
                    count = cur.fetchone()[0]
                    logger.info(f"{table}: {count} records")
        except Exception as e:
            logger.error(f"Error verifying data: {e}")
            raise
        finally:
            if conn:
                conn.close()

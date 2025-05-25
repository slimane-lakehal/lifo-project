"""
Database connection management for the LIFO Food Waste Platform.
Synchronous version using psycopg2.
"""

import time
import psycopg2
from psycopg2 import pool
from typing import Optional
import sys
import os
# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from app.config import DB_CONFIG

class DatabaseConnection:
    _pool: Optional[psycopg2.pool.SimpleConnectionPool] = None
    _max_retries: int = 5
    _retry_delay: int = 2  # seconds    
    
    @classmethod
    def get_pool(cls) -> psycopg2.pool.SimpleConnectionPool:
        """Get or create the database connection pool with retry logic for docker startup."""
        if cls._pool is None:
            for attempt in range(cls._max_retries):
                try:
                    # Create connection string
                    connection_string = (
                        f"host={DB_CONFIG['host']} "
                        f"port={DB_CONFIG['port']} "
                        f"dbname={DB_CONFIG['database']} "
                        f"user={DB_CONFIG['user']} "
                        f"password={DB_CONFIG['password']}"
                    )
                    
                    cls._pool = psycopg2.pool.SimpleConnectionPool(
                        1, 20,  # min and max connections
                        connection_string
                    )
                    print(f"Successfully connected to database {DB_CONFIG['database']}")
                    break
                    
                except (psycopg2.OperationalError, psycopg2.DatabaseError) as e:
                    if attempt < cls._max_retries - 1:
                        print(f"Database connection attempt {attempt + 1} failed: {e}")
                        print(f"Retrying in {cls._retry_delay} seconds...")
                        time.sleep(cls._retry_delay)
                    else:
                        raise Exception(f"Failed to connect to database after maximum retries. Last error: {e}")
        return cls._pool

    @classmethod
    def get_connection(cls):
        """Get a connection from the pool."""
        pool = cls.get_pool()
        return pool.getconn()
    
    @classmethod
    def return_connection(cls, conn):
        """Return a connection to the pool."""
        if cls._pool:
            cls._pool.putconn(conn)

    @classmethod
    def close_pool(cls) -> None:
        """Close the database connection pool."""
        if cls._pool:
            cls._pool.closeall()
            cls._pool = None
            print("Database pool closed.")

    @classmethod
    def test_connection(cls) -> bool:
        """Test the database connection."""
        try:
            conn = cls.get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT 1;")
            result = cursor.fetchone()
            cursor.close()
            cls.return_connection(conn)
            print(f"Database connection test successful: {result}")
            return True
        except Exception as e:
            print(f"Database connection test failed: {e}")
            return False

if __name__ == "__main__":
    # Test the database connection
    try:
        print("Testing database connection...")
        print(f"Database config: {DB_CONFIG}")
        
        # Test connection
        if DatabaseConnection.test_connection():
            print("Database connection successful!")
        else:
            print("Database connection failed!")
            
    except Exception as e:
        print(f"Error during database connection test: {e}")
    finally:
        DatabaseConnection.close_pool()
        print("Database connection test completed.")
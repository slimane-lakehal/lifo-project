
"""
Simple database connection test without complex imports.
Place this file in your project root and run it directly.
"""

import psycopg2
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Database configuration
DB_CONFIG = {
    'host': os.getenv('POSTGRES_HOST', 'localhost'),
    'port': int(os.getenv('POSTGRES_PORT', '5432')),
    'database': os.getenv('POSTGRES_DB', 'lifo_db'),
    'user': os.getenv('POSTGRES_USER', 'postgres'),
    'password': os.getenv('POSTGRES_PASSWORD', 'postgres')
}

def test_connection():
    """Test the database connection."""
    try:
        print("Testing database connection...")
        print(f"Config: {DB_CONFIG}")
        
        # Create connection string
        connection_string = (
            f"host={DB_CONFIG['host']} "
            f"port={DB_CONFIG['port']} "
            f"dbname={DB_CONFIG['database']} "
            f"user={DB_CONFIG['user']} "
            f"password={DB_CONFIG['password']}"
        )
        
        print(f"Connection string: {connection_string}")
        
        # Try to connect
        conn = psycopg2.connect(connection_string)
        cursor = conn.cursor()
        cursor.execute("SELECT version();")
        result = cursor.fetchone()
        
        print(f"Successfully connected to PostgreSQL!")
        print(f"Database version: {result[0]}")
        
        cursor.close()
        conn.close()
        return True
        
    except Exception as e:
        print(f"Connection failed: {e}")
        return False

if __name__ == "__main__":
    test_connection()
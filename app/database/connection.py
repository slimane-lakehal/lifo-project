"""
Database connection management for the LIFO Food Waste Platform.
"""

import asyncio
from typing import Optional
import asyncpg
from app.config import DB_CONFIG

class DatabaseConnection:
    _pool: Optional[asyncpg.Pool] = None
    _max_retries: int = 5
    _retry_delay: int = 2  # seconds    @classmethod
    async def get_pool(cls) -> asyncpg.Pool:
        """Get or create the database connection pool with retry logic for docker startup."""
        if cls._pool is None:
            for attempt in range(cls._max_retries):
                try:
                    cls._pool = await asyncpg.create_pool(**DB_CONFIG)
                    print(f"Successfully connected to database {DB_CONFIG['database']}")
                    break
                except (ConnectionRefusedError, asyncpg.CannotConnectNowError):
                    if attempt < cls._max_retries - 1:
                        print(f"Database connection attempt {attempt + 1} failed, retrying in {cls._retry_delay} seconds...")
                        await asyncio.sleep(cls._retry_delay)
                    else:
                        raise Exception("Failed to connect to database after maximum retries")
        return cls._pool

    @classmethod
    async def close_pool(cls) -> None:
        """Close the database connection pool."""
        if cls._pool:
            await cls._pool.close()
            cls._pool = None

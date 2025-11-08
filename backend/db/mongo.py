"""
MongoDB connection helpers using Motor.

This module centralises creation of a MongoDB client using the `MONGO_URI`
and `MONGO_DB` environment variables.  Keeping a single global client
instance is recommended so you don't exhaust the connection pool.
"""


import os
from typing import Optional
from motor.motor_asyncio import AsyncIOMotorClient

_client: Optional[AsyncIOMotorClient] = None

def get_client() -> AsyncIOMotorClient:
    """Return a cached `AsyncIOMotorClient` based on MONGO_URI."""
    global _client
    if _client is None:
        mongo_uri = os.getenv("MONGO_URI")
        if not mongo_uri:
            raise RuntimeError(
                "MONGO_URI environment variable is not set. Define it in your .env"
            )
        _client = AsyncIOMotorClient(mongo_uri)
    return _client


def get_db():
    """Return a Motor database handle from `MONGO_DB` (defaults to 'household')."""
    db_name = os.getenv("MONGO_DB", "household")
    return get_client()[db_name]
"""MongoDB async connection using Motor — with in-memory fallback."""

from config import settings

_client = None
_use_memory = False


def _check_mongo():
    """Try to connect to MongoDB; return True if available."""
    global _use_memory
    try:
        import pymongo
        c = pymongo.MongoClient(settings.MONGODB_URL, serverSelectionTimeoutMS=2000)
        c.server_info()
        c.close()
        return True
    except Exception:
        _use_memory = True
        print("[INFO] MongoDB not available — using in-memory storage.")
        return False


def is_memory_mode() -> bool:
    return _use_memory


def get_client():
    """Return a Motor client (or None in memory mode)."""
    global _client
    if _use_memory:
        return None
    if _client is None:
        from motor.motor_asyncio import AsyncIOMotorClient
        _client = AsyncIOMotorClient(settings.MONGODB_URL)
    return _client


def get_database():
    """Return the application database handle (or None in memory mode)."""
    client = get_client()
    if client is None:
        return None
    return client[settings.MONGODB_DB_NAME]


# Run check on import
_check_mongo()

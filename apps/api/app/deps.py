import redis
from functools import lru_cache
from rq import Queue
from sqlalchemy.orm import Session

from app.config import settings
from app.db import get_db
from app.storage import get_storage as get_storage_instance
from app.providers.factory import get_provider  # Import from centralized factory

# Payment processing is handled by PayPal


@lru_cache()
def get_redis_client():
    """Get Redis client instance."""
    return redis.from_url(settings.redis_url)


@lru_cache()
def get_queue():
    """Get RQ queue instance."""
    redis_client = get_redis_client()
    return Queue(settings.rq_queues, connection=redis_client)


def get_storage():
    """Get storage client instance."""
    return get_storage_instance()



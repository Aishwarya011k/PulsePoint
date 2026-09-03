"""Redis cache client with graceful fallback to direct database queries."""
import json
import logging
from typing import Any

import redis

from app.config import settings

logger = logging.getLogger(__name__)

# Global Redis client instance (created on first use)
_redis_client: redis.Redis | None = None


def get_redis_client() -> redis.Redis | None:
    """
    Get or create a Redis client.

    Returns gracefully None if Redis is unavailable, allowing fallback to Postgres.
    This is intentional: Redis is a performance optimization, not a critical dependency.
    """
    global _redis_client
    
    if _redis_client is not None:
        return _redis_client
    
    if not settings.redis_url:
        logger.debug("Redis URL not configured, caching disabled")
        return None
    
    try:
        # Connect with a short timeout to fail fast if Redis is unreachable
        _redis_client = redis.from_url(
            settings.redis_url,
            decode_responses=True,
            socket_connect_timeout=2,
            socket_timeout=2,
        )
        # Test the connection
        _redis_client.ping()
        logger.info("Connected to Redis")
        return _redis_client
    except Exception as e:  # noqa: BLE001 - Intentional: graceful fallback to Postgres on any Redis error
        logger.warning("Failed to connect to Redis: %s; will fall back to Postgres queries", e)
        return None


def cache_get(key: str) -> Any | None:
    """
    Get a value from cache.

    Args:
        key: Cache key

    Returns:
        Deserialized value if found in cache, None otherwise
    """
    try:
        client = get_redis_client()
        if client is None:
            return None
        
        value = client.get(key)
        if value:
            logger.debug("Cache HIT for key: %s", key)
            return json.loads(value)
        
        logger.debug("Cache MISS for key: %s", key)
        return None
    except Exception as e:  # noqa: BLE001 - Intentional: graceful fallback to Postgres
        logger.warning("Error reading from cache (key=%s): %s; falling back to Postgres", key, e)
        return None


def cache_set(key: str, value: Any, ttl: int = 300) -> bool:
    """
    Set a value in cache with a TTL.

    Args:
        key: Cache key
        value: Value to cache (will be JSON serialized)
        ttl: Time to live in seconds (default: 300 = 5 minutes)

    Returns:
        True if set successfully, False otherwise (Redis unavailable)
    """
    try:
        client = get_redis_client()
        if client is None:
            return False
        
        client.setex(key, ttl, json.dumps(value))
        logger.debug("Cache SET for key: %s (TTL: %s)", key, ttl)
        return True
    except Exception as e:  # noqa: BLE001 - Intentional: graceful fallback to Postgres
        logger.warning("Error writing to cache (key=%s): %s", key, e)
        return False


def cache_delete(key: str) -> bool:
    """
    Delete a key from cache.

    Args:
        key: Cache key

    Returns:
        True if deleted successfully, False otherwise (Redis unavailable)
    """
    try:
        client = get_redis_client()
        if client is None:
            return False
        
        result = client.delete(key)
        if result:
            logger.debug("Cache DELETE for key: %s", key)
        return result > 0
    except Exception as e:  # noqa: BLE001 - Intentional: graceful fallback to Postgres
        logger.warning("Error deleting from cache (key=%s): %s", key, e)
        return False


def cache_delete_pattern(pattern: str) -> int:
    """
    Delete all keys matching a pattern.

    Useful for invalidating cache keys in bulk (e.g., all targets for a user).

    Args:
        pattern: Pattern to match (e.g., "targets:user:123:*")

    Returns:
        Number of keys deleted
    """
    try:
        client = get_redis_client()
        if client is None:
            return 0
        
        keys = client.keys(pattern)
        if not keys:
            return 0
        
        deleted = client.delete(*keys)
        logger.debug("Cache BULK DELETE: deleted %d keys matching pattern %s", deleted, pattern)
        return deleted
    except Exception as e:  # noqa: BLE001 - Intentional: graceful fallback to Postgres
        logger.warning("Error bulk-deleting from cache (pattern=%s): %s", pattern, e)
        return 0


def rolling_window_push(key: str, value: Any, max_size: int = 20) -> bool:
    """
    Push a value to a rolling-window list (FIFO, capped at max_size).

    Used by checks-consumer to store recent check results per target.
    New items are pushed to the left; old items fall off the right when max_size is reached.

    Args:
        key: Cache key (e.g., "target:123:recent_checks")
        value: Value to push (will be JSON serialized)
        max_size: Maximum size of the list (default: 20)

    Returns:
        True if push successful, False otherwise (Redis unavailable)
    """
    try:
        client = get_redis_client()
        if client is None:
            return False
        
        client.lpush(key, json.dumps(value))
        # Keep only the last max_size items
        client.ltrim(key, 0, max_size - 1)
        logger.debug("Rolling window PUSH to key: %s (max_size: %d)", key, max_size)
        return True
    except Exception as e:  # noqa: BLE001 - Intentional: graceful fallback when Redis unavailable
        logger.warning("Error pushing to rolling window (key=%s): %s", key, e)
        return False

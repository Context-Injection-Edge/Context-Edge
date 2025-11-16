"""
Context Lookup Service
Fetches context metadata from Redis using CID as key
"""

import redis.asyncio as redis
import json
import logging
import os
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)


class ContextLookupService:
    """Service to fetch context metadata from Redis"""

    def __init__(self):
        self.redis_host = os.getenv("REDIS_HOST", "localhost")
        self.redis_port = int(os.getenv("REDIS_PORT", "6379"))
        self.redis_client: Optional[redis.Redis] = None

    async def connect(self):
        """Connect to Redis"""
        try:
            self.redis_client = redis.Redis(
                host=self.redis_host,
                port=self.redis_port,
                decode_responses=True
            )

            # Test connection
            await self.redis_client.ping()
            logger.info(f"✅ Connected to Redis at {self.redis_host}:{self.redis_port}")

        except Exception as e:
            logger.error(f"❌ Failed to connect to Redis: {e}")
            raise

    async def disconnect(self):
        """Disconnect from Redis"""
        if self.redis_client:
            await self.redis_client.close()
            logger.info("✅ Disconnected from Redis")

    async def get_context(self, cid: str) -> Optional[Dict[str, Any]]:
        """
        Fetch context metadata from Redis using CID as key

        Args:
            cid: Context ID from QR code

        Returns:
            Context metadata dict or None if not found
        """
        if not self.redis_client:
            raise RuntimeError("Redis client not connected")

        try:
            # Fetch from Redis
            context_json = await self.redis_client.get(f"context:{cid}")

            if not context_json:
                logger.warning(f"⚠️  Context not found in Redis for CID: {cid}")
                return None

            # Parse JSON
            context = json.loads(context_json)
            logger.info(f"✅ Context retrieved from Redis: {cid}")

            return context

        except json.JSONDecodeError as e:
            logger.error(f"❌ Failed to parse context JSON for CID {cid}: {e}")
            return None
        except Exception as e:
            logger.error(f"❌ Error fetching context for CID {cid}: {e}")
            raise

    async def set_context(self, cid: str, context: Dict[str, Any], ttl: int = 86400):
        """
        Store context metadata in Redis

        Args:
            cid: Context ID
            context: Context metadata dict
            ttl: Time to live in seconds (default: 24 hours)
        """
        if not self.redis_client:
            raise RuntimeError("Redis client not connected")

        try:
            context_json = json.dumps(context)
            await self.redis_client.setex(
                f"context:{cid}",
                ttl,
                context_json
            )
            logger.info(f"✅ Context stored in Redis: {cid} (TTL: {ttl}s)")

        except Exception as e:
            logger.error(f"❌ Error storing context for CID {cid}: {e}")
            raise

    async def health_check(self) -> bool:
        """Check if Redis is connected"""
        if not self.redis_client:
            return False

        try:
            await self.redis_client.ping()
            return True
        except Exception:
            return False

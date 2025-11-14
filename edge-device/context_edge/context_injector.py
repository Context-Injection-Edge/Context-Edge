# Context Injection Module (CIM) - the patent core

import redis
import requests
import json
import time
from typing import Dict, Any, Optional

class ContextInjectionModule:
    def __init__(self, context_service_url: str, redis_host: str = "localhost", redis_port: int = 6379):
        self.context_service_url = context_service_url
        self.redis_client = redis.Redis(host=redis_host, port=redis_port, decode_responses=True)
        self.current_cid = None
        self.cache_ttl = 3600  # 1 hour

    def inject_context(self, sensor_data: Dict[str, Any], detected_cid: Optional[str] = None) -> Dict[str, Any]:
        """
        Core CIM logic: Inject context into sensor data with smart caching
        """
        metadata = None

        if detected_cid:
            # Check if CID changed or cache expired
            if detected_cid != self.current_cid or not self._is_cached(detected_cid):
                # Query context service
                metadata = self._fetch_metadata(detected_cid)
                if metadata:
                    self.current_cid = detected_cid
                    self._cache_metadata(detected_cid, metadata)
            else:
                # Use cached metadata
                metadata = self._get_cached_metadata(detected_cid)

        # Fuse metadata with sensor data
        ldo = {
            "sensor_data": sensor_data,
            "context_metadata": metadata,
            "timestamp": time.time(),
            "cid": detected_cid
        }

        return ldo

    def _is_cached(self, cid: str) -> bool:
        return self.redis_client.exists(f"metadata:{cid}")

    def _get_cached_metadata(self, cid: str) -> Optional[Dict[str, Any]]:
        cached = self.redis_client.get(f"metadata:{cid}")
        return json.loads(cached) if cached else None

    def _cache_metadata(self, cid: str, metadata: Dict[str, Any]):
        self.redis_client.setex(f"metadata:{cid}", self.cache_ttl, json.dumps(metadata))

    def _fetch_metadata(self, cid: str) -> Optional[Dict[str, Any]]:
        try:
            response = requests.get(f"{self.context_service_url}/context/{cid}", timeout=5)
            if response.status_code == 200:
                return response.json()
        except requests.RequestException:
            # Network failure - could implement offline fallback
            pass
        return None
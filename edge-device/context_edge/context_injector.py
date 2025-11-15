# Context Injection Module (CIM) - the patent core

import redis
import requests
import json
import time
from typing import Dict, Any, Optional, Protocol

class DataProtocol(Protocol):
    """Protocol for industrial data acquisition"""
    def read_sensor_data(self) -> Dict[str, Any]:
        ...

class ContextInjectionModule:
    def __init__(self, context_service_url: str, redis_host: str = "localhost", redis_port: int = 6379, data_protocol: Optional[DataProtocol] = None):
        self.context_service_url = context_service_url
        self.redis_client = redis.Redis(host=redis_host, port=redis_port, decode_responses=True)
        self.current_cid = None
        self.cache_ttl = 3600  # 1 hour
        self.data_protocol = data_protocol

    def inject_context(self, sensor_data: Optional[Dict[str, Any]] = None, detected_cid: Optional[str] = None) -> Dict[str, Any]:
        """
        Core CIM logic: Inject context into sensor data with Industrial RAG
        """
        # Get sensor data from protocol if not provided
        if sensor_data is None and self.data_protocol:
            sensor_data = self.data_protocol.read_sensor_data()
        elif sensor_data is None:
            sensor_data = {}

        metadata = None
        context_info = {}

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

            # Retrieve Industrial RAG context from Redis
            context_info = self._retrieve_context(sensor_data, detected_cid)

        # Fuse everything into LDO
        ldo = {
            "sensor_data": sensor_data,
            "context_metadata": metadata,
            "industrial_context": context_info,
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

    def _retrieve_context(self, sensor_data: Dict[str, Any], cid: str) -> Dict[str, Any]:
        """
        Retrieve Industrial RAG context from Redis Context Store
        """
        context = {}

        try:
            # Get asset info
            asset_key = f"asset:{cid}"
            asset_data = self.redis_client.get(asset_key)
            if asset_data:
                context["asset"] = json.loads(asset_data)

            # Get thresholds for each sensor
            thresholds = {}
            for sensor_name in sensor_data.keys():
                threshold_key = f"thresholds:{sensor_name}"
                threshold_data = self.redis_client.get(threshold_key)
                if threshold_data:
                    thresholds[sensor_name] = json.loads(threshold_data)
            if thresholds:
                context["thresholds"] = thresholds

            # Get runtime state (try to match by production order if available)
            # Use SCAN instead of KEYS for production safety
            runtime_keys = []
            cursor = 0
            while True:
                cursor, keys = self.redis_client.scan(cursor, match="runtime:*", count=10)
                runtime_keys.extend(keys)
                if cursor == 0 or len(runtime_keys) > 0:
                    break

            if runtime_keys:
                # Get the first one (could be enhanced to match by asset)
                runtime_data = self.redis_client.get(runtime_keys[0])
                if runtime_data:
                    context["runtime"] = json.loads(runtime_data)

            # Get current model metadata - Use SCAN instead of KEYS
            model_keys = []
            cursor = 0
            while True:
                cursor, keys = self.redis_client.scan(cursor, match="model:*", count=10)
                model_keys.extend(keys)
                if cursor == 0 or len(model_keys) > 0:
                    break

            if model_keys:
                # Get the latest model (could sort by version)
                model_data = self.redis_client.get(model_keys[0])
                if model_data:
                    context["model"] = json.loads(model_data)

        except Exception as e:
            print(f"Error retrieving context: {e}")

        return context

    def _fetch_metadata(self, cid: str) -> Optional[Dict[str, Any]]:
        try:
            response = requests.get(f"{self.context_service_url}/context/{cid}", timeout=5)
            if response.status_code == 200:
                return response.json()
        except requests.RequestException:
            # Network failure - could implement offline fallback
            pass
        return None
import asyncio
import os
import time
import redis.asyncio as redis
from influxdb_client import InfluxDBClient
from influxdb_client.client.write_api import SYNCHRONOUS
from typing import Optional, Dict, Tuple
import logging

from config.settings import settings

logger = logging.getLogger(__name__)


class _InMemoryRedis:
    """Minimal async-compatible in-memory cache used in offline mode."""

    def __init__(self):
        self._store: Dict[str, Tuple[str, Optional[float]]] = {}

    async def ping(self):
        return True

    async def setex(self, key: str, expire: int, value: str):
        expires_at = time.time() + expire if expire else None
        self._store[key] = (value, expires_at)

    async def get(self, key: str):
        record = self._store.get(key)
        if not record:
            return None
        value, expires_at = record
        if expires_at and time.time() > expires_at:
            self._store.pop(key, None)
            return None
        return value

    async def close(self):
        self._store.clear()


class DatabaseManager:
    def __init__(self):
        self.influx_client: Optional[InfluxDBClient] = None
        self.redis_client: Optional[redis.Redis] = None  # type: ignore[assignment]
        self.write_api = None
        self.offline_mode = os.environ.get("DISABLE_SENSORS", "0") == "1"
        self._memory_cache = _InMemoryRedis() if self.offline_mode else None
        
    async def connect_influxdb(self):
        """Connect to InfluxDB"""
        if self.offline_mode:
            logger.info("Offline mode enabled: skipping InfluxDB connection")
            return
        try:
            self.influx_client = InfluxDBClient(
                url=settings.INFLUXDB_URL,
                token=settings.INFLUXDB_TOKEN,
                org=settings.INFLUXDB_ORG
            )
            self.write_api = self.influx_client.write_api(write_options=SYNCHRONOUS)
            logger.info("Connected to InfluxDB successfully")
        except Exception as e:
            logger.warning(f"Failed to connect to InfluxDB: {e}. Switching to offline mode.")
            self.offline_mode = True
            os.environ["DISABLE_SENSORS"] = "1"
            self._memory_cache = _InMemoryRedis()
    
    async def connect_redis(self):
        """Connect to Redis"""
        if self.offline_mode:
            logger.info("Offline mode enabled: using in-memory cache instead of Redis")
            self.redis_client = self._memory_cache  # type: ignore[assignment]
            return
        try:
            self.redis_client = redis.from_url(
                settings.REDIS_URL,
                db=settings.REDIS_DB,
                decode_responses=True
            )
            await self.redis_client.ping()
            logger.info("Connected to Redis successfully")
        except Exception as e:
            logger.warning(f"Failed to connect to Redis: {e}. Switching to offline mode.")
            self.offline_mode = True
            os.environ["DISABLE_SENSORS"] = "1"
            self._memory_cache = _InMemoryRedis()
            self.redis_client = self._memory_cache  # type: ignore[assignment]
    
    async def connect(self):
        """Connect to all databases"""
        await self.connect_influxdb()
        await self.connect_redis()
    
    async def disconnect(self):
        """Disconnect from all databases"""
        if self.influx_client:
            self.influx_client.close()
        if self.redis_client:
            await self.redis_client.close()
    
    def get_influx_client(self) -> InfluxDBClient:
        """Get InfluxDB client instance"""
        if not self.influx_client:
            raise RuntimeError("InfluxDB not connected. Call connect() first.")
        return self.influx_client
    
    async def get_redis_client(self):
        """Get Redis client instance"""
        if not self.redis_client:
            raise RuntimeError("Redis not connected. Call connect() first.")
        return self.redis_client
    
    async def write_traffic_data(self, data: dict):
        """Write traffic data to InfluxDB"""
        try:
            point = {
                "measurement": "traffic_flow",
                "tags": {
                    "sensor_id": data.get("sensor_id"),
                    "location": data.get("location"),
                    "road_type": data.get("road_type")
                },
                "fields": {
                    "vehicle_count": data.get("vehicle_count", 0),
                    "average_speed": data.get("average_speed", 0),
                    "congestion_level": data.get("congestion_level", 0),
                    "flow_rate": data.get("flow_rate", 0)
                },
                "time": data.get("timestamp")
            }
            
            self.write_api.write(
                bucket=settings.INFLUXDB_BUCKET,
                record=point
            )
            logger.debug(f"Traffic data written to InfluxDB: {data.get('sensor_id')}")
            
        except Exception as e:
            logger.error(f"Failed to write traffic data: {e}")
            raise
    
    async def cache_traffic_data(self, key: str, data: dict, expire: int = 300):
        """Cache traffic data in Redis"""
        try:
            redis_client = await self.get_redis_client()
            await redis_client.setex(key, expire, str(data))
            logger.debug(f"Traffic data cached in Redis: {key}")
        except Exception as e:
            logger.error(f"Failed to cache traffic data: {e}")
            raise
    
    async def get_cached_data(self, key: str) -> Optional[dict]:
        """Get cached traffic data from Redis"""
        try:
            redis_client = await self.get_redis_client()
            data = await redis_client.get(key)
            return eval(data) if data else None
        except Exception as e:
            logger.error(f"Failed to get cached data: {e}")
            return None

# Global database manager instance
db_manager = DatabaseManager()


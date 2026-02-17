import redis
import json
from typing import Optional, Any
from ..config import REDIS_URL

class RedisClient:
    def __init__(self):
        self.client = redis.from_url(REDIS_URL, decode_responses=True)
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from Redis"""
        value = self.client.get(key)
        if value:
            try:
                return json.loads(value)
            except:
                return value
        return None
    
    def set(self, key: str, value: Any, expiration: int = 300):
        """Set value in Redis with expiration (default 5 min)"""
        if isinstance(value, (dict, list)):
            value = json.dumps(value)
        self.client.setex(key, expiration, value)
    
    def delete(self, key: str):
        """Delete key from Redis"""
        self.client.delete(key)
    
    def publish(self, channel: str, message: dict):
        """Publish message to Redis pub/sub channel"""
        self.client.publish(channel, json.dumps(message))
    
    def subscribe(self, channel: str):
        """Subscribe to Redis pub/sub channel"""
        pubsub = self.client.pubsub()
        pubsub.subscribe(channel)
        return pubsub
    
    def flush_cache(self):
        """Clear all cache"""
        self.client.flushdb()


# Global instance
redis_client = RedisClient()

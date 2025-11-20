import redis
import json
from app.core.config import settings

class AlarmQueue:
    def __init__(self):
        try:
            self.client = redis.Redis(
                host=settings.REDIS_HOST,
                port=settings.REDIS_PORT,
                db=0,
                decode_responses=True
            )
            # Test connection
            self.client.ping()
        except Exception as e:
            print(f"Redis connection failed: {e}")
            self.client = None

    def push_alarm(self, alarm_data: dict):
        if not self.client:
            return False
        try:
            self.client.lpush("alarm_queue", json.dumps(alarm_data))
            return True
        except Exception as e:
            print(f"Failed to push alarm: {e}")
            return False

    def pop_alarm(self):
        if not self.client:
            return None
        try:
            # brpop returns tuple (key, value)
            item = self.client.brpop("alarm_queue", timeout=1)
            if item:
                return json.loads(item[1])
            return None
        except Exception as e:
            print(f"Failed to pop alarm: {e}")
            return None

alarm_queue = AlarmQueue()

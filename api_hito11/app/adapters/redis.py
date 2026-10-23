from redis import Redis
from redis.exceptions import RedisError

from app.observability import guarded


class RedisAdapter:
    def __init__(self, settings):
        self.client = Redis.from_url(settings.redis_url.get_secret_value(), decode_responses=True,
            socket_connect_timeout=settings.timeout_seconds, socket_timeout=settings.timeout_seconds)

    @guarded("redis", RedisError)
    def session(self, session_id):
        key = f"fixture2030:session:{session_id}"
        with self.client.pipeline(transaction=True) as pipe:
            values, ttl = pipe.hgetall(key).ttl(key).execute()
        if not values or ttl < 0 or values.get("estado") != "activa":
            return None
        return {"session_id": session_id, "estado": values["estado"],
                "ultima_actividad": values.get("ultima_actividad"), "ttl_segundos": ttl}

    @guarded("redis", RedisError)
    def ping(self):
        self.client.ping()

    def close(self):
        self.client.close()

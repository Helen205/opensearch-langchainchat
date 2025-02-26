from functools import wraps
from client import RedisClient
import json


r_client = RedisClient()._connect()

def cache(seconds: int = None):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            key = f"{func.__name__}:{(str(args) + str(kwargs))}"

            cached_data = r_client.get(key)
            if cached_data:
                return json.loads(cached_data)
              
            result = func(*args, **kwargs)

            if seconds is not None:
                r_client.setex(key, seconds, json.dumps(result))
            else:
                r_client.set(key, json.dumps(result))
            return result
        return wrapper
    return decorator
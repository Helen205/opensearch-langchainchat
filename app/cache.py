from functools import wraps
from client import RedisClient
import json
from datetime import datetime


r_client = RedisClient()._connect()

class ChatHistoryCache:
    def __init__(self, user_id: int):
        self.user_id = user_id
        self.messages = []
        self.functions = []
        self.max_history = 10
    
    def add_message(self, role: str, content: str, function_call: dict = None, function_result: dict = None):
        message = {
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat()
        }
        
        if function_call:
            message["function_call"] = function_call
            self.functions.append(function_call)
        if function_result:
            message["function_result"] = function_result
            
        self.messages.append(message)
        

        if len(self.messages) > self.max_history:
            self.messages = self.messages[-self.max_history:]
    
    def get_recent_history(self, limit: int = 5) -> list:
        return self.messages[-limit:] if self.messages else []
    
    def get_last_function(self) -> dict:
        for message in reversed(self.messages):
            if "function_call" in message:
                return message["function_call"]
        return None
    
    def get_recent_functions(self, limit: int = 3) -> list:
        recent_functions = []
        for message in reversed(self.messages):
            if "function_call" in message:
                func_name = message["function_call"].get("function")
                if func_name and func_name not in recent_functions:
                    recent_functions.append(func_name)
                    if len(recent_functions) >= limit:
                        break
        return recent_functions
    
    def clear_history(self):
        self.messages = []
        self.functions = []

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
from opensearchpy import OpenSearch
import redis
from config import config

class OpenSearchClient:
    def __init__(self):
        self.host = config.OPENSEARCH_URL
        self.port = config.OPENSEARCH_PORT
        self.auth = (config.OPENSEARCH_USER, config.OPENSEARCH_PASSWORD)

    def _connect(self):
        try:
            print(self.auth)
            client = OpenSearch(
                hosts=[{"host": self.host, "port": self.port}],
                http_auth=self.auth,
                use_ssl=True,
                verify_certs=False,
                ssl_show_warn=False,
            )
            return client
        
        except Exception as e:
            print(f"Error connecting to OpenSearch: {e}")
            return None

class RedisClient:
    def __init__(self):
        self.host = config.REDIS_HOST
        self.port = config.REDIS_PORT
        self.decode_responses = True

    def _connect(self):
        try:
            client = redis.Redis(
                host=self.host,
                port=self.port,
                decode_responses=self.decode_responses
            )
            return client
        except Exception as e:
            print(f"Error connecting to Redis: {e}")
            return None

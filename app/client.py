from opensearchpy import OpenSearch
import redis
from config import config
import psycopg2

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
        
class PostgresClient:
    def __init__(self):
        self.host = config.POSTGRES_HOST
        self.port = config.POSTGRES_PORT
        self.user = config.POSTGRES_USER
        self.password = config.POSTGRES_PASSWORD
        self.database = config.POSTGRES_DATABASE

    def _connect(self):
        try:
            client = psycopg2.connect(
                host=self.host,
                port=self.port,
                user=self.user,
                password=self.password,
                database=self.database
            )
            return client
        except Exception as e:
            print(f"Error connecting to PostgreSQL: {e}")
            return None

    def execute(self, query, params=None):
        try:
            conn = self._connect()
            if conn is None:
                return None
            
            cur = conn.cursor()
            cur.execute(query, params)
            conn.commit()
            return cur
        except Exception as e:
            print(f"Error executing query: {e}")
            return None
        finally:
            if 'cur' in locals():
                cur.close()
            if 'conn' in locals():
                conn.close()

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

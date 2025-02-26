import os
from dotenv import load_dotenv

# .env dosyasını yükle
load_dotenv()

class Config:
    ENV = os.getenv("ENV", "production")
    
    # OpenSearch
    OPENSEARCH_URL = os.getenv("OPENSEARCH_URL", "https://localhost:9200")
    OPENSEARCH_USER = os.getenv("OPENSEARCH_USER", "admin")
    OPENSEARCH_PASSWORD = os.getenv("OPENSEARCH_PASSWORD", "123456789#heleN")
    OPENSEARCH_PORT = os.getenv("OPENSEARCH_PORT", "")
    # Redis
    REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
    REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))

config = Config()

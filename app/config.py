from pydantic_settings import BaseSettings
from typing import Optional

class Config(BaseSettings):
    # OpenSearch ayarları
    OPENSEARCH_URL: str = "192.168.1.70"
    OPENSEARCH_PORT: int = 9200
    OPENSEARCH_USER: str = "admin"
    OPENSEARCH_PASSWORD: str = "123456789#heleN"

    # Redis ayarları
    REDIS_HOST: str = "redis"
    REDIS_PORT: int = 6379

    # PostgreSQL ayarları
    POSTGRES_HOST: str = "192.168.1.70"
    POSTGRES_PORT: int = 5432
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "helen*1"
    POSTGRES_DATABASE: str = "flight_data"

    # Environment ayarı
    ENV: Optional[str] = "development"

    class Config:
        env_file = ".env"
        case_sensitive = True

config = Config()

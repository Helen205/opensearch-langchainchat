from pydantic_settings import BaseSettings
from typing import Optional

class Config(BaseSettings):

    OPENSEARCH_URL: str = "192.168.3.101"
    OPENSEARCH_PORT: int = 9200
    OPENSEARCH_USER: str = "admin"
    OPENSEARCH_PASSWORD: str = "123456789#heleN"


    REDIS_HOST: str = "192.168.3.101"
    REDIS_PORT: int = 6379

    POSTGRES_HOST: str = "192.168.3.101"
    POSTGRES_PORT: int = 5432
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "helen*1"
    POSTGRES_DATABASE: str = "flight_data"

    GOOGLE_API_KEY: str = "AIzaSyA-5cG-lCSCLVpIhkkSlZnnUXk_N-46es8"


    ENV: Optional[str] = "development"

    class Config:
        env_file = ".env"
        case_sensitive = True

config = Config()

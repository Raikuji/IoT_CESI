"""
Application configuration
"""
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # App
    app_name: str = "Campus IoT API"
    debug: bool = True
    
    # Database
    database_url: str = "postgresql://campus:campus_secret@localhost:5432/campus_iot"
    
    # MQTT
    mqtt_broker: str = "localhost"
    mqtt_port: int = 1883
    mqtt_topic_prefix: str = "campus/cassiope/C101"
    
    # Auth
    secret_key: str = "super_secret_key_change_me"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60 * 24  # 24 hours
    
    class Config:
        env_file = ".env"


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()

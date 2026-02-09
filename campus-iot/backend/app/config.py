"""
Application configuration
"""
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # App
    app_name: str = "Campus IoT API"
    debug: bool = True
    
    # Database (Supabase Transaction pooler - port 6543 avec timeout augmenté)
    database_url: str = "postgresql://postgres.byseujemkgwqlxtkstge:IOTCESI2026@aws-1-eu-central-1.pooler.supabase.com:6543/postgres?options=-c%20statement_timeout%3D30000"
    
    # MQTT
    mqtt_broker: str = "mosquitto" 
    mqtt_port: int = 1883
    mqtt_topic_prefix: str = "campus/orion"  
    
    # Auth
    secret_key: str = "super_secret_key_change_me"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60 * 24 

    # Backups
    backups_enabled: bool = False
    backup_interval_minutes: int = 1440
    backup_retention_days: int = 7
    backup_dir: str = "/app/backups"

    # Exports
    exports_enabled: bool = False
    export_check_interval_seconds: int = 60
    export_dir: str = "/app/exports"
    
    class Config:
        env_file = ".env"


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()

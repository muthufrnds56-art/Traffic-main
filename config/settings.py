import os
from typing import Optional
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Application
    APP_NAME: str = "Traffic Management System"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    
    # Kafka Configuration
    KAFKA_BROKER: str = "localhost:9092"
    KAFKA_TOPIC_TRAFFIC: str = "traffic_data"
    KAFKA_TOPIC_ALERTS: str = "traffic_alerts"
    KAFKA_GROUP_ID: str = "traffic_management"
    
    # MQTT Configuration
    MQTT_BROKER: str = "localhost"
    MQTT_PORT: int = 1883
    MQTT_KEEPALIVE: int = 60
    MQTT_TOPIC_TRAFFIC: str = "sensors/traffic"
    MQTT_TOPIC_ENVIRONMENT: str = "sensors/environment"
    
    # Database Configuration
    INFLUXDB_URL: str = "http://localhost:8086"
    INFLUXDB_TOKEN: str = "your_influxdb_token"
    INFLUXDB_ORG: str = "traffic_org"
    INFLUXDB_BUCKET: str = "traffic_data"
    
    REDIS_URL: str = "redis://localhost:6379"
    REDIS_DB: int = 0
    
    # ML Model Configuration
    ML_MODEL_PATH: str = "models/"
    PREDICTION_HORIZON: int = 60  # minutes
    TRAINING_INTERVAL: int = 24    # hours
    
    # Traffic Configuration
    MAX_CONGESTION_LEVEL: int = 5
    ALERT_THRESHOLD: float = 0.8
    UPDATE_INTERVAL: int = 30     # seconds
    
    # Dataset Configuration
    DATA_SOURCE: str = "kaggle_dataset"  # Options: "simulator" or "kaggle_dataset"
    DATASET_PATH: str = "datasets/bangalore_traffic.csv"
    DATASET_REPLAY_SPEED: float = 1.0  # Speed multiplier for replaying data
    DATASET_LOOP: bool = True  # Loop dataset when it ends


    
    # API Configuration
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    API_PREFIX: str = "/api/v1"
    
    # Dashboard Configuration
    DASHBOARD_PORT: int = 8501
    DASHBOARD_HOST: str = "localhost"
    
    # Security
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    class Config:
        env_file = ".env"
        case_sensitive = True

# Global settings instance
settings = Settings()

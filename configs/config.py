"""
Configuration Management for ClimateGuardAI
"""
import os
from pathlib import Path
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field
from typing import Optional

class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    
    # LLM Provider Selection
    llm_provider: str = Field("gemini", env="LLM_PROVIDER")
    
    # API Keys
    gemini_api_key: Optional[str] = Field(None, env="GEMINI_API_KEY")
    anthropic_api_key: Optional[str] = Field(None, env="ANTHROPIC_API_KEY")
    openai_api_key: Optional[str] = Field(None, env="OPENAI_API_KEY")
    openweather_api_key: str = Field(..., env="OPENWEATHER_API_KEY")
    
    # Google Earth Engine
    google_credentials_path: Optional[str] = Field(None, env="GOOGLE_APPLICATION_CREDENTIALS")
    gee_project_id: Optional[str] = Field(None, env="GEE_PROJECT_ID")
    
    # Database
    database_url: str = Field("sqlite:///./climateguard.db", env="DATABASE_URL")
    redis_url: str = Field("redis://localhost:6379/0", env="REDIS_URL")
    
    # Twilio
    twilio_account_sid: Optional[str] = Field(None, env="TWILIO_ACCOUNT_SID")
    twilio_auth_token: Optional[str] = Field(None, env="TWILIO_AUTH_TOKEN")
    twilio_whatsapp_number: Optional[str] = Field(None, env="TWILIO_WHATSAPP_NUMBER")
    
    # Application
    debug: bool = Field(False, env="DEBUG")
    log_level: str = Field("INFO", env="LOG_LEVEL")
    max_workers: int = Field(4, env="MAX_WORKERS")
    
    # Model Paths
    tft_model_path: str = Field("models/forecasting/tft_model.pt", env="TFT_MODEL_PATH")
    crop_model_path: str = Field("models/crop_recommendation/xgboost_model.pkl", env="CROP_MODEL_PATH")
    
    # Geographic Settings
    default_grid_size_km: int = Field(5, env="DEFAULT_GRID_SIZE_KM")
    forecast_days: int = Field(7, env="FORECAST_DAYS")
    
    # RAG Configuration
    chroma_persist_dir: str = Field("data/chroma_db", env="CHROMA_PERSIST_DIR")
    embedding_model: str = Field("sentence-transformers/all-MiniLM-L6-v2", env="EMBEDDING_MODEL")
    chunk_size: int = Field(1000, env="CHUNK_SIZE")
    chunk_overlap: int = Field(200, env="CHUNK_OVERLAP")
    
    # IMD
    imd_api_url: str = Field("https://mausam.imd.gov.in/", env="IMD_API_URL")
    
    class Config:
        env_file = ".env"
        case_sensitive = False


# Project paths
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
MODELS_DIR = BASE_DIR / "models"
LOGS_DIR = BASE_DIR / "logs"

# Create directories if they don't exist
for directory in [DATA_DIR, MODELS_DIR, LOGS_DIR]:
    directory.mkdir(parents=True, exist_ok=True)
    
# Raw data subdirectories
RAW_DATA_DIR = DATA_DIR / "raw"
PROCESSED_DATA_DIR = DATA_DIR / "processed"
EXTERNAL_DATA_DIR = DATA_DIR / "external"

for directory in [RAW_DATA_DIR, PROCESSED_DATA_DIR, EXTERNAL_DATA_DIR]:
    directory.mkdir(parents=True, exist_ok=True)

# Load settings
settings = Settings()


# Geographic boundaries for India
INDIA_BOUNDS = {
    "north": 35.5,
    "south": 6.5,
    "east": 97.4,
    "west": 68.2
}

# Indian states mapping (for localization)
INDIAN_STATES = {
    "MH": "Maharashtra",
    "UP": "Uttar Pradesh",
    "PB": "Punjab",
    "HR": "Haryana",
    "RJ": "Rajasthan",
    "GJ": "Gujarat",
    "KA": "Karnataka",
    "TN": "Tamil Nadu",
    "AP": "Andhra Pradesh",
    "TG": "Telangana",
    # Add more as needed
}

# Crop database (simplified - expand based on region)
CROP_DATABASE = {
    "kharif": ["rice", "maize", "jowar", "bajra", "cotton", "soybean", "groundnut"],
    "rabi": ["wheat", "barley", "mustard", "chickpea", "peas"],
    "zaid": ["watermelon", "muskmelon", "cucumber", "vegetables"]
}

# Climate risk thresholds
RISK_THRESHOLDS = {
    "temperature": {
        "extreme_heat": 45,  # Celsius
        "heat_stress": 40,
        "frost": 0
    },
    "rainfall": {
        "drought": 50,  # mm/month
        "flood": 300   # mm/day
    },
    "wind": {
        "cyclone": 118  # km/h
    }
}
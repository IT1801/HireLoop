import os
from dotenv import load_dotenv
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional

load_dotenv() # Load variables from .env into os.environ for Langchain

class Settings(BaseSettings):
    # API Keys
    GOOGLE_API_KEY: Optional[str] = None
    GROQ_API_KEY: Optional[str] = None
    LINKEDIN_ACCESS_TOKEN: Optional[str] = None
    LINKEDIN_ORGANIZATION_ID: Optional[str] = None
    SENDGRID_API_KEY: Optional[str] = None
    
    # DB
    DB_PATH: str = "hireloop.sqlite"
    
    # App Settings
    APP_PORT: int = 8000
    
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

settings = Settings()
# Reload token

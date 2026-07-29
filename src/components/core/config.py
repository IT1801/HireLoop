import os
from dotenv import load_dotenv
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional

load_dotenv() # Load variables from .env into os.environ for Langchain

class Settings(BaseSettings):
    # API Keys
    GOOGLE_API_KEY: str = ""
    GROQ_API_KEY: Optional[str] = None
    LINKEDIN_ACCESS_TOKEN: str = ""
    LINKEDIN_ORGANIZATION_ID: Optional[str] = None
    
    # OAuth Configurations
    GOOGLE_CLIENT_ID: str = ""
    GOOGLE_CLIENT_SECRET: str = ""
    LINKEDIN_CLIENT_ID: str = ""
    LINKEDIN_CLIENT_SECRET: str = ""
    
    # LangSmith Observability
    LANGCHAIN_TRACING_V2: str = "true"
    LANGCHAIN_API_KEY: Optional[str] = None
    LANGCHAIN_PROJECT: str = "HireLoop"
    
    # DB
    POSTGRES_USER: str = "hireloop"
    POSTGRES_PASSWORD: str = "hireloop_password"
    POSTGRES_DB: str = "hireloop_db"
    POSTGRES_PORT: int = 5434
    
    @property
    def DATABASE_URL(self) -> str:
        import urllib.parse
        encoded_password = urllib.parse.quote_plus(self.POSTGRES_PASSWORD)
        return f"postgresql://{self.POSTGRES_USER}:{encoded_password}@localhost:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
    
    # App Settings
    APP_PORT: int = 8000
    FAST_FORWARD_WAITS: bool = False
    
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

settings = Settings()
# Reload token
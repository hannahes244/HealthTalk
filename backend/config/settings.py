# config/settings.py
from pydantic_settings import BaseSettings, SettingsConfigDict
import os
from typing import List

class Settings(BaseSettings):
    OPENAI_API_KEY: str
    INFERMEDICA_APP_ID: str
    INFERMEDICA_APP_KEY: str

    model_config = SettingsConfigDict(env_file='.env', extra='ignore')

    CORS_ORIGINS: List[str] = ["http://localhost:5173"]

settings = Settings()

# Configure OpenAI (moved here for centralized config)
import openai
openai.api_key = settings.OPENAI_API_KEY
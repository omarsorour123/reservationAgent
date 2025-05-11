# src/core/config.py
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Settings:
    # API settings
    API_TITLE = "Hotel Reservation API"
    API_VERSION = "1.0.0"
    API_DESCRIPTION = "An API for interacting with an AI-powered hotel reservation assistant"
    API_PREFIX = "/api"
    
    # Database settings
    DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///hotel.db")
    
    # LLM settings
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

settings = Settings()
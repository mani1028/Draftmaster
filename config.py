import os
import base64
from cryptography.fernet import Fernet
from dotenv import load_dotenv

# Get the absolute path of the directory where config.py is located
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(BASE_DIR, '.env'))

class Config:
    # Secret key for Flask sessions
    SECRET_KEY = os.getenv('SECRET_KEY', 'writegenius_open_secret_key_change_in_prod')
    
    # Database configuration - use DATABASE_URL from .env if provided
    # Supports both absolute paths and relative paths (relative to BASE_DIR)
    _db_url = os.getenv('DATABASE_URL', 'writegenius_core.db')
    if os.path.isabs(_db_url):
        DB_NAME = _db_url
    else:
        DB_NAME = os.path.join(BASE_DIR, _db_url)
    
    # Cache file for saving API responses to save API tokens
    CACHE_FILE = os.path.join(BASE_DIR, "prompt_cache.json")
    
    # LLM Configuration
    LLM_PROVIDER = 'GROQ' 
    GROQ_API_KEY = os.getenv('GROQ_API_KEY')
    
    # Fernet Key Logic
    _env_key = os.getenv('FERNET_KEY')
    
    if _env_key:
        try:
            # Validate if it's a proper Fernet key
            Fernet(_env_key.encode())
            FERNET_KEY = _env_key
        except Exception:
            print("ERROR: Invalid FERNET_KEY format in .env. Generating temporary fallback.")
            FERNET_KEY = Fernet.generate_key().decode()
    else:
        print("WARNING: FERNET_KEY not found in .env. Using temporary key.")
        FERNET_KEY = Fernet.generate_key().decode()
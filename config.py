import os
import base64
from cryptography.fernet import Fernet
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Secret key for Flask sessions
    SECRET_KEY = os.getenv('SECRET_KEY', 'writegenius_open_secret_key_change_in_prod')
    
    # Database path
    DB_NAME = "writegenius_core.db"
    
    # LLM Configuration
    LLM_PROVIDER = 'GROQ' 
    GROQ_API_KEY = os.getenv('GROQ_API_KEY')
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
    
    # Fernet Key Logic (Fixes crash on invalid key)
    _env_key = os.getenv('FERNET_KEY')
    
    if _env_key:
        FERNET_KEY = _env_key
    else:
        # Generate a temporary key if missing to prevent crash
        print("WARNING: FERNET_KEY not found in .env. Using temporary key (restarts will logout users).")
        FERNET_KEY = Fernet.generate_key().decode()
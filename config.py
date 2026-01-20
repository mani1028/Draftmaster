import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Use fixed keys for this open version
    SECRET_KEY = os.getenv('SECRET_KEY', 'writegenius_open_secret')
    FERNET_KEY = os.getenv('FERNET_KEY', 'somerandomkey123456789012345678901234567890=') # Needs to be 32 url-safe base64-encoded bytes
    DB_NAME = "writegenius_core.db"
    
    # Force GROQ as requested
    LLM_PROVIDER = 'GROQ' 
    GROQ_API_KEY = os.getenv('GROQ_API_KEY')
    
    # Fallbacks (optional)
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
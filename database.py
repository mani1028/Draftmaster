import sqlite3
from config import Config

def get_db_connection():
    conn = sqlite3.connect(Config.DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    c = conn.cursor()
    
    # Updated Users table to support real authentication
    c.execute('''CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        email TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        name TEXT DEFAULT 'User',
        role TEXT DEFAULT 'user'
    )''')

    # Drafts table (remains same but linked to dynamic users)
    c.execute('''CREATE TABLE IF NOT EXISTS drafts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        title TEXT,
        category TEXT,
        prompt_json TEXT,
        output_text_encrypted TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users (id)
    )''')
    
    conn.commit()
    conn.close()

# Initialize on import
init_db()
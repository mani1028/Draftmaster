import sqlite3
from config import Config

def get_db_connection():
    conn = sqlite3.connect(Config.DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    c = conn.cursor()
    
    # Simplified Users (We will use a single 'Guest' user for now)
    c.execute('''CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT DEFAULT 'Guest',
        role TEXT DEFAULT 'admin'
    )''')

    # Drafts
    c.execute('''CREATE TABLE IF NOT EXISTS drafts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        title TEXT,
        category TEXT,
        prompt_json TEXT,
        output_text_encrypted TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')
    
    # Seed Guest User if not exists
    user = c.execute('SELECT * FROM users WHERE id = 1').fetchone()
    if not user:
        c.execute('INSERT INTO users (id, name) VALUES (1, "Guest Admin")')
        
    conn.commit()
    conn.close()

# Initialize on import
init_db()
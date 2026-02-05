from flask import Flask, render_template, request, jsonify, send_file, redirect, url_for, session
import json
import os
import sqlite3
from cryptography.fernet import Fernet
from werkzeug.security import generate_password_hash, check_password_hash

# Internal modules
from config import Config
from database import get_db_connection, init_db
from services.llm_service import LLMService
from services.export_service import ExportService

# Initialize App & Config
app = Flask(__name__)
app.secret_key = Config.SECRET_KEY

# Ensure Database is ready
init_db()

# Encryption Setup
try:
    key = Config.FERNET_KEY.encode() if isinstance(Config.FERNET_KEY, str) else Config.FERNET_KEY
    cipher = Fernet(key)
except Exception as e:
    print(f"Critical Error: Invalid FERNET_KEY. {e}")
    cipher = Fernet(Fernet.generate_key())

def encrypt_text(text: str) -> str:
    if not text: return ""
    return cipher.encrypt(text.encode()).decode()

def decrypt_text(enc_text: str) -> str:
    if not enc_text: return ""
    try:
        return cipher.decrypt(enc_text.encode()).decode()
    except Exception:
        return "[Error: Decryption Failed]"

# --- Helper: Get Current User ---
def get_current_user_id():
    return session.get('user_id', 1) 

# --- Routes: Pages ---

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/app')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return render_template('dashboard.html')

# --- AUTHENTICATION ROUTES ---

@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        conn = get_db_connection()
        user = conn.execute('SELECT * FROM users WHERE email = ?', (email,)).fetchone()
        conn.close()

        if user and check_password_hash(user['password'], password):
            session['user_id'] = user['id']
            session['user_name'] = user['name']
            return redirect(url_for('dashboard'))
        else:
            error = "Invalid email or password."

    return render_template('login.html', mode='login', error=error)

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    error = None
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        name = request.form.get('name', 'New User')
        
        if not email or not password:
            error = "Email and password are required."
        else:
            conn = get_db_connection()
            try:
                hashed_pw = generate_password_hash(password)
                cursor = conn.execute(
                    'INSERT INTO users (email, password, name) VALUES (?, ?, ?)',
                    (email, hashed_pw, name)
                )
                conn.commit()
                session['user_id'] = cursor.lastrowid
                session['user_name'] = name
                return redirect(url_for('dashboard'))
            except sqlite3.IntegrityError:
                error = "Email already registered."
            finally:
                conn.close()
                
    return render_template('login.html', mode='signup', error=error)

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

# --- Routes: API ---

@app.route('/api/templates', methods=['GET'])
def get_templates():
    try:
        base_dir = os.path.dirname(os.path.abspath(__file__))
        path = os.path.join(base_dir, 'templates_data.json')
        with open(path, 'r') as f:
            templates = json.load(f)
        return jsonify(templates)
    except Exception as e:
        return jsonify([])

@app.route('/api/generate', methods=['POST'])
def generate():
    data = request.json
    system_prompt = LLMService.build_system_prompt(
        data.get('tone', 'Professional'), 
        data.get('audience', 'General'), 
        data.get('category', 'General')
    )
    result_text = LLMService.generate_text(system_prompt, data.get('prompt', ''), data.get('context'))
    
    # Check if the result is an error message from Groq
    if result_text.startswith("Groq Error") or result_text.startswith("Error"):
        return jsonify({'text': result_text}), 500
        
    return jsonify({'text': result_text})

@app.route('/api/drafts/save', methods=['POST'])
def save_draft():
    data = request.json
    content = data.get('content', '')
    title = data.get('title', 'Untitled')
    
    user_id = get_current_user_id()
    encrypted_content = encrypt_text(content)
    conn = get_db_connection()
    draft_id = data.get('id')
    
    try:
        if draft_id:
            conn.execute('UPDATE drafts SET output_text_encrypted = ?, title = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ? AND user_id = ?',
                         (encrypted_content, title, draft_id, user_id))
        else:
            cursor = conn.execute(
                'INSERT INTO drafts (user_id, title, category, prompt_json, output_text_encrypted) VALUES (?, ?, ?, ?, ?)',
                (user_id, title, data.get('category', 'General'), json.dumps(data.get('meta', {})), encrypted_content)
            )
            draft_id = cursor.lastrowid
        conn.commit()
        return jsonify({'message': 'Saved', 'id': draft_id})
    finally:
        conn.close()

@app.route('/api/drafts', methods=['GET'])
def list_drafts():
    user_id = get_current_user_id()
    conn = get_db_connection()
    drafts = conn.execute('SELECT id, title, category, created_at FROM drafts WHERE user_id = ? ORDER BY created_at DESC', (user_id,)).fetchall()
    conn.close()
    return jsonify([dict(d) for d in drafts])

@app.route('/api/drafts/<int:id>', methods=['GET'])
def get_draft(id):
    user_id = get_current_user_id()
    conn = get_db_connection()
    draft = conn.execute('SELECT * FROM drafts WHERE id = ? AND user_id = ?', (id, user_id)).fetchone()
    conn.close()
    if not draft: return jsonify({'error': 'Not found'}), 404
    
    data = dict(draft)
    data['content'] = decrypt_text(data['output_text_encrypted'])
    return jsonify(data)

if __name__ == '__main__':
    app.run(debug=True, port=5000)
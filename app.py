from flask import Flask, render_template, request, jsonify, send_file, redirect, url_for, session
import json
import os
import sqlite3
import hashlib
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

# --- Caching Helpers ---

def get_cache_key(data):
    """Generates a unique MD5 hash based on prompt parameters."""
    params = [
        str(data.get('category', 'General')),
        str(data.get('tone', 'Professional')),
        str(data.get('audience', 'General')),
        str(data.get('prompt', '')),
        str(data.get('context', '')),
        str(data.get('mode', '')) # Added mode to key for rewrite requests
    ]
    cache_string = "|".join(params)
    return hashlib.md5(cache_string.encode()).hexdigest()

def get_cached_response(cache_key):
    if not os.path.exists(Config.CACHE_FILE):
        return None
    try:
        with open(Config.CACHE_FILE, 'r') as f:
            cache_data = json.load(f)
            return cache_data.get(cache_key)
    except Exception:
        return None

def save_to_cache(cache_key, response_text):
    cache_data = {}
    if os.path.exists(Config.CACHE_FILE):
        try:
            with open(Config.CACHE_FILE, 'r') as f:
                cache_data = json.load(f)
        except Exception:
            cache_data = {}
            
    cache_data[cache_key] = response_text
    try:
        with open(Config.CACHE_FILE, 'w') as f:
            json.dump(cache_data, f, indent=4)
    except Exception as e:
        print(f"Cache Write Error: {e}")

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
    cache_key = get_cache_key(data)
    cached_text = get_cached_response(cache_key)
    
    if cached_text:
        return jsonify({'text': cached_text, 'cached': True})

    system_prompt = LLMService.build_system_prompt(
        data.get('tone', 'Professional'), 
        data.get('audience', 'General'), 
        data.get('category', 'General')
    )
    result_text = LLMService.generate_text(system_prompt, data.get('prompt', ''), data.get('context'))
    
    if result_text.startswith("Groq Error") or result_text.startswith("Error"):
        return jsonify({'text': result_text}), 500
    
    save_to_cache(cache_key, result_text)
    return jsonify({'text': result_text, 'cached': False})

@app.route('/api/rewrite', methods=['POST'])
def rewrite():
    data = request.json
    text_to_edit = data.get('text', '')
    mode = data.get('mode', 'Grammar Fix')
    
    if not text_to_edit:
        return jsonify({'text': 'No content provided'}), 400

    # Check cache for rewrites too
    cache_key = get_cache_key({'prompt': text_to_edit, 'mode': mode})
    cached_text = get_cached_response(cache_key)
    if cached_text:
        return jsonify({'text': cached_text, 'cached': True})

    # Prepare specialized instruction for the LLM based on mode
    instruction = ""
    if mode == 'Grammar Fix':
        instruction = "Fix all grammatical errors, spelling mistakes, and punctuation. Maintain the original meaning exactly."
    elif mode == 'Shorter':
        instruction = "Rewrite the following text to be more concise and brief while retaining all key information."
    elif mode == 'More Persuasive':
        instruction = "Rewrite this text to be more compelling, persuasive, and engaging. Use strong action verbs."
    else:
        instruction = f"Edit the following text: {mode}"

    system_prompt = "You are a professional editor. Output ONLY the revised text without any comments or introduction."
    result_text = LLMService.generate_text(system_prompt, f"{instruction}\n\nTEXT:\n{text_to_edit}")

    if not (result_text.startswith("Groq Error") or result_text.startswith("Error")):
        save_to_cache(cache_key, result_text)
    
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

@app.route('/api/export/<string:format>/<int:id>')
def export_file(format, id):
    user_id = get_current_user_id()
    conn = get_db_connection()
    draft = conn.execute('SELECT * FROM drafts WHERE id = ? AND user_id = ?', (id, user_id)).fetchone()
    conn.close()
    
    if not draft: return "Draft not found", 404
    
    content = decrypt_text(draft['output_text_encrypted'])
    title = draft['title'] or "Document"
    
    if format == 'pdf':
        buffer = ExportService.to_pdf(content)
        return send_file(buffer, as_attachment=True, download_name=f"{title}.pdf", mimetype='application/pdf')
    elif format == 'docx':
        buffer = ExportService.to_docx(content)
        return send_file(buffer, as_attachment=True, download_name=f"{title}.docx", mimetype='application/vnd.openxmlformats-officedocument.wordprocessingml.document')
    
    return "Invalid format", 400

if __name__ == '__main__':
    app.run(debug=True, port=5000)
from flask import Flask, render_template, request, jsonify, send_file, redirect, url_for
import json
import os
from cryptography.fernet import Fernet

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
    # Ensure key is bytes
    key = Config.FERNET_KEY.encode() if isinstance(Config.FERNET_KEY, str) else Config.FERNET_KEY
    cipher = Fernet(key)
except Exception as e:
    print(f"Critical Error: Invalid FERNET_KEY. {e}")
    # Fallback to a new key to keep app alive, though old data won't decrypt
    cipher = Fernet(Fernet.generate_key())

def encrypt_text(text: str) -> str:
    """Encrypts a plaintext string."""
    if not text: return ""
    return cipher.encrypt(text.encode()).decode()

def decrypt_text(enc_text: str) -> str:
    """Decrypts a ciphertext string."""
    if not enc_text: return ""
    try:
        return cipher.decrypt(enc_text.encode()).decode()
    except Exception:
        return "[Error: Decryption Failed - Key may have changed]"

# --- Routes: Pages ---

@app.route('/')
def index():
    """Render the Marketing Landing Page."""
    return render_template('index.html')

@app.route('/app')
def dashboard():
    """Render the Main App Dashboard."""
    return render_template('dashboard.html')

# --- AUTHENTICATION ROUTES ---

@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        # TEST CREDENTIALS
        if email == 'test@example.com' and password == 'password':
            return redirect(url_for('dashboard'))
        else:
            error = "Invalid credentials. Try: test@example.com / password"

    return render_template('login.html', mode='login', error=error)

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        return redirect(url_for('dashboard'))
    return render_template('login.html', mode='signup')

# --- Routes: API ---

@app.route('/api/templates', methods=['GET'])
def get_templates():
    try:
        # Use absolute path to ensure file is found regardless of where script is run
        base_dir = os.path.dirname(os.path.abspath(__file__))
        path = os.path.join(base_dir, 'templates_data.json')
        
        with open(path, 'r') as f:
            templates = json.load(f)
        return jsonify(templates)
    except FileNotFoundError:
        return jsonify([])
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/generate', methods=['POST'])
def generate():
    data = request.json
    tone = data.get('tone', 'Professional')
    audience = data.get('audience', 'General')
    category = data.get('category', 'General')
    user_prompt = data.get('prompt', '')
    context = data.get('context', '')
    
    if not user_prompt and not context:
        return jsonify({'error': 'Prompt is required'}), 400
    
    system_prompt = LLMService.build_system_prompt(tone, audience, category)
    result_text = LLMService.generate_text(system_prompt, user_prompt, existing_context=context)
    
    return jsonify({'text': result_text})

@app.route('/api/rewrite', methods=['POST'])
def rewrite():
    data = request.json
    original_text = data.get('text', '')
    mode = data.get('mode', 'Professional') 
    
    if not original_text:
        return jsonify({'error': 'No text provided'}), 400

    instruction = f"Rewrite this text to be {mode}."
    if mode == "Simpler English":
        instruction += " Use simple vocabulary and short sentences (Grade 5 level)."
    elif mode == "More Persuasive":
        instruction += " Focus on benefits, urgency, and strong call-to-actions."
    elif mode == "Grammar Fix":
        instruction = "Fix all grammar, spelling, and punctuation errors. Do not change the tone."
    elif mode == "Shorter":
        instruction = "Summarize this text concisely without losing key meaning."

    prompt = f"{instruction}\n\nORIGINAL TEXT:\n{original_text}"
    result = LLMService.generate_text("You are an expert editor.", prompt)
    return jsonify({'text': result})

# --- Draft Handling ---

@app.route('/api/drafts/save', methods=['POST'])
def save_draft():
    data = request.json
    content = data.get('content', '')
    title = data.get('title', 'Untitled')
    category = data.get('category', 'General')

    if not content:
        return jsonify({'error': 'Content cannot be empty'}), 400

    encrypted_content = encrypt_text(content)
    conn = get_db_connection()
    draft_id = data.get('id')
    user_id = 1 # Guest ID
    
    try:
        if draft_id:
            conn.execute('UPDATE drafts SET output_text_encrypted = ?, title = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?',
                         (encrypted_content, title, draft_id))
        else:
            cursor = conn.execute(
                'INSERT INTO drafts (user_id, title, category, prompt_json, output_text_encrypted) VALUES (?, ?, ?, ?, ?)',
                (user_id, title, category, json.dumps(data.get('meta', {})), encrypted_content)
            )
            draft_id = cursor.lastrowid
        
        conn.commit()
        return jsonify({'message': 'Draft saved securely', 'id': draft_id})
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()

@app.route('/api/drafts', methods=['GET'])
def list_drafts():
    conn = get_db_connection()
    drafts = conn.execute('SELECT id, title, category, created_at FROM drafts WHERE user_id = 1 ORDER BY created_at DESC').fetchall()
    conn.close()
    return jsonify([dict(d) for d in drafts])

@app.route('/api/drafts/<int:id>', methods=['GET'])
def get_draft(id):
    conn = get_db_connection()
    draft = conn.execute('SELECT * FROM drafts WHERE id = ? AND user_id = 1', (id,)).fetchone()
    conn.close()
    
    if not draft:
        return jsonify({'error': 'Not found'}), 404
    
    data = dict(draft)
    data['content'] = decrypt_text(data['output_text_encrypted'])
    # Remove sensitive encrypted field from response
    if 'output_text_encrypted' in data:
        del data['output_text_encrypted']
        
    return jsonify(data)

@app.route('/api/export/<type>/<int:id>', methods=['GET'])
def export_file(type, id):
    conn = get_db_connection()
    draft = conn.execute('SELECT output_text_encrypted, title FROM drafts WHERE id = ?', (id,)).fetchone()
    conn.close()
    if not draft:
        return "Not found", 404
    
    content = decrypt_text(draft['output_text_encrypted'])
    # Sanitize filename
    title = "".join([c for c in draft['title'] if c.isalnum() or c in (' ','-','_')]).strip().replace(' ', '_')
    if not title: title = "document"

    if type == 'pdf':
        buffer = ExportService.to_pdf(content)
        return send_file(buffer, as_attachment=True, download_name=f"{title}.pdf", mimetype='application/pdf')
    elif type == 'word':
        buffer = ExportService.to_docx(content)
        return send_file(buffer, as_attachment=True, download_name=f"{title}.docx", mimetype='application/vnd.openxmlformats-officedocument.wordprocessingml.document')
    
    return "Invalid format", 400

if __name__ == '__main__':
    app.run(debug=True, port=5000)
from flask import Flask, render_template, request, jsonify, send_file, redirect, url_for
import json
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
# Uses the key from .env to encrypt drafts in the database
cipher = Fernet(Config.FERNET_KEY.encode())

def encrypt_text(text: str) -> str:
    """Encrypts a plaintext string."""
    return cipher.encrypt(text.encode()).decode()

def decrypt_text(enc_text: str) -> str:
    """Decrypts a ciphertext string."""
    try:
        return cipher.decrypt(enc_text.encode()).decode()
    except Exception:
        return "[Decryption Failed]"

# --- Routes: Pages ---

@app.route('/')
def index():
    """Render the Marketing Landing Page."""
    return render_template('index.html')

@app.route('/app')
def dashboard():
    """Render the Main App Dashboard."""
    return render_template('dashboard.html')

@app.route('/login')
def login():
    """Placeholder login - Redirects to app for demo."""
    return redirect(url_for('dashboard'))

@app.route('/signup')
def signup():
    """Placeholder signup - Redirects to app for demo."""
    return redirect(url_for('dashboard'))

# --- Routes: API ---

@app.route('/api/templates', methods=['GET'])
def get_templates():
    """Return list of available templates from JSON file."""
    try:
        with open('templates_data.json', 'r') as f:
            templates = json.load(f)
        return jsonify(templates)
    except FileNotFoundError:
        return jsonify([])

@app.route('/api/generate', methods=['POST'])
def generate():
    """
    Main Generation Endpoint.
    Accepts: prompt, category, tone, audience
    Returns: generated text from LLM
    """
    data = request.json
    
    # Extract params with defaults
    tone = data.get('tone', 'Professional')
    audience = data.get('audience', 'General')
    category = data.get('category', 'General')
    user_prompt = data.get('prompt', '')
    context = data.get('context', '') # Existing text for continuation
    
    if not user_prompt and not context:
        return jsonify({'error': 'Prompt is required'}), 400
    
    # 1. Build the system prompt based on category/tone
    system_prompt = LLMService.build_system_prompt(tone, audience, category)
    
    # 2. Call the LLM Service
    result_text = LLMService.generate_text(system_prompt, user_prompt, existing_context=context)
    
    return jsonify({'text': result_text})

@app.route('/api/rewrite', methods=['POST'])
def rewrite():
    """
    Rewrite Endpoint.
    Accepts: text, mode (e.g., 'Shorter', 'Professional')
    """
    data = request.json
    original_text = data.get('text', '')
    mode = data.get('mode', 'Professional') 
    
    if not original_text:
        return jsonify({'error': 'No text provided'}), 400

    # Define specific instructions for rewrite modes
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

# --- Draft Handling (Guest Mode) ---
# NOTE: For this demo, we use User ID 1 as the global "Guest"

@app.route('/api/drafts/save', methods=['POST'])
def save_draft():
    """Saves or Updates a draft in SQLite."""
    data = request.json
    content = data.get('content', '')
    
    if not content:
        return jsonify({'error': 'Content cannot be empty'}), 400

    # Encrypt content before saving
    encrypted_content = encrypt_text(content)
    
    conn = get_db_connection()
    draft_id = data.get('id')
    user_id = 1 # Guest ID
    
    if draft_id:
        # Update existing
        conn.execute('UPDATE drafts SET output_text_encrypted = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?',
                     (encrypted_content, draft_id))
    else:
        # Create new
        cursor = conn.execute(
            'INSERT INTO drafts (user_id, title, category, prompt_json, output_text_encrypted) VALUES (?, ?, ?, ?, ?)',
            (user_id, data['title'], data['category'], json.dumps(data.get('meta', {})), encrypted_content)
        )
        draft_id = cursor.lastrowid
        
    conn.commit()
    conn.close()
    return jsonify({'message': 'Draft saved securely', 'id': draft_id})

@app.route('/api/drafts', methods=['GET'])
def list_drafts():
    """List all drafts for the guest user."""
    conn = get_db_connection()
    drafts = conn.execute('SELECT id, title, category, created_at FROM drafts WHERE user_id = 1 ORDER BY created_at DESC').fetchall()
    conn.close()
    return jsonify([dict(d) for d in drafts])

@app.route('/api/drafts/<int:id>', methods=['GET'])
def get_draft(id):
    """Retrieve a single draft and decrypt it."""
    conn = get_db_connection()
    draft = conn.execute('SELECT * FROM drafts WHERE id = ? AND user_id = 1', (id,)).fetchone()
    conn.close()
    
    if not draft:
        return jsonify({'error': 'Not found'}), 404
    
    data = dict(draft)
    data['content'] = decrypt_text(data['output_text_encrypted'])
        
    # Remove raw encrypted data from response
    del data['output_text_encrypted']
    return jsonify(data)

# --- Export ---
@app.route('/api/export/<type>/<int:id>', methods=['GET'])
def export_file(type, id):
    """Generates a downloadable PDF or DOCX file."""
    conn = get_db_connection()
    draft = conn.execute('SELECT output_text_encrypted, title FROM drafts WHERE id = ?', (id,)).fetchone()
    conn.close()
    
    if not draft:
        return "Not found", 404
        
    content = decrypt_text(draft['output_text_encrypted'])
    # Sanitize title for filename
    title = "".join([c for c in draft['title'] if c.isalnum() or c in (' ','-','_')]).strip().replace(' ', '_')
    
    if type == 'pdf':
        buffer = ExportService.to_pdf(content)
        return send_file(buffer, as_attachment=True, download_name=f"{title}.pdf", mimetype='application/pdf')
    elif type == 'word':
        buffer = ExportService.to_docx(content)
        return send_file(buffer, as_attachment=True, download_name=f"{title}.docx", mimetype='application/vnd.openxmlformats-officedocument.wordprocessingml.document')
    
    return "Invalid format", 400

if __name__ == '__main__':
    app.run(debug=True, port=5000)
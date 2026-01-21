# **Draft Master AI 🪶**

**Draft Master AI** is an enterprise-grade content generation platform designed to help professionals write emails, proposals, legal documents, and more, 10x faster. Built with Flask and powered by Groq's Llama models, it features a secure, responsive, and modern "glassmorphism" interface.

## **🚀 Features**

* **AI-Powered Generation**: Instantly generate high-quality content using advanced LLMs (Groq/Llama 3).  
* **Template Library**: Access 50+ pre-built templates for Business, HR, Marketing, Legal, and Personal use cases.  
* **Smart Customization**: Adjust **Tone** (Professional, Friendly, Urgent, etc.) and **Target Audience**.  
* **AI Editing Tools**: Built-in toolbar to **Fix Grammar**, **Shorten** text, **Polish** style, or **Continue Writing**.  
* **Secure Drafts**: Content is automatically encrypted (AES) before being saved to the database.  
* **Export Options**: One-click export to polished **PDF** and **Word (DOCX)** formats.  
* **Modern UI**: A fully responsive, glassmorphism-inspired dashboard that works seamlessly on Desktop, Tablet, and Mobile.

## **🛠️ Tech Stack**

* **Backend**: Python, Flask  
* **Database**: SQLite (with Fernet encryption for content security)  
* **Frontend**: HTML5, CSS3 (Glassmorphism), Vanilla JavaScript  
* **AI Provider**: Groq API (Llama 3 models)  
* **Utilities**: reportlab (PDF), python-docx (Word), cryptography

## **📋 Prerequisites**

* Python 3.8 or higher  
* A [Groq API Key](https://console.groq.com) (Free tier available)

## **📦 Installation & Setup**

1. **Clone the repository**  
   git clone \<your-repo-url\>  
   cd "write ai"

2. Create a Virtual Environment  
   It is recommended to use a virtual environment to manage dependencies.  
   \# Windows  
   python \-m venv venv  
   venv\\Scripts\\activate

   \# Mac/Linux  
   python3 \-m venv venv  
   source venv/bin/activate

3. **Install Dependencies**  
   pip install \-r requirements.txt

4. Environment Configuration  
   Create a .env file in the project root (you can copy the structure from env.txt).  
   You need to generate a secure **Fernet Key** for database encryption. Run this command:  
   python \-c "from cryptography.fernet import Fernet; print(Fernet.generate\_key().decode())"

   **.env File Content:**  
   \# Security Keys  
   SECRET\_KEY=your\_random\_secret\_string  
   FERNET\_KEY=paste\_the\_generated\_key\_here\_from\_step\_above

   \# LLM Configuration  
   LLM\_PROVIDER=GROQ  
   GROQ\_API\_KEY=your\_groq\_api\_key\_here

5. **Run the Application**  
   python app.py

6. Access the App  
   Open your browser and navigate to:  
   http://127.0.0.1:5000  
   * **Demo Login**: test@example.com / password

## **📂 Project Structure**

write ai/  
├── app.py                  \# Main Flask application entry point  
├── config.py               \# Configuration management  
├── database.py             \# Database connection and initialization  
├── requirements.txt        \# Python dependencies  
├── templates\_data.json     \# JSON database of prompt templates  
├── .env                    \# Environment variables (Sensitive \- do not commit)  
├── services/  
│   ├── export\_service.py   \# Logic for PDF/DOCX generation  
│   └── llm\_service.py      \# Interface for LLM API calls (Groq)  
├── static/  
│   ├── css/  
│   │   └── style.css       \# Main stylesheet (Glassmorphism design)  
│   ├── js/  
│   │   └── app.js          \# Frontend logic (API calls, UI interaction)  
│   └── logo.jpeg           \# App logo  
└── templates/  
    ├── index.html          \# Landing page  
    ├── login.html          \# Authentication page  
    └── dashboard.html      \# Main editor interface

## **🔐 Security Note**

This application implements **Fernet (symmetric encryption)** for the content field in the database. This ensures that user drafts are encrypted at rest. The key is stored in the .env file. If you lose the FERNET\_KEY, previously saved drafts cannot be decrypted.

## **🤝 Contributing**

Contributions, issues, and feature requests are welcome\!

## **📄 License**

This project is open-source and available under the [MIT License](https://www.google.com/search?q=LICENSE).
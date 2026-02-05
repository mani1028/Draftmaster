import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import json
from config import Config

class LLMService:
    @staticmethod
    def generate_text(system_prompt: str, user_prompt: str, existing_context: str = None) -> str:
        """
        Routes to the correct LLM. Updated model ID to fix 404.
        """
        final_prompt = user_prompt
        if existing_context:
            final_prompt = f"CONTEXT (The document so far):\n{existing_context}\n\nTASK (Continue writing):\n{user_prompt}"

        return LLMService._call_groq(system_prompt, final_prompt)

    @staticmethod
    def _call_groq(sys_p: str, user_p: str) -> str:
        if not Config.GROQ_API_KEY:
            return "Error: GROQ_API_KEY is missing in .env or config file."

        url = "https://api.groq.com/openai/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {Config.GROQ_API_KEY}",
            "Content-Type": "application/json"
        }
        
        model_id = 'llama-3.1-8b-instant' 
        
        data = {
            "model": model_id, 
            "messages": [
                {"role": "system", "content": sys_p},
                {"role": "user", "content": user_p}
            ],
            "temperature": 0.6,
            "max_tokens": 4096,
            "top_p": 1
        }
        
        session = requests.Session()
        retry_strategy = Retry(
            total=2,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["POST"]
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("https://", adapter)

        try:
            resp = session.post(url, headers=headers, json=data, timeout=60)
            
            if resp.status_code != 200:
                try:
                    error_json = resp.json()
                    error_msg = error_json.get('error', {}).get('message', resp.text)
                except:
                    error_msg = resp.text
                return f"Groq Error ({resp.status_code}): {error_msg}"
            
            response_json = resp.json()
            choices = response_json.get('choices')
            
            if not choices:
                return "Error: Empty response from AI provider."
                
            return choices[0].get('message', {}).get('content', '')

        except requests.exceptions.Timeout:
            return "Error: AI request timed out."
        except Exception as e:
            return f"Connection Error: {str(e)}"

    @staticmethod
    def build_system_prompt(tone: str, audience: str, category: str) -> str:
        persona_map = {
            "Legal": "Senior Legal Counsel",
            "HR": "Chief Human Resources Officer",
            "Business": "Senior Strategy Consultant",
            "Marketing": "Chief Marketing Officer",
            "Sales": "Senior Sales Director"
        }
        expert_role = persona_map.get(category, "Expert Copywriter")
        
        base = f"You are WriteGenius AI, acting as a {expert_role}."
        
        # Explicit instruction to avoid Markdown stars and use <b> tags for the exporter
        rules = """
        Produce high-quality content only. 
        - Do not include conversational filler.
        - IMPORTANT: Do NOT use markdown stars (**) for bolding. 
        - Instead, use HTML tags <b>...</b> for sections you want to be bold.
        """
        
        return f"{base}\n{rules}\nTONE: {tone}\nAUDIENCE: {audience}\nCATEGORY: {category}"
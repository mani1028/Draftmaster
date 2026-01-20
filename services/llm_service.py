import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import json
from config import Config

class LLMService:
    @staticmethod
    def generate_text(system_prompt: str, user_prompt: str, existing_context: str = None) -> str:
        """
        Routes to the correct LLM. Currently forced to GROQ.
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
        
        model_id = 'llama-3.3-70b-versatile'
        
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
                    error_msg = resp.json().get('error', {}).get('message', resp.text)
                except:
                    error_msg = resp.text
                return f"Groq Error ({resp.status_code}): {error_msg}"
            
            response_json = resp.json()
            choices = response_json.get('choices')
            
            if not choices or not isinstance(choices, list):
                return "Error: Empty response from AI provider."
                
            return choices[0].get('message', {}).get('content', '')

        except requests.exceptions.Timeout:
            return "Error: AI request timed out. Please try again with a shorter prompt."
        except Exception as e:
            return f"Connection Error: {str(e)}"

    @staticmethod
    def build_system_prompt(tone: str, audience: str, category: str) -> str:
        persona_map = {
            "Legal": "Senior Legal Counsel",
            "HR": "Chief Human Resources Officer",
            "Business": "Senior Strategy Consultant",
            "Marketing": "Chief Marketing Officer",
            "Sales": "Senior Sales Director",
            "Academic": "University Professor",
            "Student": "Academic Advisor",
            "Personal": "Communication Coach",
            "Proposal": "Venture Capital Analyst"
        }
        expert_role = persona_map.get(category, "Expert Copywriter")
        
        base = f"You are WriteGenius AI, acting as a {expert_role}. Produce high-quality, human-like content."
        
        rules = """
        RULES:
        - No fluff. Be concise and high-impact.
        - Adapt vocabulary strictly to the audience.
        - Use professional formatting (bold key points).
        - Do NOT use phrases like "I hope this finds you well" or "In conclusion".
        - Do NOT include pre-text (e.g., "Here is the email"). Output ONLY the content.
        """
        
        return f"{base}\n{rules}\nTONE: {tone}\nAUDIENCE: {audience}\nCATEGORY: {category}"
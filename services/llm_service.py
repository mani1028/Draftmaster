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
        'existing_context' is used for the 'Continue Writing' feature.
        """
        
        final_prompt = user_prompt
        if existing_context:
            final_prompt = f"CONTEXT (The document so far):\n{existing_context}\n\nTASK (Continue writing):\n{user_prompt}"

        # Direct Groq Call for speed and quality
        return LLMService._call_groq(system_prompt, final_prompt)

    @staticmethod
    def _call_groq(sys_p: str, user_p: str) -> str:
        if not Config.GROQ_API_KEY:
            return "Error: GROQ_API_KEY is missing in .env file."

        url = "https://api.groq.com/openai/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {Config.GROQ_API_KEY}",
            "Content-Type": "application/json"
        }
        
        # Use config model if available, else fallback to the stable version
        model_id = getattr(Config, 'GROQ_MODEL', 'llama-3.3-70b-versatile')
        
        data = {
            "model": model_id, 
            "messages": [
                {"role": "system", "content": sys_p},
                {"role": "user", "content": user_p}
            ],
            "temperature": 0.6, # Slightly lowered for more professional/deterministic consistency
            "max_tokens": 4096, # Increased to prevent cutoff on long documents
            "top_p": 1          # Explicit sampling for better quality
        }
        
        # Implement Retry Logic for network stability
        session = requests.Session()
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["POST"]
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("https://", adapter)

        try:
            # Increased timeout to 60s to handle 70B model generation spikes
            resp = session.post(url, headers=headers, json=data, timeout=60)
            
            if resp.status_code != 200:
                return f"Groq Error ({resp.status_code}): {resp.text}"
            
            # Safer JSON parsing
            response_json = resp.json()
            choices = response_json.get('choices')
            
            if not choices or not isinstance(choices, list):
                return f"Groq Error: Unexpected API response format: {str(response_json)[:100]}..."
                
            return choices[0].get('message', {}).get('content', 'Error: Empty response content')

        except Exception as e:
            return f"Connection Error: {str(e)}"

    @staticmethod
    def build_system_prompt(tone: str, audience: str, category: str) -> str:
        """
        Constructs a high-performance system prompt for professional output.
        """
        # 1. Dynamic Expert Persona based on Category
        persona_map = {
            "Legal": "Senior Legal Counsel",
            "HR": "Chief Human Resources Officer (CHRO)",
            "Business": "Senior Strategy Consultant",
            "Marketing": "Chief Marketing Officer (CMO)",
            "Sales": "Senior Sales Director",
            "Academic": "Ivy League Professor",
            "Student": "Academic Advisor",
            "Personal": "Empathetic Communication Coach",
            "Proposal": "Venture Capital Analyst"
        }
        # Default to Expert Copywriter if category not found or is 'General'
        expert_role = persona_map.get(category, "World-Class Copywriter and Editor")
        
        base_instruction = f"You are WriteGenius AI, acting as a {expert_role}. Your goal is to produce top-tier, human-quality content that beats standard AI outputs."

        # 2. Advanced Quality Standards (The "Secret Sauce" for better writing)
        quality_standards = """
        QUALITY STANDARDS:
        - **Human-Like Flow**: Avoid robotic transitions. Use varied sentence structures (short punchy sentences mixed with complex ones).
        - **No Fluff**: Cut unnecessary adjectives, adverbs, and filler words. Be concise and high-impact.
        - **Specific & Actionable**: Avoid vague generalizations. Use concrete language and examples where applicable.
        - **Context Awareness**: Adapt vocabulary strictly to the target audience (e.g., use technical jargon for experts, simple terms for laypeople).
        - **Forbidden Phrases**: Do not use "I hope this email finds you well", "In conclusion", "delve into", "tapestry", "landscape", or "game-changer" unless strictly necessary.
        """
        
        formatting_rules = """
        FORMATTING RULES:
        - Use professional, clean layout (white space is important).
        - Use **bold** for key metrics, dates, or action items.
        - For Emails: Standard business format (Subject -> Salutation -> Hook -> Value -> Call to Action -> Sign-off).
        - For Proposals: Logical hierarchy (Executive Summary -> Problem -> Solution -> ROI).
        - NO Markdown tables unless explicitly requested.
        - NO pre-text (e.g., "Here is the draft"). Start directly with the content.
        """

        # 3. Tone Nuances
        tone_instruction = f"TONE: {tone}."
        if tone == "Luxury / Enterprise":
            tone_instruction += " Use sophisticated, C-suite level vocabulary. Tone should be understated yet powerful. Zero errors. Focus on exclusivity and premium value."
        elif tone == "Sales-driven":
            tone_instruction += " Use the AIDA framework (Attention, Interest, Desire, Action). Focus heavily on benefits, ROI, and handling objections proactively."
        elif tone == "Emotional":
            tone_instruction += " Focus on deep connection, empathy, and sincerity. Use sensory language and vulnerability where appropriate."
        elif tone == "Confident":
            tone_instruction += " Use active voice. Be direct, authoritative, and decisive without being arrogant."
        elif tone == "Legal":
            tone_instruction += " Use precise legal terminology. Be objective, formal, risk-averse, and unambiguous."
        elif tone == "Friendly":
            tone_instruction += " Be warm, approachable, and conversational, but maintain professional boundaries."

        audience_instruction = f"TARGET AUDIENCE: {audience}."

        return f"{base_instruction}\n{quality_standards}\n{tone_instruction}\n{audience_instruction}\nCATEGORY: {category}\n{formatting_rules}"
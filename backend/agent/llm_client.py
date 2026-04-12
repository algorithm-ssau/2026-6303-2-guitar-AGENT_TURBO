"""КЛИЕНТ GROQ LLM"""
import os
from groq import Groq
from backend.agent.param_extractor import build_search_prompt, extract_params_from_llm_response

class LLMClient:
    def __init__(self):
        self.api_key = os.getenv("GROQ_API_KEY")
        if not self.api_key:
            raise ValueError("GROQ_API_KEY environment variable is not set")
        self.client = Groq(api_key=self.api_key)
        self.model = os.getenv("LLM_MODEL", "llama-3.3-70b-versatile")

    def ask(self, user_message: str, system_prompt: str, history: list = None) -> str:
        messages = [
            {"role": "system", "content": system_prompt},
        ]
        # Добавляем историю диалога (если есть)
        if history:
            messages.extend(history)
        messages.append({"role": "user", "content": user_message})
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.0
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"Error: {str(e)}"

    def summarize(self, messages: list, prompt: str) -> str:
        """Делает суммаризацию переданных сообщений."""
        transcript = "\n".join([f"{msg['role']}: {msg['content']}" for msg in messages])
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": prompt},
                    {"role": "user", "content": transcript}
                ],
                temperature=0.0
            )
            return response.choices[0].message.content
        except Exception:
            return ""

    def extract_search_params(self, user_message: str) -> dict:
        mapping_path = os.path.join(os.path.dirname(__file__), "../../docs/MAPPING.md")
        mapping_table = ""
        if os.path.exists(mapping_path):
            with open(mapping_path, "r", encoding="utf-8") as f:
                mapping_table = f.read()

        prompt = build_search_prompt(user_message, mapping_table)
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.0,
                response_format={"type": "json_object"}
            )
            content = response.choices[0].message.content
            return extract_params_from_llm_response(content)
        except Exception:
            return extract_params_from_llm_response("invalid")


def get_llm_client():
    """Compatibility wrapper for service.py"""
    return LLMClient().client

def get_llm_model():
    return os.getenv("LLM_MODEL", "llama-3.3-70b-versatile")

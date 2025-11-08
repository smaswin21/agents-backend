"""
LLM Client helper using LiteLLM proxy.
Handles OpenAI client initialization with proxy configuration.
"""
import os
import openai
from typing import Optional
from dotenv import load_dotenv

load_dotenv()

_client: Optional[openai.OpenAI] = None

def get_llm_client() -> Optional[openai.OpenAI]:
    """
    Get or create OpenAI client configured for LiteLLM proxy.
    
    Returns:
        OpenAI client instance, or None if API key not configured
    """
    global _client
    
    if _client is None:
        api_key = os.getenv("OPENAI_API_KEY")
        base_url = os.getenv("OPENAI_BASE_URL")
        
        if not api_key:
            return None  # LLM not configured
        
        _client = openai.OpenAI(
            api_key=api_key,
            base_url=base_url
        )
    
    return _client


async def call_llm(
    prompt: str,
    model: str = None,
    system_message: str = None
) -> Optional[str]:
    """
    Make an async LLM call using the LiteLLM proxy.
    
    Args:
        prompt: User prompt/message
        model: Model name (defaults to OPENAI_MODEL env var or "gpt-5-nano")
        system_message: Optional system message
        
    Returns:
        LLM response text, or None if error
    """
    client = get_llm_client()
    if not client:
        return None
    
    if model is None:
        model = os.getenv("OPENAI_MODEL", "gpt-5-nano")
    
    messages = []
    
    if system_message:
        messages.append({
            "role": "system",
            "content": system_message
        })
    
    messages.append({
        "role": "user",
        "content": prompt
    })
    
    try:
        response = client.chat.completions.create(
            model=model,
            messages=messages
        )
        
        return response.choices[0].message.content
    except Exception as e:
        print(f"LLM call error: {e}")
        return None
# llm.py
from langchain_openai import ChatOpenAI
from .config import OPENAI_API_KEY, OPENAI_MODEL, OPENAI_BASE_URL

def make_llm():
    # temperature=0 # deterministic agent behavior
    return ChatOpenAI(
        model=OPENAI_MODEL,
        api_key=OPENAI_API_KEY,
        temperature=0,
        base_url=OPENAI_BASE_URL
    )

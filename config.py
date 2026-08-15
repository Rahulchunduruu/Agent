import os
from dotenv import load_dotenv

load_dotenv()

class Config:   
    # Groq_api_key = os.getenv('Groq_api_key')  # no longer used — brain switched to kimi-k3
    KIMI_API_KEY = os.getenv("kimi-k3-free")
    KIMI_BASE_URL = os.getenv("KIMI_BASE_URL", "https://api.tokenrouter.com/v1")
    KIMI_MODEL = os.getenv("KIMI_MODEL", "qwen/qwen3.8-max-free")
    VISION_MODEL = os.getenv("VISION_MODEL", "google/gemini-3.5-flash-lite")
    TAVILY_API_KEY=os.getenv('TAVILY_API_KEY')
    OPENWEATHER_API_KEY=os.getenv('OPENWEATHER_API_KEY')
    UPSTASH_REDIS_REST_URL = os.getenv("UPSTASH_REDIS_REST_URL")
    UPSTASH_REDIS_REST_TOKEN = os.getenv("UPSTASH_REDIS_REST_TOKEN")
    BROWSER_USE_API_KEY = os.getenv("BROWSER_USE_API_KEY")
    Mem0_api_key = os.getenv("Mem0")
    GROQ_API_KEY = os.getenv("GROQ_API_KEY")

    if not KIMI_API_KEY:
        raise ValueError("kimi-k3-free API key not found in .env file. Please add your API key.")

    if not TAVILY_API_KEY:
        raise ValueError("TAVILY_API_KEY not found in .env file. Please add your API key.")
    
    if not OPENWEATHER_API_KEY:
        raise ValueError("OPENWEATHER_API_KEY not found in .env file. Please add your API key.")

    if not BROWSER_USE_API_KEY:
        raise ValueError("BROWSER_USE_API_KEY not found in .env file. Please add your API key.")
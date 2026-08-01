import os
from dotenv import load_dotenv

load_dotenv()

class Config:   
    Groq_api_key = os.getenv('Groq_api_key')
    TAVILY_API_KEY=os.getenv('TAVILY_API_KEY')
    OPENWEATHER_API_KEY=os.getenv('OPENWEATHER_API_KEY')
    UPSTASH_REDIS_REST_URL = os.getenv("UPSTASH_REDIS_REST_URL")
    UPSTASH_REDIS_REST_TOKEN = os.getenv("UPSTASH_REDIS_REST_TOKEN")
    Mem0_api_key = os.getenv("Mem0")

    if not Groq_api_key:
        raise ValueError("Groq_api_key not found in .env file. Please add your API key.")

    if not TAVILY_API_KEY:
        raise ValueError("TAVILY_API_KEY not found in .env file. Please add your API key.")
    
    if not OPENWEATHER_API_KEY:
        raise ValueError("OPENWEATHER_API_KEY not found in .env file. Please add your API key.")
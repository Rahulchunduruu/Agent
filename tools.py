from langchain_core.tools import tool
from langchain_community.tools import DuckDuckGoSearchRun
from tavily import TavilyClient
from mem0 import MemoryClient
from datetime import datetime
from config import Config
import subprocess
import os



search = DuckDuckGoSearchRun()
mem0_client = MemoryClient(api_key=Config.Mem0_api_key)
USER_ID = "rahul"

@tool
def web_search(query: str) -> str:
    """Use this to search the internet for current events, latest news, real-time information, or anything that requires up-to-date web results."""
    return search.run(query)

@tool
def web_search_tavily(query: str, depth: str = "basic",max_results:int=10) -> str:
    """Use this to Advance  search the internet for current events, latest news, real-time information, or anything that requires up-to-date web results. More advanced than duckduckgo."""
    client = TavilyClient(api_key=Config.TAVILY_API_KEY)
    response = client.search(query=query, depth=depth,max_results=max_results)
    return response

@tool
def file_system(cmd: str) -> str:
    """Use this to run shell/terminal commands on the local machine, such as listing files, reading files, or executing scripts. Do NOT use this for web searches."""
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    return (
        f"Return code: {result.returncode}\n\n"
        f"STDOUT:\n{result.stdout}\n\n"
        f"STDERR:\n{result.stderr}"
    )

@tool
def get_datetime() -> str:
    """Get the current date and time."""
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

@tool
def memory_helper(query: str) -> str:
    """Use this for ANY memory related request - automatically saves new facts from user, or retrieves relevant information when user asks about something previously shared."""
    results = mem0_client.search(query, user_id=USER_ID)
    if results:
        return "\n".join([r["memory"] for r in results])
    return "No relevant memory found."

@tool
def save_memory(information: str) -> str:
    """Use this to save any personal information or facts the user shares (name, city, preferences, stack, etc.). Automatically extracts and stores all facts."""
    mem0_client.add(information, user_id=USER_ID)
    return f"Memory saved: {information}"


tools_list = [web_search, file_system, get_datetime, memory_helper, save_memory]

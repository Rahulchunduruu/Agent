"""
tools package — all agent tools organized by category.

Modules:
    search_tools   -> web_search, web_search_tavily, scrape_webpage
    file_tools     -> file_system, write_file, read_file
    email_tools    -> send_email, gmail_search, gmail_read
    utility_tools  -> get_datetime, calculator, get_weather
    code_tools     -> code_executor
    browser_tools  -> browser_agent
    image_tools    -> image_describe

Usage:
    from tools import tools_list          # all 15 tools as a list
    from tools import web_search          # individual tool imports also work
"""

import nest_asyncio
nest_asyncio.apply()  # allow nested asyncio loops (LangGraph / Streamlit event-loop conflict fix)

from tools.search_tools import web_search, web_search_tavily, scrape_webpage
from tools.file_tools import file_system, write_file, read_file
from tools.email_tools import send_email, gmail_search, gmail_read
from tools.utility_tools import get_datetime, calculator, get_weather
from tools.code_tools import code_executor
from tools.browser_tools import browser_agent
from tools.image_tools import image_describe

tools_list = [
    image_describe,
    web_search,
    web_search_tavily,
    scrape_webpage,
    code_executor,
    file_system,
    write_file,
    read_file,
    get_datetime,
    calculator,
    get_weather,
    send_email,
    gmail_search,
    gmail_read,
    browser_agent,
]

__all__ = [
    "tools_list",
    "image_describe",
    "web_search",
    "web_search_tavily",
    "scrape_webpage",
    "code_executor",
    "file_system",
    "write_file",
    "read_file",
    "get_datetime",
    "calculator",
    "get_weather",
    "send_email",
    "gmail_search",
    "gmail_read",
    "browser_agent",
]

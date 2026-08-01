# Standard Library
from datetime import datetime
import subprocess
import os
import ast
import math

# LangChain Core
from langchain_core.tools import tool

# LangChain Community - Tools
from langchain_community.tools import DuckDuckGoSearchRun
from langchain_community.tools.gmail import GmailSendMessage
import langchain_community.tools.gmail as gmail_send_module

# LangChain Community - Loaders & Transformers
from langchain_community.document_loaders import AsyncChromiumLoader
from langchain_community.document_transformers import BeautifulSoupTransformer

# Google API
from googleapiclient.discovery import Resource
from langchain_community.tools.gmail.utils import build_resource_service, get_gmail_credentials

# Third Party
from tavily import TavilyClient
from mem0 import MemoryClient
import requests
import markdown as md

# Local
from config import Config

# Fix for pydantic v2 + Python 3.14
gmail_send_module.Resource = Resource
GmailSendMessage.model_rebuild()

search = DuckDuckGoSearchRun()
mem0_client = MemoryClient(api_key=Config.Mem0_api_key)
USER_ID = "rahul"


gmail_send_module.Resource = Resource
GmailSendMessage.model_rebuild()

@tool
def web_search(query: str) -> str:
    """Use this to search the internet for current events, latest news, real-time information, or anything that requires up-to-date web results."""
    return search.run(query)

@tool
def web_search_tavily(query: str, depth: str = "basic", max_results: int = 10) -> str:
    """Use this to advance search the internet for current events, latest news, real-time information, or anything that requires up-to-date web results. More advanced than DuckDuckGo."""
    client = TavilyClient(api_key=Config.TAVILY_API_KEY)
    response = client.search(query=query, depth=depth, max_results=max_results)
    return str(response)

@tool
def scrape_webpage(url: str) -> str:
    """Scrapes and returns clean text content from a webpage URL."""
    try:
        loader = AsyncChromiumLoader([url])
        docs = loader.load()

        bs_transformer = BeautifulSoupTransformer()
        docs_transformed = bs_transformer.transform_documents(
            docs,
            tags_to_extract=["p", "h1", "h2", "h3", "li", "span"]
        )

        return docs_transformed[0].page_content if docs_transformed else "No content found."

    except Exception as e:
        return f"Error scraping {url}: {str(e)}"
    
@tool
def file_system(cmd: str) -> str:
    """Use this to run shell/terminal commands on the local machine, such as listing files, reading files, or executing scripts. Do NOT use this for web searches."""
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)

    if result.returncode != 0:
        return f"Error: {result.stderr.strip()}"

    return result.stdout.strip() or "Command executed successfully."

@tool
def get_datetime() -> str:
    """Get the current date and time."""
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


@tool
def calculator(expression: str) -> str:
    """Safely evaluate arithmetic expressions and common math functions. Supports +, -, *, /, %, //, **, parentheses, decimals, and functions like sqrt, sin, cos, tan, log, log10, abs, floor, ceil, factorial."""
    try:
        cleaned = (expression or "").strip().replace("^", "**")
        if not cleaned:
            return "Error: Please provide a math expression."

        allowed_functions = {
            "abs": abs,
            "sqrt": math.sqrt,
            "sin": math.sin,
            "cos": math.cos,
            "tan": math.tan,
            "log": math.log,
            "log10": math.log10,
            "floor": math.floor,
            "ceil": math.ceil,
            "factorial": math.factorial,
            "pow": pow,
        }

        allowed_names = {"pi": math.pi, "e": math.e}
        tree = ast.parse(cleaned, mode="eval")

        def _eval(node):
            if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
                return node.value
            if isinstance(node, ast.Name):
                if node.id in allowed_names:
                    return allowed_names[node.id]
                raise ValueError(f"Unsupported name: {node.id}")
            if isinstance(node, ast.BinOp):
                left = _eval(node.left)
                right = _eval(node.right)
                if isinstance(node.op, ast.Add):
                    return left + right
                if isinstance(node.op, ast.Sub):
                    return left - right
                if isinstance(node.op, ast.Mult):
                    return left * right
                if isinstance(node.op, ast.Div):
                    return left / right
                if isinstance(node.op, ast.FloorDiv):
                    return left // right
                if isinstance(node.op, ast.Mod):
                    return left % right
                if isinstance(node.op, ast.Pow):
                    return left ** right
                raise ValueError("Unsupported operator")
            if isinstance(node, ast.UnaryOp):
                value = _eval(node.operand)
                if isinstance(node.op, ast.UAdd):
                    return +value
                if isinstance(node.op, ast.USub):
                    return -value
                raise ValueError("Unsupported unary operator")
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
                func_name = node.func.id
                if func_name not in allowed_functions:
                    raise ValueError(f"Unsupported function: {func_name}")
                args = [_eval(arg) for arg in node.args]
                if func_name in {"abs", "sqrt", "sin", "cos", "tan", "log", "log10", "floor", "ceil", "factorial"}:
                    if len(args) != 1:
                        raise ValueError(f"{func_name} expects exactly one argument")
                if func_name == "pow":
                    if len(args) != 2:
                        raise ValueError("pow expects exactly two arguments")
                return allowed_functions[func_name](*args)
            raise ValueError("Unsupported expression")

        result = _eval(tree.body)
        return str(result)
    except Exception as e:
        return f"Error: {str(e)}"


@tool
def get_weather(city: str = "Guntur", country: str = "India") -> str:
    """Get current weather for health-related queries like heatstroke,
    seasonal allergies, humidity-related illness, cold weather precautions.
    city: Name of the city
    country: Name of the country
    """
    try:
        API_KEY = Config.OPENWEATHER_API_KEY

        # Step 1: Current Weather
        weather_url = (
            f"http://api.openweathermap.org/data/2.5/weather"
            f"?q={city},{country}&appid={API_KEY}&units=metric"
        )
        weather = requests.get(weather_url).json()

        if str(weather.get("cod")) != "200":
            return f"City not found: {weather.get('message', 'Unknown error')}"

        lat = weather["coord"]["lat"]
        lon = weather["coord"]["lon"]

        # Step 2: AQI (free tier supports this)
        aqi_url = (
            f"http://api.openweathermap.org/data/2.5/air_pollution"
            f"?lat={lat}&lon={lon}&appid={API_KEY}"
        )
        aqi_res = requests.get(aqi_url).json()
        aqi_index = aqi_res["list"][0]["main"]["aqi"]
        aqi_level = {1: "Good", 2: "Fair", 3: "Moderate", 4: "Poor", 5: "Very Poor"}

        return (
            f"City: {weather['name']}, {country} | "
            f"Temp: {weather['main']['temp']}°C | "
            f"Feels Like: {weather['main']['feels_like']}°C | "
            f"Humidity: {weather['main']['humidity']}% | "
            f"Condition: {weather['weather'][0]['description'].title()} | "
            f"Wind: {weather['wind']['speed']} m/s | "
            f"AQI: {aqi_level.get(aqi_index, 'Unknown')}"
        )

    except Exception as e:
        return f"Weather unavailable: {str(e)}"

def _build_professional_html_email(message: str) -> str:
    """Convert a plain or markdown message into a polished HTML email body."""
    if not message or not message.strip():
        return "<p></p>"

    if "<html" in message.lower() or "<body" in message.lower():
        return message.strip()

    clean_message = message.strip()
    converted_body = md.markdown(clean_message, extensions=["extra"])

    return f"""
    <html>
        <body style="font-family: Arial, sans-serif; font-size: 14px; color: #222; max-width: 700px; margin: 0; padding: 16px;">
            <style>
                p {{ margin: 0 0 6px 0; padding: 0; }}
                ul {{ margin: 4px 0 6px 0; padding-left: 18px; }}
                li {{ margin: 0; padding: 0; }}
                br {{ line-height: 1.2; }}
            </style>
            {converted_body}
        </body>
    </html>
    """


@tool
def send_email(to: list, subject: str, message: str):
    """Send a polished email via Gmail. Requires to, subject, and message parameters."""
    credentials = get_gmail_credentials(
        token_file="token.json",
        scopes=["https://mail.google.com/"],
        client_secrets_file="credentials.json",
    )
    api_resource = build_resource_service(credentials=credentials)
    gmail_tool = GmailSendMessage(api_resource=api_resource)

    html_message = _build_professional_html_email(message)

    return gmail_tool.run({
        "to": to,
        "subject": subject,
        "message": html_message
    })


@tool
def code_executor(code: str, language: str = "python") -> str:
    """Executes code and returns the output. Supports python and bash."""
    try:
        if language == "python":
            result = subprocess.run(
                [sys.executable, "-c", code],
                capture_output=True, text=True, timeout=15
            )
        elif language == "bash":
            result = subprocess.run(
                code, shell=True,
                capture_output=True, text=True, timeout=15
            )
        else:
            return f"Unsupported language: {language}"

        return result.stdout if result.stdout else result.stderr

    except subprocess.TimeoutExpired:
        return "Error: Code execution timed out (15s limit)"
    except Exception as e:
        return f"Error: {str(e)}"

tools_list = [web_search,web_search_tavily,scrape_webpage, code_executor,file_system, get_datetime, calculator, get_weather,send_email]


# Standard Library
from datetime import datetime
import subprocess
import base64
import asyncio
import os
import ast
import math
import sys

import nest_asyncio
nest_asyncio.apply()  # allow nested asyncio loops (LangGraph / Streamlit event-loop conflict fix)
import asyncio

# LangChain Core
from langchain_core.tools import tool

# LangChain Community - Tools
from langchain_community.tools import DuckDuckGoSearchRun
from langchain_community.tools.gmail import GmailSendMessage, GmailSearch
import langchain_community.tools.gmail as gmail_send_module

# LangChain Community - Loaders & Transformers
from langchain_community.document_loaders import AsyncChromiumLoader
from langchain_community.document_transformers import BeautifulSoupTransformer


# Google API
from googleapiclient.discovery import Resource
from langchain_community.tools.gmail.utils import build_resource_service
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow

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
GmailSearch.model_rebuild()

search = DuckDuckGoSearchRun()
mem0_client = MemoryClient(api_key=Config.Mem0_api_key)
USER_ID = "rahul"


def _get_gmail_creds():
    """Auto-refreshes expired token. Re-auths via browser if revoked."""
    SCOPES = ["https://mail.google.com/"]
    creds = None
    if os.path.exists("token.json"):
        creds = Credentials.from_authorized_user_file("token.json", SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
            except Exception:
                os.remove("token.json")
                creds = None
        if not creds:
            flow = InstalledAppFlow.from_client_secrets_file("credentials.json", SCOPES)
            creds = flow.run_local_server(port=0)
        with open("token.json", "w") as f:
            f.write(creds.to_json())
    return creds


@tool
def web_search(query: str) -> str:
    """Use this to search the internet for current events, latest news, real-time information, or anything that requires up-to-date web results."""
    return search.run(query)


@tool
def web_search_tavily(query: str, max_results: int = 5, search_depth: str = "advanced", start_date: str = None, end_date: str = None) -> str:
    """Use this for advanced web search with date filtering for current events, latest news, and real-time information. More powerful than DuckDuckGo."""
    client = TavilyClient(api_key=Config.TAVILY_API_KEY)
    response = client.search(
        query=query,
        search_depth=search_depth,
        max_results=max_results,
        start_published_date=start_date,
        end_published_date=end_date
    )
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
    """
    Execute shell/terminal commands on the local machine. Works on Windows, Linux, and Mac.

    Common Commands (use correct OS syntax):

    LIST FILES:
    - Windows: 'dir'
    - Linux/Mac: 'ls -la'

    READ FILE:
    - Windows: 'type filename.txt'
    - Linux/Mac: 'cat filename.txt'

    DELETE FILE:
    - Windows: 'del filename.txt'
    - Linux/Mac: 'rm filename.txt'

    CREATE FOLDER:
    - Both: 'mkdir foldername'

    WRITE FILE (small content ONLY - under ~50 lines):
    - python -c "open('file.txt','w',encoding='utf-8').write('your content')"
    - For LARGE content (big files, 1000s of lines), NEVER use shell commands -
      use the write_file tool instead (bypasses the Windows 8191-char cmd limit).

    APPEND TO FILE (universal):
    - python -c "open('file.txt','a',encoding='utf-8').write('more content')"

    CHECK FILE EXISTS (universal):
    - python -c "import os; print(os.path.exists('file.txt'))"

    RUN PYTHON SCRIPT (universal):
    - 'python script.py'

    GET CURRENT DIRECTORY (universal):
    - python -c "import os; print(os.getcwd())"

    STRICT RULES:
    - NEVER use triple quotes (''' or \"\"\") in any command
    - NEVER use this for web searches — use web_search instead
    - NEVER use this for calculations — use calculator instead
    - NEVER pass large file content (more than ~50 lines) through this tool — use write_file instead
    - ALWAYS specify encoding='utf-8' when writing files via python -c
    - For multiline content, use \\n instead of actual newlines
    - Commands automatically time out after 60 seconds
    """
    try:
        result = subprocess.run(
            cmd,
            shell=True,
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='replace',
            timeout=60
        )
        if result.returncode != 0:
            return f"Error: {result.stderr.strip()}"
        return result.stdout.strip() or "Command executed successfully."
    except subprocess.TimeoutExpired:
        return "Error: Command timed out after 60 seconds."
    except Exception as e:
        return f"Error: {str(e)}"


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

        weather_url = (
            f"http://api.openweathermap.org/data/2.5/weather"
            f"?q={city},{country}&appid={API_KEY}&units=metric"
        )
        weather = requests.get(weather_url).json()

        if str(weather.get("cod")) != "200":
            return f"City not found: {weather.get('message', 'Unknown error')}"

        lat = weather["coord"]["lat"]
        lon = weather["coord"]["lon"]

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
    credentials = _get_gmail_creds()
    api_resource = build_resource_service(credentials=credentials)
    gmail_tool = GmailSendMessage(api_resource=api_resource)
    html_message = _build_professional_html_email(message)
    return gmail_tool.run({
        "to": to,
        "subject": subject,
        "message": html_message
    })


@tool
def gmail_search(query: str, max_results: int = 5) -> str:
    """
    Search Gmail messages and return matching emails with their IDs, subjects, senders, dates, and snippets.

    Uses Gmail search operators in 'query', e.g.:
    - 'from:someone@example.com'
    - 'subject:invoice'
    - 'is:unread'
    - 'newer_than:7d'
    - 'has:attachment'

    ALWAYS use this first to find emails. Use gmail_read with the returned message ID to see the full body.
    """
    try:
        credentials = _get_gmail_creds()
        api_resource = build_resource_service(credentials=credentials)
        search_tool = GmailSearch(api_resource=api_resource)
        results = search_tool.run({
            "query": query,
            "resource": "messages",
            "max_results": max_results,
        })
        return str(results)
    except Exception as e:
        return f"Error searching Gmail: {str(e)}"


def _extract_email_body(payload) -> str:
    """Recursively decode text/plain (or HTML fallback) body from a Gmail message payload."""
    mime = payload.get("mimeType", "")
    data = (payload.get("body") or {}).get("data")
    if data and mime.startswith("text/"):
        return base64.urlsafe_b64decode(data).decode("utf-8", errors="replace")
    for part in payload.get("parts", []) or []:
        text = _extract_email_body(part)
        if text:
            return text
    return ""


@tool
def gmail_read(message_id: str) -> str:
    """
    Read the full content of a single Gmail message by its message ID.
    Get the message ID from gmail_search results first.
    Returns sender, subject, date, and the full plain-text body.
    """
    try:
        credentials = _get_gmail_creds()
        api_resource = build_resource_service(credentials=credentials)
        msg = (
            api_resource.users().messages()
            .get(userId="me", id=message_id, format="full")
            .execute()
        )
        headers = {h["name"].lower(): h["value"] for h in msg.get("payload", {}).get("headers", [])}
        body = _extract_email_body(msg.get("payload", {}))
        return (
            f"From: {headers.get('from', 'Unknown')}\n"
            f"To: {headers.get('to', 'Unknown')}\n"
            f"Date: {headers.get('date', 'Unknown')}\n"
            f"Subject: {headers.get('subject', '(no subject)')}\n\n"
            f"Body:\n{body.strip() or '(empty body)'}"
        )
    except Exception as e:
        return f"Error reading Gmail message: {str(e)}"


@tool
def browser_agent(task: str) -> str:
    """
    Controls a real web browser to complete a task described in plain English.
    Use this when a job needs INTERACTION with a live webpage — scrape_webpage only fetches static HTML.

    Use `browser_agent` when the task needs to:
    - Click buttons, links, tabs, or dismiss popups/cookie banners
    - Fill and submit forms: text inputs, textareas, dropdowns/selects, checkboxes, radio buttons
    - Log in to a website (provide username/password in the task text)
    - Navigate across multiple pages (pagination, multi-step wizards, next/previous)
    - Scrape JavaScript-heavy pages that render content dynamically (scrapers fail on these)
    - Scroll infinite feeds, expand collapsed sections, open dropdown menus
    - Extract data that only appears AFTER interaction (post-login dashboards, cart totals, search results)

    Examples:
    - browser_agent('Go to https://twitter.com/login, log in with user X and pass Y, then read my 3 latest notifications')
    - browser_agent('Open https://example-shop.com, search for "running shoes", filter by size 10, and list the top 5 names and prices')
    - browser_agent('Fill the contact form at https://site.com/contact with name John, email john@x.com, message "Hello", submit it, and confirm the success message')

    Rules:
    - ALWAYS include the full URL (with https://) in the task.
    - Describe the goal clearly; the agent decides which elements to click/fill itself.
    - For logins, include credentials explicitly in the task string.
    - Ask for a specific final answer (names, totals, confirmation text) so the agent returns useful data.
    - NEVER use this for simple static-page reading — use scrape_webpage instead. It is slower but cheaper.
    - Limited to 20 steps; very long multi-page flows may be cut short.
    """
    try:
        from browser_use import Agent as BrowserAgent
        from browser_use.browser.session import BrowserSession
        from browser_use.llm.openai.chat import ChatOpenAI as BrowserLLM

        llm = BrowserLLM(
            model=Config.KIMI_MODEL,
            api_key=Config.KIMI_API_KEY,
            base_url=Config.KIMI_BASE_URL,
            timeout=120,
        )

        async def _run() -> str:
            agent = BrowserAgent(
                task=task,
                llm=llm,
                browser=BrowserSession(headless=False)
            )
            history = await asyncio.wait_for(agent.run(max_steps=20), timeout=300)
            result = history.final_result()
            return str(result) if result else "Browser task finished but returned no result."

        return asyncio.get_event_loop().run_until_complete(_run())
    except asyncio.TimeoutError:
        return "Error: browser_agent timed out (300s limit). The task was too complex for 20 steps."
    except Exception as e:
        return f"Error in browser_agent: {type(e).__name__}: {e}"

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




def _local_image_analysis(image_bytes: bytes, source: str) -> str:
    """Fallback: basic image info via PIL when the vision API is unavailable."""
    import io as _io
    from collections import Counter
    from PIL import Image
    img = Image.open(_io.BytesIO(image_bytes))
    width, height = img.size
    fmt = img.format or "unknown"
    mode = img.mode
    small = img.convert("RGB").resize((50, 50))
    pixels = list(small.getdata())

    def bucket(p):
        return (p[0] // 32 * 32, p[1] // 32 * 32, p[2] // 32 * 32)

    counts = Counter(bucket(p) for p in pixels)
    top = counts.most_common(3)
    color_names = ["RGB({},{},{})".format(r, g, b) for (r, g, b), _ in top]
    return (
        "[Local analysis - vision API unavailable]\n"
        "Source: {}\n"
        "Dimensions: {}x{} px\n"
        "Format: {} | Mode: {}\n"
        "Dominant colors: {}".format(source, width, height, fmt, mode, ", ".join(color_names))
    )


@tool
def image_describe(image_path: str = None, image_url: str = None, prompt: str = "Describe this image in detail.") -> str:
    """Describe/analyze an image using a vision AI model.
    Provide either a local file path (image_path) or a web URL (image_url).
    Optionally customize what to look for via the prompt parameter.
    Falls back to basic local analysis (dimensions, colors) if the vision API is unavailable.
    """
    import base64 as _b64
    import io as _io
    from PIL import Image
    try:
        if not image_path and not image_url:
            return "Error: Provide either image_path (local file) or image_url (web link)."

        if image_path:
            if not os.path.exists(image_path):
                return "Error: File not found: {}".format(image_path)
            with open(image_path, "rb") as f:
                image_bytes = f.read()
            source = image_path
        else:
            resp = requests.get(image_url, timeout=30)
            resp.raise_for_status()
            image_bytes = resp.content
            source = image_url

        if len(image_bytes) > 10 * 1024 * 1024:
            return "Error: Image too large (max 10 MB)."

        img = Image.open(_io.BytesIO(image_bytes))
        fmt = (img.format or "PNG").upper()
        mime = {"JPEG": "image/jpeg", "JPG": "image/jpeg", "PNG": "image/png",
                "GIF": "image/gif", "WEBP": "image/webp", "BMP": "image/bmp"}.get(fmt, "image/png")

        if img.width > 1500 or img.height > 1500:
            img.thumbnail((1500, 1500))
            buf = _io.BytesIO()
            if fmt in ("JPEG", "JPG"):
                img.convert("RGB").save(buf, format="JPEG")
                mime = "image/jpeg"
            else:
                img.save(buf, format="PNG")
                mime = "image/png"
            image_bytes = buf.getvalue()

        b64_data = _b64.b64encode(image_bytes).decode()
        data_url = "data:{};base64,{}".format(mime, b64_data)

        api_resp = requests.post(
            Config.KIMI_BASE_URL + "/chat/completions",
            headers={"Authorization": "Bearer " + Config.KIMI_API_KEY, "Content-Type": "application/json"},
            json={
                "model": Config.VISION_MODEL,
                "max_tokens": 500,
                "messages": [{"role": "user", "content": [
                    {"type": "text", "text": prompt},
                    {"type": "image_url", "image_url": {"url": data_url}},
                ]}],
            },
            timeout=90,
        )

        if api_resp.status_code == 200:
            description = api_resp.json()["choices"][0]["message"]["content"]
            return "Image analysis ({}):\n\n{}".format(source, description)

        err_msg = api_resp.text[:200]
        fallback = _local_image_analysis(image_bytes, source)
        return "Vision API error ({}): {}\n\n{}".format(api_resp.status_code, err_msg, fallback)

    except Exception as e:
        return "Error analyzing image: {}".format(str(e))



# File Management Tools (direct Python I/O — bypasses Windows 8191-char cmd limit, safe for 10k+ lines)
@tool
def write_file(file_path: str, content: str, append: bool = False) -> str:
    """Write text content to a file (UTF-8). Safe for very large content (10,000+ lines)
    because it writes directly via Python I/O — no shell escaping or command-line length limits.
    Use this INSTEAD of file_system whenever you need to create or update file contents.
    - append=False (default): creates or OVERWRITES the file.
    - append=True: adds content to the end of the file. Use this to write huge files
      in multiple chunks when the content is too big for a single call.
    Parent folders are created automatically."""
    try:
        directory = os.path.dirname(file_path)
        if directory and not os.path.exists(directory):
            os.makedirs(directory, exist_ok=True)

        mode = "a" if append else "w"
        with open(file_path, mode, encoding="utf-8") as f:
            f.write(content)

        line_count = content.count("\n") + (1 if content and not content.endswith("\n") else 0)
        size = os.path.getsize(file_path)
        action = "Appended to" if append else "Wrote"
        return f"Success: {action} '{file_path}' ({line_count} lines this call, {size:,} bytes total on disk)."
    except Exception as e:
        return f"Error: {str(e)}"


@tool
def read_file(file_path: str, max_lines: int = 0) -> str:
    """Read and return the contents of a file (UTF-8).
    For very large files, set max_lines to limit how many lines are returned
    (e.g. max_lines=200). max_lines=0 (default) returns the whole file."""
    try:
        if not os.path.exists(file_path):
            return f"Error: File '{file_path}' does not exist."
        with open(file_path, "r", encoding="utf-8", errors="replace") as f:
            if max_lines and max_lines > 0:
                lines = []
                for i, line in enumerate(f):
                    if i >= max_lines:
                        break
                    lines.append(line)
                return "".join(lines) + f"\n... [truncated at {max_lines} lines]"
            return f.read()
    except Exception as e:
        return f"Error: {str(e)}"


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
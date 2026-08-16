# 🤖 AI Agent Bot

A powerful, tool-calling AI agent built with **LangGraph**, **LangChain**, and **Streamlit**. Powered by the **Kimi K3** model via TokenRouter's OpenAI-compatible API, this agent can search the web, control a browser, send emails, execute code, check weather, and more — all through a clean chat interface.

---

## ✨ Features

- 🧠 **Kimi K3 Brain** — LLM-powered reasoning with tool-calling ability
- 🌊 **Streaming Responses** — Tokens appear in real-time as they're generated
- 🔧 **Tool Call Transparency** — See exactly which tools the agent uses and their results
- 🔄 **Retry on Errors** — One-click retry button when requests fail
- 💾 **Persistent Memory** — Conversation history saved in SQLite via LangGraph checkpointing
- 🖥️ **Streamlit UI** — Clean, responsive chat interface with sidebar controls

---

## 🛠️ Tools Available

| # | Tool | Description |
|---|------|-------------|
| 1 | `web_search` | Quick web search via DuckDuckGo |
| 2 | `web_search_tavily` | Advanced web search with date filtering |
| 3 | `scrape_webpage` | Extract clean text content from any URL |
| 4 | `browser_agent` | Control a real browser — click, type, login, navigate |
| 5 | `file_system` | Execute shell/terminal commands on the local machine |
| 6 | `code_executor` | Run Python & Bash code safely |
| 7 | `calculator` | Safe arithmetic evaluation with math functions |
| 8 | `get_datetime` | Get the current date and time |
| 9 | `get_weather` | Live weather, humidity, wind & AQI for any city |
| 10 | `send_email` | Send polished HTML emails via Gmail |
| 11 | `gmail_search` | Search Gmail inbox with operators |
| 12 | `gmail_read` | Read full email content by message ID |

---

## 🚀 Getting Started

### Prerequisites

- **Python 3.11+** (required — `browser-use` needs ≥3.11)
- A [TokenRouter](https://tokenrouter.com) API key
- Gmail OAuth2 credentials (`credentials.json`)
- OpenWeatherMap API key
- Tavily API key

### Installation

#### ⚡ Quick Setup (Recommended)

A one-command setup script handles everything — virtual environment, pinned dependencies, **and Playwright browser binaries**:

```bash
# Clone the repository
git clone git@github.com:Rahulchunduruu/Agent.git
cd Agent

# Linux / Mac
bash setup.sh

# Windows
setup.bat
```

The setup script automatically:
1. ✅ Creates a virtual environment (`.venv`)
2. ✅ Installs all **pinned** dependencies from `requirements.txt`
3. ✅ Installs Playwright **Chromium browser binaries** (`playwright install chromium`)
4. ✅ Installs system dependencies (`playwright install-deps chromium` — Linux only)

#### 🔧 Manual Setup

```bash
# Create virtual environment
python -m venv .venv
.venv\Scripts\activate    # Windows
# source .venv/bin/activate  # Linux/Mac

# Install pinned dependencies
pip install -r requirements.txt

# ⚠️ IMPORTANT: pip does NOT install Playwright browser binaries.
# You MUST run these separately or scrape_webpage/browser tools will fail:
playwright install chromium
playwright install-deps chromium   # Linux only (system libraries)
```

> 📌 **Note:** All dependencies in `requirements.txt` are **pinned to exact versions** for reproducible deployments across machines and VMs.

### Environment Setup

Create a `.env` file in the project root:

```env
kimi-k3-free=your_tokenrouter_api_key
KIMI_BASE_URL=https://api.tokenrouter.com/v1
KIMI_MODEL=your_model_name
TAVILY_API_KEY=your_tavily_key
OPENWEATHER_API_KEY=your_openweathermap_key
BROWSER_USE_API_KEY=your_browser_use_key
Mem0=your_mem0_key
GROQ_API_KEY=your_groq_key
```

### Running the App

```bash
streamlit run app.py
```

Open [http://localhost:8501](http://localhost:8501) in your browser.

---

## 📁 Project Structure

```
Agent/
├── app.py              # Streamlit UI (streaming, transparency, retry)
├── main.py             # LangGraph agent graph + SQLite checkpointer
├── config.py           # Environment configuration
├── prompt.py           # System prompt for the agent
├── tools.py            # All 12 tool definitions
├── evals.py            # DeepEval evaluation script
├── requirements.txt    # Pinned Python dependencies
├── setup.sh            # One-command setup (Linux/Mac)
├── setup.bat           # One-command setup (Windows)
├── .gitignore          # Git ignore rules
└── .env                # API keys (NOT committed)
```

---

## 🔐 Security

- All API keys are stored in `.env` (never committed to git)
- Gmail OAuth tokens (`credentials.json`, `token.json`) are git-ignored
- Chat database (`chatbot.db`) is git-ignored
- GitHub Push Protection enabled for secret scanning

---

## 🧪 Evaluation

Run the DeepEval evaluation script to test answer relevancy:

```bash
python evals.py
```

---

## 📦 Tech Stack

| Component | Technology |
|-----------|-----------|
| LLM | Kimi K3 (via TokenRouter) |
| Agent Framework | LangGraph + LangChain |
| UI | Streamlit |
| Memory | SQLite (LangGraph SqliteSaver) |
| Browser Automation | browser-use |
| Web Scraping | Playwright + BeautifulSoup |
| Email | Gmail API (OAuth2) |
| Weather | OpenWeatherMap API |
| Search | DuckDuckGo (ddgs) + Tavily |

---

## 📝 License

This project is for personal/educational use.

---

## 👨‍💻 Author

**Rahul Chunduru**
- GitHub: [@Rahulchunduruu](https://github.com/Rahulchunduruu)

---

## 🙏 Acknowledgments

- [LangChain](https://www.langchain.com/) — LLM framework
- [LangGraph](https://github.com/langchain-ai/langgraph) — Agent orchestration
- [Streamlit](https://streamlit.io/) — UI framework
- [browser-use](https://github.com/browser-use/browser-use) — Browser automation
- [TokenRouter](https://tokenrouter.com) — Model API gateway

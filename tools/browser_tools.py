"""Browser automation tool: browser_agent."""

import asyncio

from langchain_core.tools import tool

from config import Config


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

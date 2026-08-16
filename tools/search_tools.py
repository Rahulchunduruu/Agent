"""Web search & scraping tools: web_search, web_search_tavily, scrape_webpage."""

from langchain_core.tools import tool
from langchain_community.tools import DuckDuckGoSearchRun
from langchain_community.document_loaders import AsyncChromiumLoader
from langchain_community.document_transformers import BeautifulSoupTransformer
from tavily import TavilyClient

from config import Config

search = DuckDuckGoSearchRun()


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

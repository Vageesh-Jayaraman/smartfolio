import os

from langsmith import traceable
from tavily import TavilyClient
from dotenv import load_dotenv

load_dotenv()

tavily = TavilyClient(
    api_key=os.getenv("TAVILY_API_KEY")
)

@traceable(name="Tavily Search")
def search_news(
        query: str,
        max_results: int = 5,
):
    response = tavily.search(
        query=query,
        search_depth="advanced",
        topic="news",
        max_results=max_results,
    )

    return response["results"]
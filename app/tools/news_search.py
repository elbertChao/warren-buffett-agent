from langchain.tools import Tool
from langchain_community.utilities import SerpAPIWrapper


def create_news_search_tool(api_key):
    """
    Checks if a SerpAPI key is provided and initializes a news search tool using SerpAPI.
    If the key is not provided or initialization fails, it returns a placeholder tool with an error message.
    """
    if api_key:
        try:
            params = {
                "engine": "google_news",
                "gl": "ca",
                "hl": "en",
                "num": 5
            }
            search_wrapper = SerpAPIWrapper(params=params, serpapi_api_key=api_key)

            def safe_news_run(query):
                try:
                    return search_wrapper.run(query)
                except Exception as e:
                    return f"News search failed: {str(e)}"

            return Tool(
                name="search_stock_news",
                func=safe_news_run,
                description="Useful for searching recent news articles about a specific company or stock symbol."
            )

        except Exception as e:
            return Tool(
                name="search_stock_news",
                func=lambda x: f"News search unavailable (initialization failed: {e})",
                description="News search tool (currently unavailable due to configuration error)."
            )

    else:
        return Tool(
            name="search_stock_news",
            func=lambda x: "News search unavailable (SerpAPI key not provided).",
            description="News search tool (unavailable - API key needed)."
        )

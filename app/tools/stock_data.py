import json
import yfinance as yf
from langchain.tools import Tool
import streamlit as st

@st.cache_data(show_spinner=False)
def get_stock_info(symbol: str) -> str:
    """
    Fetches key financial data for a given stock symbol using Yahoo Finance.
    """
    try:
        ticker = yf.Ticker(symbol)
        info = ticker.info

        if not info or all(info.get(k) is None for k in ['regularMarketPrice', 'currentPrice', 'previousClose']):
            hist = ticker.history(period="5d")
            if hist.empty:
                return f"Error: Could not retrieve any data for symbol {symbol}."
            last_close = hist['Close'].iloc[-1] if not hist.empty else 'N/A'
            current_price = info.get("currentPrice") or info.get("regularMarketPrice") or last_close
        else:
            current_price = info.get("currentPrice") or info.get("regularMarketPrice") or info.get("previousClose", "N/A")

        data = {
            "symbol": symbol,
            "companyName": info.get("longName", "N/A"),
            "currentPrice": current_price,
            "peRatio": info.get("trailingPE") or info.get("forwardPE", "N/A"),
            "earningsPerShare": info.get("trailingEps", "N/A"),
            "marketCap": info.get("marketCap", "N/A"),
            "dividendYield": info.get("dividendYield", "N/A"),
            "priceToBook": info.get("priceToBook", "N/A"),
            "sector": info.get("sector", "N/A"),
            "industry": info.get("industry", "N/A"),
            "summary": info.get("longBusinessSummary", "N/A")[:500] + ("..." if len(info.get("longBusinessSummary", "")) > 500 else "")
        }

        if data["currentPrice"] == "N/A":
            return f"Error: Could not retrieve current price for {symbol}."

        return json.dumps(data)

    except Exception as e:
        return f"Error fetching data for {symbol} using yfinance: {str(e)}"

stock_data_tool = Tool(
    name="get_stock_financial_data",
    func=get_stock_info,
    description="Useful for fetching fundamental financial data for a specific stock symbol (ticker)..."
)
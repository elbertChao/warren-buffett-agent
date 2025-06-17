import json
import os
import yfinance as yf
from datetime import datetime

PORTFOLIO_PATH = "../data/portfolio_db.json"

def load_portfolio():
    """
    Loads the portfolio from the JSON file saved in the database.
    """
    if not os.path.exists(PORTFOLIO_PATH):
        return {}
    with open(PORTFOLIO_PATH, "r") as f:
        return json.load(f)

def save_portfolio(portfolio):
    """
    Saves the portfolio to the JSON file in the database.
    """
    os.makedirs(os.path.dirname(PORTFOLIO_PATH), exist_ok=True)
    with open(PORTFOLIO_PATH, "w") as f:
        json.dump(portfolio, f, indent=4)

def add_stock_to_portfolio(user_id, symbol, quantity, purchase_date):
    """
    Adds a stock to the user's portfolio.
    : user_id: The ID of the user.
    : symbol: The stock symbol to add.
    : quantity: The number of shares purchased.
    : purchase_date: The date of purchase in 'YYYY-MM-DD' format.
    """
    portfolio = load_portfolio()
    if user_id not in portfolio:
        portfolio[user_id] = []

    portfolio[user_id].append({
        "symbol": symbol.upper(),
        "quantity": quantity,
        "purchase_date": purchase_date
    })
    save_portfolio(portfolio)

def get_portfolio_value(user_id):
    """
    Retrieves the current value of the user's portfolio.
    : user_id: The ID of the user.
    : returns: A list of dictionaries containing stock information and current values.
    """
    portfolio = load_portfolio()
    user_portfolio = portfolio.get(user_id, [])
    results = []

    for entry in user_portfolio:
        symbol = entry["symbol"]
        quantity = entry["quantity"]
        purchase_date = entry["purchase_date"]

        try:
            ticker = yf.Ticker(symbol)
            hist = ticker.history(start=purchase_date)
            if hist.empty:
                continue
            buy_price = hist["Close"].iloc[0]
            current_price = ticker.info.get("currentPrice") or ticker.info.get("regularMarketPrice")

            if not current_price:
                continue

            investment_value = quantity * current_price
            gain_loss = (current_price - buy_price) * quantity

            results.append({
                "symbol": symbol,
                "buy_price": round(buy_price, 2),
                "current_price": round(current_price, 2),
                "quantity": quantity,
                "gain_loss": round(gain_loss, 2),
                "total_value": round(investment_value, 2)
            })
        except Exception as e:
            print(f"Error retrieving data for {symbol}: {e}")
            continue

    return results

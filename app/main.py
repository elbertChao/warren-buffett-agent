import streamlit as st
from dotenv import load_dotenv
from agents.buffett_agent import create_buffett_agent_runnable
from utils.key_utils import setup_api_key_inputs, get_active_api_keys, show_api_status
import yfinance as yf
from datetime import datetime, timedelta

# Load environment variables from .env if user has a global one, override it
load_dotenv(override=True)

# Streamlit page config
st.set_page_config(page_title="Warren Buffett Investment Chatbot 🧠", layout="wide")

# Navigation control
if "page" not in st.session_state:
    st.session_state.page = "chat"

st.sidebar.title("🧭 Navigation")
if st.sidebar.button("🏠 Home/Chat"):
    st.session_state.page = "chat"
if st.sidebar.button("📈 Analyze Portfolio"):
    st.session_state.page = "analysis"

# Sidebar configuration and API key input
setup_api_key_inputs()
openai_key, serpapi_key = get_active_api_keys()
show_api_status(openai_key, serpapi_key)

# Sidebar portfolio tracker
st.sidebar.subheader("📁 My Portfolio")
if "portfolio" not in st.session_state:
    st.session_state.portfolio = []

with st.sidebar.form(key="portfolio_form"):
    ticker = st.text_input("Stock Symbol", value="", placeholder="e.g. AAPL, TSLA")
    shares = st.number_input("Number of Shares", min_value=0.0, step=1.0)
    add = st.form_submit_button("➕ Add to Portfolio")
    if add and ticker:
        st.session_state.portfolio.append({"ticker": ticker.upper(), "shares": shares})

if st.session_state.portfolio:
    st.sidebar.markdown("### 📊 Current Holdings")
    total_value = 0.0
    for stock in st.session_state.portfolio:
        try:
            ticker_data = yf.Ticker(stock["ticker"])
            price = ticker_data.info.get("regularMarketPrice") or ticker_data.info.get("previousClose")
            value = price * stock["shares"] if price else 0
            total_value += value
            st.sidebar.write(f"{stock['ticker']}: {stock['shares']} shares @ ${price:.2f} = ${value:,.2f}")
        except:
            st.sidebar.write(f"{stock['ticker']}: Price data not available")

    st.sidebar.markdown(f"**💰 Total Portfolio Value:** ${total_value:,.2f}")

    if st.sidebar.button("🗑️ Clear Portfolio"):
        st.session_state.portfolio = []

# ----------- Chat Page -----------
if st.session_state.page == "chat":
    st.title("Warren Buffett Investment Chatbot 🧠")
    st.caption("Ask me about investing, stocks, or market wisdom – in the style of Warren Buffett.")

    if "messages" not in st.session_state:
        st.session_state.messages = [
            {"role": "assistant", "content": "Hello! I'm your Warren Buffett-inspired investment assistant. Ask me anything!"}
        ]

    if openai_key and serpapi_key:
        agent_runnable, chat_history = create_buffett_agent_runnable(openai_key, serpapi_key)

        for msg in st.session_state.messages:
            st.chat_message(msg["role"]).write(msg["content"])

        if prompt := st.chat_input("Ask Buffett Bot..."):
            st.chat_message("user").write(prompt)
            st.session_state.messages.append({"role": "user", "content": prompt})

            with st.spinner("Buffett is thinking..."):
                try:
                    response = agent_runnable.invoke({"input": prompt}, config={"configurable": {"session_id": "default_user"}})

                    # Handle full response dict
                    if isinstance(response, dict) and "output" in response:
                        output = response["output"]
                    else:
                        output = str(response)

                    st.chat_message("assistant").write(output)
                    st.session_state.messages.append({"role": "assistant", "content": output})

                except Exception as e:
                    st.error(f"An error occurred: {str(e)}")

    if st.sidebar.button("🧹 Clear Chat History"):
        st.session_state.messages = []
        st.rerun()

# ----------- Analysis Page -----------
elif st.session_state.page == "analysis":
    st.title("📈 Portfolio Analysis")
    if not st.session_state.portfolio:
        st.warning("No portfolio data to analyze.")
    else:
        total_value = 0.0
        st.subheader("Historical Performance")

        timeframes = {"7d": "Last 7 Days", "1mo": "Last 1 Month", "1y": "Last 1 Year"}
        selected_period = st.selectbox("Select performance period", options=list(timeframes.keys()), format_func=lambda x: timeframes[x])

        for stock in st.session_state.portfolio:
            try:
                ticker_data = yf.Ticker(stock["ticker"])
                hist = ticker_data.history(period=selected_period)
                current_price = hist["Close"].iloc[-1]
                past_price = hist["Close"].iloc[0]
                shares = stock["shares"]
                value_now = current_price * shares
                value_then = past_price * shares
                gain = value_now - value_then
                percent = (gain / value_then) * 100 if value_then != 0 else 0
                total_value += value_now
                st.metric(label=f"{stock['ticker']} ({shares} shares)", value=f"${value_now:,.2f}", delta=f"{percent:.2f}%")
            except:
                st.write(f"{stock['ticker']}: Historical data not available.")

        st.subheader("🧠 Buffett-style Portfolio Commentary")
        diversified = len(st.session_state.portfolio) >= 5
        high_quality = all(yf.Ticker(stock["ticker"]).info.get("trailingPE", 0) > 10 for stock in st.session_state.portfolio)

        commentary = ""
        rating = 0

        if diversified and high_quality:
            commentary = "This portfolio demonstrates a sound degree of diversification and includes several companies with strong earnings. As Mr. Buffett might say, 'It’s far better to buy a wonderful company at a fair price than a fair company at a wonderful price.'"
            rating = 90
        elif diversified:
            commentary = "While this portfolio is well-diversified, some holdings might require deeper inspection of earnings quality. Buffett would remind us: 'Only when the tide goes out do you discover who's been swimming naked.'"
            rating = 70
        else:
            commentary = "This portfolio lacks diversification, which can be risky. Warren Buffett has always favored concentration when you know what you're doing – but for most, diversification is protection against ignorance."
            rating = 40

        st.info(commentary)
        st.success(f"🧮 Buffett Approval Rating: {rating}%")
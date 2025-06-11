import streamlit as st
import os
import json
import yfinance as yf
from dotenv import load_dotenv

# LangChain components
from langchain_openai import ChatOpenAI
from langchain.agents import AgentExecutor, create_openai_functions_agent
from langchain.memory import ConversationBufferMemory
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import SystemMessage  # No need for HumanMessage/AIMessage here anymore
from langchain.tools import Tool
from langchain_community.utilities import SerpAPIWrapper

# ************* Load .env file (as a fallback) *************
load_dotenv()

# ************* Set Page Config *************
st.set_page_config(page_title="Warren Buffett Bot", layout="wide")

st.title("Warren Buffett Investment Chatbot 🧠")
st.caption("Ask me about investing, stocks, or market wisdom – in the style of Warren Buffett.")

# ************* API Key Input in Sidebar *************
st.sidebar.header("API Configuration")

# Initialize session state for keys if they don't exist
if 'openai_api_key' not in st.session_state:
    st.session_state.openai_api_key = ""

if 'serpapi_api_key' not in st.session_state:
    st.session_state.serpapi_api_key = ""

# Create text input fields for keys, storing values in session state
input_openai_key = st.sidebar.text_input(
    "OpenAI API Key", type="password", value=st.session_state.openai_api_key, key="openai_input"
)

input_serpapi_key = st.sidebar.text_input(
    "SerpAPI API Key", type="password", value=st.session_state.serpapi_api_key, key="serpapi_input"
)

# Update session state with current input values
st.session_state.openai_api_key = input_openai_key
st.session_state.serpapi_api_key = input_serpapi_key

def is_valid_openai_key(key):
    return key and key.startswith("sk-") and len(key) > 40

def is_valid_serpapi_key(key):
    return bool(key)

# Determine which keys are active (user input takes priority)
active_openai_key = st.session_state.openai_api_key # or os.getenv("OPENAI_API_KEY")
active_serpapi_key = st.session_state.serpapi_api_key # or os.getenv("SERPAPI_API_KEY")

# ************* Display API Status *************
st.sidebar.header("API Status")

# (Add the if/else blocks using st.sidebar.success/error/warning as in the provided code)
if active_openai_key:
    st.sidebar.success("✅ OpenAI API Key loaded")
else:
    st.sidebar.error("❌ OpenAI API Key missing")

if active_serpapi_key:
    st.sidebar.success("✅ SerpAPI Key loaded")
else:
    st.sidebar.error("❌ SerpAPI Key missing")

# ************* Constants & Prompt Engineering *************

MODEL_NAME = "gpt-4o"  # Specify the OpenAI model
TEMPERATURE = 0.8       # Controls AI creativity (lower is more predictable)
MEMORY_KEY = "chat_history"  # Key for storing conversation history

# what OpenAI model will use to understand its role
BUFFETT_SYSTEM_PROMPT = """
You are a conversational AI assistant modeled after Warren Buffett, the legendary value investor. Embody his persona accurately.

**Your Core Principles:**

- **Value Investing:** Focus on finding undervalued companies with solid fundamentals (earnings, low debt, strong management). Judge businesses, not stock tickers.

- **Long-Term Horizon:** Think in terms of decades, not days or months. Discourage short-term speculation and market timing.

- **Margin of Safety:** Only invest when the market price is significantly below your estimate of intrinsic value. Be conservative.

- **Business Moats:** Favor companies with durable competitive advantages (strong brands, network effects, low-cost production, regulatory advantages).

- **Understand the Business:** Only invest in companies you understand. “Risk comes from not knowing what you're doing.”

- **Management Quality:** Assess the integrity and competence of the company’s leadership.

- **Patience and Discipline:** Wait for the right opportunities (“fat pitches”). Avoid unnecessary activity. Be rational and unemotional.

- **Circle of Competence:** Stick to industries and businesses you can reasonably understand. Acknowledge what you don’t know.

**Your Communication Style:**

- **Wise and Folksy:** Use simple language, analogies, and occasional humor, much like Buffett does in his letters and interviews.

- **Patient and Calm:** Respond thoughtfully, avoiding hype or panic.

- **Educational:** Explain your reasoning clearly, referencing your core principles.

- **Prudent:** Be cautious about making specific buy/sell recommendations without thorough analysis based on your principles. Often, you might explain *how* you would analyze it rather than giving a direct “yes” or “no.”

- **Quote Yourself:** Occasionally weave in famous Buffett quotes where appropriate (e.g., “Price is what you pay, value is what you get.” “Be fearful when others are greedy and greedy when others are fearful.”).

- **Acknowledge Limitations:** If asked about something outside your expertise (e.g., complex tech you wouldn't invest in, short-term trading), politely state it’s not your area.

**Interaction Guidelines:**

- When asked for stock recommendations, first use your tools to gather fundamental data (P/E, earnings, debt if possible) and recent news.

- Analyze the gathered information through the lens of your core principles (moat, management, valuation, long-term prospects).

- Explain your thought process clearly.

- If a company seems to fit your criteria, express cautious optimism, emphasizing the need for further diligence by the investor.

- If it doesn’t, say why (e.g., too speculative, high P/E without justification, outside circle of competence). Only explain why based on your principles.

- When in doubt, lean on timeless ideas, draw upon your well-known philosophies.

- Mistakes or recommendations must use the provided chat history. Refer back to previous points if needed.

Remember: You are simulating Warren Buffett. Your goal is to provide insights consistent with his philosophy and communication style, weighing the tools for data when needed. Do not give definitive financial advice, but rather educate and explain the “Buffett way” of thinking about investments.
"""

# ************* Tool Definitions *************
# 1. Stock Data Tool (Yahoo Finance) – Caching added
@st.cache_data(show_spinner=False)
def get_stock_info(symbol: str) -> str:
    """
    Fetches key financial data for a given stock symbol using Yahoo Finance...
    """
    try:
        ticker = yf.Ticker(symbol)
        info = ticker.info

        if not info or info.get('regularMarketPrice') is None and info.get('currentPrice') is None and info.get('previousClose') is None:
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

# Tool wrapper
stock_data_tool = Tool(
    name="get_stock_financial_data",
    func=get_stock_info,
    description="Useful for fetching fundamental financial data for a specific stock symbol (ticker)..."
)

# 2. News Search Tool (SerpAPI)
def create_news_search_tool(api_key):
    if api_key:
        try:
            params = {
                "engine": "google_news",
                "gl": "us",
                "hl": "en",
                "num": 5
            }
            search_wrapper = SerpAPIWrapper(params=params, serpapi_api_key=api_key)
            # Optional test:
            # search_wrapper.run("test query")

            return Tool(
                name="search_stock_news",
                func=search_wrapper.run,
                description="Useful for searching recent news articles about a specific company or stock symbol..."
            )

        except Exception as e:
            print(f"SerpAPI Tool Creation Warning: {e}")
            return Tool(
                name="search_stock_news",
                func=lambda x: f"News search unavailable (SerpAPI key configured, but error occurred: {e}).",
                description="News search tool (currently unavailable due to configuration error)."
            )

    else:
        # Dummy fallback if no key is provided
        return Tool(
            name="search_stock_news",
            func=lambda x: "News search unavailable (SerpAPI key not provided).",
            description="News search tool (unavailable - API key needed)."
        )

# Instantiate tool using available API key
news_search_tool = create_news_search_tool(active_serpapi_key)

# Combine tools for agent
tools = [stock_data_tool, news_search_tool]

# --- Initialize Agent ---
if active_openai_key and "agent_executor" not in st.session_state:
    llm = ChatOpenAI(model=MODEL_NAME, temperature=TEMPERATURE, openai_api_key=active_openai_key)
    prompt_template = ChatPromptTemplate.from_messages([
        SystemMessage(content=BUFFETT_SYSTEM_PROMPT),
        MessagesPlaceholder(variable_name=MEMORY_KEY),
        ("human", "{input}"),
        MessagesPlaceholder(variable_name="agent_scratchpad"),
    ])
    st.session_state["memory"] = ConversationBufferMemory(memory_key=MEMORY_KEY, return_messages=True)
    agent = create_openai_functions_agent(llm, tools, prompt_template)
    st.session_state["agent_executor"] = AgentExecutor(agent=agent, tools=tools, memory=st.session_state["memory"], verbose=True, handle_parsing_errors=True, max_iterations=5)

# --- Chat History and Interaction ---

# Initialize chat history if it doesn't exist
if "messages" not in st.session_state:
    st.session_state["messages"] = [
        {"role": "assistant", "content": "Greetings! I'm your Warren Buffett-inspired investment assistant. Ask me anything!"}
    ]

# Display existing chat messages
for msg in st.session_state.messages:
    st.chat_message(msg["role"]).write(msg["content"])

# Get new user input
if prompt := st.chat_input("Ask Buffett Bot..."):
    # Display user message
    st.session_state.messages.append({"role": "user", "content": prompt})
    st.chat_message("user").write(prompt)

    # Prepare input for the agent
    agent_input = {"input": prompt}

    # Invoke the agent executor
    try:
        with st.spinner("Buffett is pondering..."):
            # Get the executor instance from session state
            agent_executor_instance = st.session_state['agent_executor']
            response = agent_executor_instance.invoke(agent_input)

            # Display assistant response
            output = response.get("output", "Sorry, an error occurred.")
            st.session_state.messages.append({"role": "assistant", "content": output})
            st.chat_message("assistant").write(output)

    except Exception as e:
        # Handle errors during agent execution
        error_message = f"An error occurred: {str(e)}"
        st.error(error_message, icon="🔥")

        # Add error to chat display
        st.session_state.messages.append({"role": "assistant", "content": f"Sorry... {e}"})
        st.chat_message("assistant").write(f"Sorry... {e}")

if st.sidebar.button("Clear Chat History"):
    # Code to clear chat memory and messages
    st.session_state.messages = []
    st.session_state.memory = None
    st.rerun()

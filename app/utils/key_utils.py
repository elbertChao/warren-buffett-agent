import os
import streamlit as st
from dotenv import load_dotenv

load_dotenv(override=True)

def get_active_api_keys():
    """
    Returns the OpenAI and SerpAPI keys based on Streamlit session or .env
    """
    key_source = st.sidebar.radio("Use API key from:", ["Environment (.env)", "Manual Input"])

    if key_source == "Environment (.env)":
        openai_key = os.getenv("OPENAI_API_KEY")
        serpapi_key = os.getenv("SERPAPI_API_KEY")
    else:
        openai_key = st.session_state.get("openai_api_key", "")
        serpapi_key = st.session_state.get("serpapi_api_key", "")

    return openai_key, serpapi_key

def show_api_status(openai_key, serpapi_key):
    st.sidebar.header("API Status")

    if openai_key:
        st.sidebar.success("✅ OpenAI API Key loaded")
    else:
        st.sidebar.error("❌ OpenAI API Key missing")

    if serpapi_key:
        st.sidebar.success("✅ SerpAPI Key loaded")
    else:
        st.sidebar.error("❌ SerpAPI Key missing")


def setup_api_key_inputs():
    st.sidebar.header("API Configuration")

    if "openai_api_key" not in st.session_state:
        st.session_state.openai_api_key = ""

    if "serpapi_api_key" not in st.session_state:
        st.session_state.serpapi_api_key = ""

    st.sidebar.text_input(
        "OpenAI API Key", type="password",
        value=st.session_state.openai_api_key, key="openai_api_key"
    )

    st.sidebar.text_input(
        "SerpAPI API Key", type="password",
        value=st.session_state.serpapi_api_key, key="serpapi_api_key"
    )
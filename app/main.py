import streamlit as st
from utils.key_utils import setup_api_key_inputs, get_active_api_keys, show_api_status
from agents.buffett_agent import initialize_agent

st.set_page_config(page_title="Warren Buffett Bot", layout="wide")

st.title("Warren Buffett Investment Chatbot 🧠")
st.caption("Ask me about investing, stocks, or market wisdom - in the style of Warren Buffett.")

setup_api_key_inputs()
openai_key, serpapi_key = get_active_api_keys()
show_api_status(openai_key, serpapi_key)

if openai_key and "agent_executor" not in st.session_state:
    executor, memory = initialize_agent(openai_key, serpapi_key)
    st.session_state.agent_executor = executor
    st.session_state.memory = memory

if "messages" not in st.session_state:
    st.session_state["messages"] = [
        {"role": "assistant", "content": "Greetings! I'm your Warren Buffett-inspired investment assistant. Ask me anything!"}
    ]

for msg in st.session_state.messages:
    st.chat_message(msg["role"]).write(msg["content"])

if prompt := st.chat_input("Ask Buffett Bot..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    st.chat_message("user").write(prompt)

    try:
        with st.spinner("Buffett is pondering..."):
            agent_executor = st.session_state.agent_executor
            response = agent_executor.invoke({"input": prompt})
            output = response.get("output", "Sorry, an error occurred.")
            st.session_state.messages.append({"role": "assistant", "content": output})
            st.chat_message("assistant").write(output)
    except Exception as e:
        err_msg = f"An error occurred: {str(e)}"
        st.error(err_msg, icon="🔥")
        st.session_state.messages.append({"role": "assistant", "content": err_msg})
        st.chat_message("assistant").write(err_msg)

if st.sidebar.button("Clear Chat History"):
    st.session_state.messages = []
    st.session_state.memory = None
    st.rerun()

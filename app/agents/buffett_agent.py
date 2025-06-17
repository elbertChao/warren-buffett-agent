from langchain_openai import ChatOpenAI
from langchain.agents import AgentExecutor, create_openai_functions_agent
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_community.chat_message_histories import StreamlitChatMessageHistory
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder

from prompts.buffett_prompt import BUFFETT_SYSTEM_PROMPT
from tools.stock_data import stock_data_tool
from tools.news_search import create_news_search_tool

MODEL_NAME = "gpt-4o"
TEMPERATURE = 0.8
MEMORY_KEY = "chat_history"

chat_histories = {}

def create_buffett_agent_runnable(openai_api_key: str, serpapi_api_key: str, user_id: str = "default_user"):
    # LLM
    llm = ChatOpenAI(model=MODEL_NAME, temperature=TEMPERATURE, openai_api_key=openai_api_key)

    # Prompt
    prompt_template = ChatPromptTemplate.from_messages([
        ("system", BUFFETT_SYSTEM_PROMPT),
        MessagesPlaceholder(variable_name=MEMORY_KEY),
        ("human", "{input}"),
        MessagesPlaceholder(variable_name="agent_scratchpad"),
    ])

    # Tools
    news_search_tool = create_news_search_tool(serpapi_api_key)
    tools = [stock_data_tool, news_search_tool]

    # Agent + Executor
    agent = create_openai_functions_agent(llm, tools, prompt_template)
    executor = AgentExecutor(agent=agent, tools=tools, verbose=True, handle_parsing_errors=True)

    # History
    chat_histories[user_id] = StreamlitChatMessageHistory(key=user_id)

    # Wrap the executor as a RunnableWithMessageHistory
    runnable_agent = RunnableWithMessageHistory(
        executor,
        lambda session_id: chat_histories[session_id],
        input_messages_key="input",
        history_messages_key=MEMORY_KEY,
    )

    return runnable_agent, chat_histories[user_id]

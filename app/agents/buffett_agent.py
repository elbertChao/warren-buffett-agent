from langchain_openai import ChatOpenAI
from langchain.agents import AgentExecutor, create_openai_functions_agent
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain.memory import ConversationBufferWindowMemory
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from app.prompts.buffett_prompt import BUFFETT_SYSTEM_PROMPT
from app.tools.stock_data import stock_data_tool
from app.tools.news_search import create_news_search_tool

MODEL_NAME = "gpt-4o"
TEMPERATURE = 0.8
MEMORY_KEY = "chat_history"


def initialize_agent(openai_api_key: str, serpapi_api_key: str):
    llm = ChatOpenAI(
        model=MODEL_NAME,
        temperature=TEMPERATURE,
        openai_api_key=openai_api_key
    )

    prompt_template = ChatPromptTemplate.from_messages([
        ("system", BUFFETT_SYSTEM_PROMPT),
        MessagesPlaceholder(variable_name=MEMORY_KEY),
        ("human", "{input}"),
        MessagesPlaceholder(variable_name="agent_scratchpad"),
    ])

    memory = ConversationBufferWindowMemory(
        memory_key=MEMORY_KEY,
        return_messages=True,
        k=5
    )

    news_search_tool = create_news_search_tool(serpapi_api_key)
    tools = [stock_data_tool, news_search_tool]

    agent = create_openai_functions_agent(llm, tools, prompt_template)

    executor = AgentExecutor(
        agent=agent,
        tools=tools,
        memory=memory,
        verbose=True,
        handle_parsing_errors=True,
        max_iterations=5
    )

    return executor, memory
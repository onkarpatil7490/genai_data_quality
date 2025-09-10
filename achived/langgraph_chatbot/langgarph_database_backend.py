from langgraph.graph import StateGraph, START, END
from typing import TypedDict, Annotated
from langchain_core.messages import BaseMessage, HumanMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.graph.message import add_messages
from dotenv import load_dotenv
from langgraph.checkpoint.sqlite import SqliteSaver
import sqlite3

load_dotenv()

conn = sqlite3.connect(database='chatbot.db',check_same_thread=False)
checkpointer = SqliteSaver(conn = conn)

# Define State
class ChatState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]

# Define Graph
graph = StateGraph(ChatState)

# Nodes
def chat_node(state: ChatState):
    # taken user query from state
    messages = state["messages"]

    # send to llm
    response = model.invoke(messages)

    # response store state
    return {"messages":[response]}

# Add nodes
graph.add_node("chat_node", chat_node)

# Add edges
graph.add_edge(START, "chat_node")
graph.add_edge("chat_node",END)

# Compile
chatbot = graph.compile(checkpointer=checkpointer)

# LLM
model = ChatGoogleGenerativeAI(model="gemini-1.5-flash")

# test
# CONFIG = {"configurable":{"thread_id":"thread-2"}}
# response = chatbot.invoke({"messages":[HumanMessage(content="short receipie of pizza")]},config=CONFIG)
# print(response)

# get all unique threads
def retrieve_all_threads():
    all_threads = set()
    for checkpoint in (checkpointer.list(None)):
        all_threads.add(checkpoint.config["configurable"]["thread_id"])
    return (all_threads)
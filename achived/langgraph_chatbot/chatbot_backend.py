from langgraph.graph import StateGraph, START, END
from typing import TypedDict, Annotated
from langchain_core.messages import BaseMessage, HumanMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.graph.message import add_messages
from dotenv import load_dotenv
from langgraph.checkpoint.memory import MemorySaver

load_dotenv()

checkpointer = MemorySaver()

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


# # Call
# thread_id = "1"
# while True:
#     user_message = input("Type here: ")
#     # print("User:", user_message)
#     if user_message.strip().lower() in ["exit","quit","bye"]:
#         break
#     config = {"configurable":{"thread_id":thread_id}}
#     response = chatbot.invoke({"messages":[HumanMessage(content = user_message)]}, config=config)
#     print("AI:", response["messages"][-1].content)


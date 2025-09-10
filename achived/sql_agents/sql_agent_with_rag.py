from langchain_community.agent_toolkits.sql.toolkit import SQLDatabaseToolkit
from langchain_community.utilities.sql_database import SQLDatabase
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import ToolNode
from langchain_core.messages import BaseMessage, HumanMessage
from typing import TypedDict, Annotated
from project.dq_poc.utils import load_database, get_vector_database_and_retriever_tool, table_names
from langchain_core.prompts import PromptTemplate
from system_prompts import SQL_AGENT_PROMPT
from langgraph.graph.message import add_messages
from langgraph.checkpoint.memory import MemorySaver


from dotenv import load_dotenv

load_dotenv()
checkpointer = MemorySaver()

class ChatState(TypedDict):
    context: str
    messages: Annotated[list[BaseMessage], add_messages]

# Define Graph
workflow = StateGraph(ChatState)

def create_db_agent_graph(
    model,
    tools,
    retriever_tool,
    table_names):

    def retrieve(state: ChatState):
        user_input = state["messages"][-1].content
        retrieved_outputs = retriever_tool.invoke(user_input)
        return {"context": retrieved_outputs}

    def should_continue(state: ChatState):
        print("INSIDE SHOULD CONTINUE --------------------------------")
        breakpoint()
        messages = state["messages"]
        last_message = messages[-1]
        if last_message.tool_calls:
            return "tools"
        return END

    def sql_agent(state: ChatState): 
        print("INSIDE SQL AGENT --------------------------------")
        breakpoint()
        sql_agent_prompt_template = PromptTemplate(
            input_variables=[
                "user_input"
                "dialect",
                "top_k",
                "table_names",
                "context"
            ],
            template=SQL_AGENT_PROMPT,
        )
        user_input = state["messages"]
        prompt = sql_agent_prompt_template.invoke(
            {
                "user_input": user_input,
                "dialect": "sqlite",
                "top_k": 10,
                "table_names": table_names,
                "context": state["context"]
            }
        )
        response = model.invoke(prompt)
        return {"messages": [response]}

    tool_node = ToolNode(tools)
    workflow = StateGraph(ChatState)

    # Nodes
    workflow.add_node("retrieve", retrieve)
    workflow.add_node("sql_agent", sql_agent)
    workflow.add_node("tools", tool_node)

    # Edges
    workflow.add_edge(START, "retrieve")
    workflow.add_edge("retrieve", "sql_agent")
    workflow.add_conditional_edges("sql_agent", should_continue, ["tools", END])
    workflow.add_edge("tools", "sql_agent")
    workflow.add_edge("sql_agent", END)

    # Compile
    chatbot = workflow.compile(checkpointer=checkpointer)
    return chatbot


def create_db_agent():

    model = ChatGoogleGenerativeAI(model="gemini-2.5-flash")
    engine = load_database()
    db = SQLDatabase(engine)
    toolkit = SQLDatabaseToolkit(db=db, llm=model)
    tools = toolkit.get_tools()
    model = model.bind_tools(tools)
    retriever_tool = get_vector_database_and_retriever_tool()

    db_agent = create_db_agent_graph(
        model,
        tools,
        retriever_tool,
        table_names
    )

    return db_agent

db_agent = create_db_agent()

# Test input
while True:

    user_input = input("input here:")
    response = db_agent.invoke({"messages":[HumanMessage(content=user_input)]},
                    config={"configurable":{"thread_id":"thread_id-1"}})

    print(response["messages"][-1].content)
    breakpoint()
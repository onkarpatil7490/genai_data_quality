from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_community.utilities.sql_database import SQLDatabase
from dotenv import load_dotenv
from sqlalchemy import create_engine
import ast
from sqlalchemy.engine import Engine
from sqlalchemy.pool import StaticPool
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, MessagesState, StateGraph
from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode, tools_condition
from langchain_core.prompts import PromptTemplate
from langchain_community.agent_toolkits import SQLDatabaseToolkit
from typing import TypedDict, Annotated, Literal
from sqlalchemy import text
from sqlalchemy import text
from prompts import suggest_rule_prompt, generate_query_system_prompt, check_query_system_prompt

import os

# ------------------------------------------ setup ----------------------------------------------

checkpointer = MemorySaver()
load_dotenv()

# Paths
DATA_BASE_PATH_SOURCE = r"C:\Users\OnkarPatil\Desktop\genai_data_quality\project\data\source_data"
DB_PATH_SOURCE = os.path.join(DATA_BASE_PATH_SOURCE, "conventional_power_plants", "conventional_power_plants.sqlite")

DATA_BASE_PATH_RULES = r"C:\Users\OnkarPatil\Desktop\genai_data_quality\project\data\rules"
DB_PATH_RULES = os.path.join(DATA_BASE_PATH_RULES, "rule_management.sqlite")



# --------------------------------------- general utils ----------------------------------------------

def load_database(db_path=DATA_BASE_PATH_SOURCE) -> Engine:
    """Engine for opsd data."""
    return create_engine(f"sqlite:///{db_path}", poolclass=StaticPool)

def get_llm():
    llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash")
    return llm

def get_db(db_path):
    engine = create_engine(f"sqlite:///{db_path}", poolclass=StaticPool)
    db = SQLDatabase(engine)
    return db

llm = get_llm()
db_source = get_db(DB_PATH_SOURCE)
db_rules = get_db(DB_PATH_RULES)


# Get schema of a table
def get_schema_of_table(table, db, llm):

    toolkit = SQLDatabaseToolkit(db=db, llm=llm)
    tools = toolkit.get_tools()
    tools = tools
    
    get_schema_tool = next(tool for tool in tools if tool.name == "sql_db_schema")
    schema_call = {
    "name": "sql_db_schema",
    "args": {"table_names": table.strip()},
    "id": f"schema_{table.strip()}",
    "type": "tool_call",
    }
    schema_message = get_schema_tool.invoke(schema_call)
    schema = schema_message.content
    return schema

# Delete a table
def delete_table(table_name: str):
    """Delete (drop) a table from the database."""
    engine = load_database()
    with engine.connect() as conn:
        conn.execute(text(f"DROP TABLE IF EXISTS {table_name}"))
        conn.commit()
        print(f"Table '{table_name}' deleted successfully (if it existed).")

# Get sql tools
def get_sql_tools(db,llm):
    toolkit = SQLDatabaseToolkit(db=db, llm=llm)
    tools = toolkit.get_tools()
    tools = tools
    return tools

# Get tables from database
def list_tables(db,llm):
    tool_call = {
    "name": "sql_db_list_tables",
    "args": {},
    "id": "abc123",
    "type": "tool_call",
    }
    tools = get_sql_tools(db,llm)
    list_tables_tool = next(tool for tool in tools if tool.name == "sql_db_list_tables")
    tool_message = list_tables_tool.invoke(tool_call)
    return tool_message.content

# Get number of bad rows
def get_bad_rows_num(query: str):
    engine = load_database()
    with engine.connect() as conn:
        result = conn.execute(text(query))
        rows = result.fetchall()
        return [row[0] for row in rows]
    
# Run query
def run_query(query: str, db_path=DATA_BASE_PATH_SOURCE):
    engine = load_database(db_path)
    with engine.connect() as conn:
        result = conn.execute(text(query))
        return result.fetchall()

def insert_rule(rule_id, rule, table_name, column_name, rule_category, sql_query):
    query = f"""
        INSERT INTO rule_storage (rule_id, rule, table_name, column_name, rule_category, sql_query)
        VALUES ('{rule_id}', '{rule}', '{table_name}', '{column_name}', '{rule_category}', '{sql_query}')
    """
    db_rules.run(query)
    print(f"✅ Rule '{rule_id}' inserted successfully.")

def get_top_values(table_name: str, column_name: str, db_path=DATA_BASE_PATH_SOURCE, limit: int = 200):
    query = f"""
        SELECT {column_name}, COUNT(*) AS value_count
        FROM {table_name}
        GROUP BY {column_name}
        ORDER BY value_count DESC
        LIMIT {limit};
    """
    return run_query(query, db_path)

def delete_rule(rule_id):
    query = f"DELETE FROM rule_storage WHERE rule_id = '{rule_id}'"
    db_rules.run(query)
    print(f"✅ Rule '{rule_id}' deleted successfully (if it existed).")

def get_existing_rules_on_column(column_name, table_name):
    query = f"SELECT rule FROM rule_storage WHERE column_name = '{column_name}' AND table_name = '{table_name}'"
    results = db_rules.run(query)
    if not results:
        return []
    results = ast.literal_eval(results)
    flat_list = [r[0] for r in results]
    return flat_list

def get_all_rules_of_table(table_name):
    query = f"SELECT rule, table_name, column_name, rule_category, sql_query FROM rule_storage WHERE table_name = '{table_name}'"
    results = db_rules.run(query)
    # breakpoint()
    if not results:
        return []
    results = ast.literal_eval(results)
    keys = ["rule", "table_name", "column_name", "rule_category", "sql_query"]
    # convert each tuple into a dictionary
    dict_list = [dict(zip(keys, row)) for row in results]

    return dict_list
# ------------------------------------------ agents ---------------------------------------------------

# Agent - Tells stuff on the column and helps to create rules
def know_all_agent(prompt, db, llm, checkpointer):

    # llm bind with tools
    tools = get_sql_tools(db,llm)
    llm_with_tools = llm.bind_tools(tools)

    # Define class
    class ChatState(TypedDict):
        messages: Annotated[list[BaseMessage], add_messages]
        current_column: str

    # Nodes
    def chat_node(state: ChatState):
        
        prompt_template = PromptTemplate(input_variables=["current_column"], template=prompt)
        system_prompt = prompt_template.format(current_column=state["current_column"])
        system_message = SystemMessage(content=system_prompt)
        messages = [system_message] + state["messages"]

        response = llm_with_tools.invoke(messages)

        return {"messages": [response]}

    tool_node = ToolNode(tools)

    # Graph
    # - Nodes
    graph = StateGraph(ChatState)
    graph.add_node("chat_node", chat_node)
    graph.add_node("tools", tool_node)
    # - Edges
    graph.add_edge(START, "chat_node")
    graph.add_conditional_edges("chat_node",tools_condition)
    graph.add_edge('tools', 'chat_node')
    # - Compile
    chatbot = graph.compile(checkpointer=checkpointer)

    return chatbot

# Agent - Rule to SQL conversion agent
def rule_to_sql_agent(llm, db, checkpointer, table_name, schema, column_name, generate_query_system_prompt, check_query_system_prompt):

    # Tools
    toolkit = SQLDatabaseToolkit(db=db, llm=llm)
    tools = toolkit.get_tools()
    tools = tools

    run_query_tool = next(tool for tool in tools if tool.name == "sql_db_query")
    run_query_node = ToolNode([run_query_tool], name="run_query")

    def generate_query(state: MessagesState):
        prompt_template = PromptTemplate(input_variables=["dialect", "schema", "table_name", "column_name"], template=generate_query_system_prompt)
        system_prompt = prompt_template.format(dialect=db.dialect, schema=schema, table_name=table_name, column_name=column_name)
        system_message = SystemMessage(content=system_prompt)

        llm_with_tools = llm.bind_tools([run_query_tool])
        response = llm_with_tools.invoke([system_message] + state["messages"])
        return {"messages": [response]}

    def check_query(state: MessagesState):
        prompt_template = PromptTemplate(input_variables=["dialect"], template=check_query_system_prompt)
        system_prompt = prompt_template.format(dialect=db.dialect)
        system_message = SystemMessage(content=system_prompt)
        
        # Last message contains the generated query
        tool_call = state["messages"][-1].tool_calls[0]
        user_message = {"role": "user", "content": tool_call["args"]["query"]}
        
        llm_with_tools = llm.bind_tools([run_query_tool], tool_choice="any")
        response = llm_with_tools.invoke([system_message, user_message])
        response.id = state["messages"][-1].id
        return {"messages": [response]}

    def should_continue(state: MessagesState) -> Literal[END, "check_query"]:
        last_message = state["messages"][-1]
        return END if not last_message.tool_calls else "check_query"

    # --- 3. Build agent graph ---
    builder = StateGraph(MessagesState)
    builder.add_node(generate_query)
    builder.add_node(check_query)
    builder.add_node(run_query_node, "run_query")

    builder.add_edge(START, "generate_query")
    builder.add_conditional_edges("generate_query", should_continue)
    builder.add_edge("check_query", "run_query")
    builder.add_edge("run_query", "generate_query")

    agent = builder.compile(checkpointer=checkpointer)
    return agent

# llm call - Get data quality rule for a specific column
def get_rule_on_column_agent(column_name, table_name, existing_rules):

    llm = get_llm()
    db = get_db(DB_PATH_SOURCE)
    schema = get_schema_of_table(table_name, db, llm)
    values = get_top_values(table_name, column_name, db_path=DB_PATH_SOURCE, limit=200)
    existing_rules = get_existing_rules_on_column(column_name, table_name)
    prompt_template = PromptTemplate(input_variables=["existing_rules","column","table_name","schema","values"], template=suggest_rule_prompt)
    system_prompt = prompt_template.format(existing_rules=existing_rules, column=column_name, table_name=table_name, schema=schema, values=values)
    system_message = SystemMessage(content=system_prompt)
    user_message = HumanMessage(content=f"Please suggest a data quality rule for this column - {column_name}.")
    response = llm.invoke([system_message, user_message])
    response = response.content.strip()
    # Clean up and enforce the exact format
    if "rule:" in response.lower():
        rule_text = response
        return rule_text
    else:
        return None

def get_rule_from_response(llm, get_rule_out_prompt, response):
    system_message = SystemMessage(content=get_rule_out_prompt)
    rule = llm.invoke([system_message]+[response])
    return rule.content.strip()

# ---------------------------------------- process agent outputs ----------------------------------------------

def convert_rule_to_sql(rule, table_name, column_name):

    llm = get_llm()
    db = get_db(DATA_BASE_PATH_SOURCE)
    schema = get_schema_of_table(table_name, db, llm)
    agent = rule_to_sql_agent(llm, db, checkpointer, table_name, schema, column_name, generate_query_system_prompt, check_query_system_prompt)
    user_input = rule
    query_ready = True

    response = agent.invoke({
        "messages": [HumanMessage(content=user_input)],
    }, config={"configurable": {"thread_id": "thread_id-1"}})

    result = response["messages"][-1].content

    # Need something from user to break the loop, like an approval
    if "query:" in result.lower():
        query = result.split(":")[-1].strip()
        output = query
    elif "question" in result.lower():
        question = result.split(":")[-1].strip()
        output = question
        query_ready = False

    return query_ready, output

def call_know_all_agent(user_input, prompt):
    llm = get_llm()
    db = get_db(DATA_BASE_PATH_SOURCE)
    chatbot = know_all_agent(prompt, db, llm, checkpointer)
    response = chatbot.invoke({"messages":[HumanMessage(content=user_input)],"current_column":"postcode"},
                    config={"configurable":{"thread_id":"thread_id-1"}})
    return response["messages"][-1].content


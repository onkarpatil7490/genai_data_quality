import ast
import os
import re

from langgraph.graph import END, START, MessagesState, StateGraph
from langgraph.prebuilt import ToolNode
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_community.agent_toolkits import SQLDatabaseToolkit
from langchain_community.utilities.sql_database import SQLDatabase
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.messages import HumanMessage
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool
from typing import Literal
from project.dq_backend.utils import load_database
from dotenv import load_dotenv


#-----------------------------SETUP------------------------------
load_dotenv()
checkpointer = MemorySaver()
llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash")
DATA_BASE_PATH = r"C:\Users\OnkarPatil\Desktop\genai_data_quality\project\data"
DB_PATH = os.path.join(DATA_BASE_PATH, "conventional_power_plants", "conventional_power_plants.sqlite")
engine = load_database(DB_PATH)
db = SQLDatabase(engine)
toolkit = SQLDatabaseToolkit(db=db, llm=llm)
tools = toolkit.get_tools()

#------------------------------- UTILS ------------------------------
def load_database(db_path=DB_PATH):
    """Engine for opsd data."""
    return create_engine(f"sqlite:///{db_path}", poolclass=StaticPool)

def list_tables_in_database():
    tool_call = {
        "name": "sql_db_list_tables",
        "args": {},
        "id": "abc123",
        "type": "tool_call",
    }

    list_tables_tool = next(tool for tool in tools if tool.name == "sql_db_list_tables")
    tool_message = list_tables_tool.invoke(tool_call)

    table_names = tool_message.content.split(",")
    return table_names

def get_schema_of_table(table):
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

def get_columns_from_table(table):
    columns_info_str = db.run(f"PRAGMA table_info('{table}')")
    columns_info = ast.literal_eval(columns_info_str)
    columns = [col[1] for col in columns_info]
    return columns, columns_info

def get_first_k_values(table_name, column_name, k):
    query = f"SELECT {column_name} FROM {table_name} LIMIT {k}"
    result_str = db.run(query)
    result_values = ast.literal_eval(result_str)
    values = [value[0] for value in result_values]
    return values

def get_rule_on_column(values, column, table_name, schema, existing_rules):
    prompt = f"""
    You are a strict data quality expert. Based on the given column details, suggest ONE NEW data quality rule. 

    Rules must be clear, short, and in natural language.
    If all possible rules are already covered in this list: {existing_rules}, then return "None".

    Rules should always follow this format:
    RULE: (your rule here)

    Example: RULE: The values in the age column should not be more than 60

    Column: {column}
    Table: {table_name}
    Schema: {schema}
    Sample Data: {values}
    """

    response = llm.invoke(prompt).content.strip()

    # Clean up and enforce the exact format
    if response.startswith("RULE:"):
        rule_text = response
        # Avoid duplicates
        if rule_text in existing_rules:
            return None
        return rule_text
    else:
        return None

def dq_from_query(db, query, table_name):
    valid = ast.literal_eval(db.run(query))[0][0]
    total = int(ast.literal_eval(db.run(f"SELECT COUNT(*) FROM {table_name}"))[0][0])
    return {
        "valid_count": valid,
        "invalid_count": total - valid,
        "purity_percent": round(valid / total * 100, 2) if total > 0 else None
    }

def rule_creation_agent(table_name, schema, column_name):

    run_query_tool = next(tool for tool in tools if tool.name == "sql_db_query")
    run_query_node = ToolNode([run_query_tool], name="run_query")

    def generate_query(state: MessagesState):
        generate_query_system_prompt = f"""
        You are an expert in SQL and Data Quality rules.
        Given a natural language data quality rule, generate a syntactically correct {db.dialect} query
        that validates this rule. Use ONLY the following table, column, and schema:

        Schema: {schema}
        Table: {table_name}
        Column: {column_name}

        Rules for query generation:
        1. The query MUST NOT return actual column values.
        2. The query MUST return only the count of valid rows (good rows) that satisfy the rule.
        3. Use COUNT(*) or equivalent aggregation.
        4. Do NOT run the query; just generate it.

        If the requirement is unclear, ask a clarifying question to the user before generating the query.

        Output must be in exactly one of the following formats:
        QUERY: <query>
        OR
        QUESTION: <clarifying question to the user>
        """

        system_message = {"role": "system", "content": generate_query_system_prompt}
        llm_with_tools = llm.bind_tools([run_query_tool])
        response = llm_with_tools.invoke([system_message] + state["messages"])
        return {"messages": [response]}

    def check_query(state: MessagesState):
        check_query_system_prompt = f"""
        You are a SQL expert with strong attention to detail.
        Check the following {db.dialect} query for mistakes:
        - Using NOT IN with NULL values
        - Using UNION when UNION ALL should be used
        - BETWEEN exclusive vs inclusive
        - Data type mismatch
        - Correct quoting of identifiers
        - Correct number of arguments for functions
        - Proper columns for joins
        Rewrite the query if needed; otherwise, reproduce it.
        """
        system_message = {"role": "system", "content": check_query_system_prompt}
        
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

def extract_rules(llm_output):
    if "RULES:" not in llm_output:
        return []

    rules_section = llm_output.split("RULES:")[1].strip()

    # Split by rule numbers (1., 2., 3., etc.)
    rule_splits = re.split(r'\n\d+\.\s+', '\n' + rules_section)

    rules = []
    for rule_text in rule_splits:
        rule_text = rule_text.strip()
        if not rule_text:
            continue
        rules.append(rule_text)

    return rules

def create_sql_of_rule(rule, table_name, schema, column_name):
    agent = rule_creation_agent(table_name, schema, column_name)
    i = 0
    user_input = rule

    response = agent.invoke({
        "messages": [HumanMessage(content=user_input)],
    }, config={"configurable": {"thread_id": "thread_id-1"}})

    result = response["messages"][-1].content
    print(result)

    # Need something from user to break the loop, like an approval
    if "query:" in result.lower():
        query = result.split(":")[-1].strip()
        output = query
    elif "question" in result.lower():
        question = result.split(":")[-1].strip()
        output = question

    return query, output

def confirm_rule():
    pass
#---------------------------- WORKFLOW -----------------------------------------

# Get the table names from the db
tables = list_tables_in_database()
print("-"*50)
print("Tables in the database:")
for i, table in enumerate(tables, start=1):
    table = table.strip()
    print(f"{i}. {table}")
print("-"*50)

# Let user choose the table
table_num = 1 # take from the user
table_name = tables[table_num-1].strip()


# Get the names of the columns
print("-"*50)
columns_list, columns_info = get_columns_from_table(table_name)
print(f"Columns in the table - {table}:")
for i, column in enumerate(columns_info, start=1):
    column_name = column[1].strip()
    column_type = column[2]
    print(f"{i}. {column_name}:{column_type}")
print("-"*50)

# Let the user choose the column name
print("-"*50)
k = 100 # ---> instead of getting top k values, we can get random k values (E) # could take this from user
column_num = 7 # take from the user
column_name = columns_list[column_num-1]
print(f"Selected Column: {column_name}")
print("-"*50)

# Get first k values for the chose column
print("-"*50)
values = get_first_k_values(table_name, column_name, k)
print(f"Top {k} values for column - {column_name}: {values}")
print("-"*50)

# Get schema of the table
schema = get_schema_of_table(table_name)

# Get ai_suggested_rule on the column using the data
print("-"*50)

rule_query_dict = {}
while True:
    print("Return -")
    print("1. To get AI suggested Rule")
    print("2. To type your own rule")
    print("3. To exit")
    user_input = input("User Input:")

    ai_suggested_rule = get_rule_on_column(values,column_name, table_name, schema, rule_query_dict.keys())
    print("Rule Suggested by AI")
    print(ai_suggested_rule)
    print("")
    if ai_suggested_rule == None:
        print("No AI suggested rule found.")
        rule = input("Enter your data quality rule (natural language): ")
    else:
        print("Return:")
        print("1. To replace the AI suggested rule")
        print("2. To confirm the AI suggested rule")
        user_input = input("User Input:")
        if user_input == "1":
            rule = input("Enter your data quality rule (natural language): ")
        else:
            rule = ai_suggested_rule

    # generate sql query from the rule and check if its valid
    sql_query = create_sql_of_rule(rule, table_name, schema, column_name)
    print(sql_query)
    rule_query_dict[rule] = sql_query
    print(rule_query_dict)
    print(" ")


    
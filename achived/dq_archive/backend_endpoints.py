# THIS SCRIPT CONTAINS THE API ENDPOINTS
# RUN WITH "uvicorn main:app --reload"
# in the url, add '/docs/ and hit enter
# you will all the api, click on each and click try it out and enter inputs, and hit submit

from fastapi import FastAPI, Query
from fastapi.responses import JSONResponse
from utils import convert_rule_to_sql, insert_rule, delete_rule, get_rule_suggestion_on_column, \
    get_all_rules_of_table, get_query_test_results, load_table_values, load_col_values, chatbot
import uuid
from langchain_core.messages import HumanMessage

app = FastAPI()

# need apis for 
"""
1. load table data ------------
2. load col data -------------
3. get rule suggestion: input - column name, table name, existing rules (optional); output - suggested rule ---------
4. convert rule to sql: input - table name, column name, rule; output - sql query -----------
5. validate query: input - sql query, column name, table name; output - valid/invalid percentage, column data show --------------
6. add rule: input - table name, column name, rule text; output - success/failure -------------
7. delete rule: input - rule id; output - success/failure --------------
8. list rules: input - table name, column name (optional); output - list of rules -----------
9. chat with ai agent: input - user query, column name, table name; output - ai response -----------
10. rule exporting from chat: input - chat conversation; output - success/failure
"""

# convert rule to sql
@app.get("/convert_rule_to_sql/")
def convert_rule_to_sql_api(table_name: str, column_name: str, rule: str):
    output = convert_rule_to_sql(rule, table_name, column_name)
    return JSONResponse(content={"sql": output})

# add rule in the rules storage table
@app.put("/add_rule/")
def add_rule_api(rule: str, table_name: str, column_name: str, rule_category: str, sql_query: str):
    rule_id = str(uuid.uuid4())
    insert_rule(rule_id, rule, table_name, column_name, rule_category, sql_query)
    return JSONResponse(content={"message": f"Rule '{rule_id}' inserted successfully."})

# delete rule from the rules storage table
@app.delete("/delete_rule/")
def delete_rule_api(rule_id: str):  
    delete_rule(rule_id)
    return JSONResponse(content={"message": f"Rule '{rule_id}' deleted successfully (if it existed)."})

# get rule suggestion from AI
@app.get("/get_rule_suggestion/")
def get_rule_suggestion_api(table_name: str, column_name: str, existing_rules: list[str] = Query(default=[])):
    suggested_rule = get_rule_suggestion_on_column(column_name, table_name, existing_rules)
    return JSONResponse(content={"suggested_rule": suggested_rule})

# get rules of a table
@app.get("/get_all_rules_of_table/")
def get_all_rules_of_table_api(table_name: str):
    rules = get_all_rules_of_table(table_name)
    return JSONResponse(content={"rules": rules})

# test/validate the query
@app.get("/validate_query/")
def validate_query_api(sql_query: str, table_name: str, column_name: str):
    stats_dict = get_query_test_results(sql_query, column_name, table_name)
    return JSONResponse(content={"stats": stats_dict})

# load source data
@app.get("/get_table_data/")
def get_table_data_api(table_name: str, offset: int = 0, limit: int = 100):
    columns, data = load_table_values(table_name, offset, limit)
    return JSONResponse(content={"columns": columns, "rows": data})

# load column data
@app.get("/get_col_data/")
def get_table_data_api(table_name: str, column_name:str, offset: int = 0, limit: int = 100):
    data = load_col_values(table_name, column_name, offset, limit)
    return JSONResponse(content={"rows": data})

# chat with ai
@app.get("/chatbot/")
def chatbot_api(user_input, column_name, table_name):
    response = chatbot.invoke({"messages":[HumanMessage(content=user_input)],"current_column":column_name},
                    config={"configurable":{"thread_id":"thread_id-1"}})
    return JSONResponse(content={"AI Response": response["messages"][-1].content})

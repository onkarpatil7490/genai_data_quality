from fastapi import FastAPI, Query
from sqlalchemy import MetaData, Table, select
from fastapi.responses import JSONResponse
from utils import load_database, list_tables, get_stuff, get_rule_on_column_agent
from test2 import convert_rule_to_sql_api

app = FastAPI()
llm, db = get_stuff()
table_name = list_tables(db, llm)
engine = load_database()
metadata = MetaData()
metadata.reflect(bind=engine)

@app.get("/table/")
def get_table_rows(offset: int = Query(0), limit: int = Query(5)):
    table = Table(table_name, metadata, autoload_with=engine)
    with engine.connect() as conn:
        rows = conn.execute(select(table).offset(offset).limit(limit)).fetchall()
        results = [dict(row._mapping) for row in rows]
    return JSONResponse(content=results)


@app.get("/get_ai_suggestion/}")
def get_ai_suggestion(table_name: str, column_name: str):
    # here we will have a sqlite table to store rules per column
    # function to fetch rules
    existing_rules = []  # Fetch existing rules for the column
    rule_suggested_by_ai = get_rule_on_column_agent(column_name, table_name, existing_rules)
    return JSONResponse(content={"table": table_name, "column": column_name, "suggestion": rule_suggested_by_ai})

@app.post("/add_rule/")
def add_rule(table_name: str, column_name: str, rule: str):
    # Here you would implement the logic to add the rule to the database
    return JSONResponse(content={"message": "Rule added successfully"})

# table_name = "conventional_power_plants_DEe"
# column_name = "postcode"
# rule = "The 'postcode' column should always contain values that are exactly 5 characters long."
@app.get("/convert_rule_to_sql/")
def convert_rule_to_sql_api_okay(table_name: str, column_name: str, rule: str):
    output = convert_rule_to_sql_api(table_name, column_name, rule)
    return JSONResponse(content={"sql": output})

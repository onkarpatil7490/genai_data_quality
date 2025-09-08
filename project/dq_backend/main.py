from fastapi import FastAPI, Query
from sqlalchemy import MetaData, Table, select
from fastapi.responses import JSONResponse
from utils import load_database, list_tables, get_stuff, get_rule_on_column_agent
from project.dq_backend.api_functions import convert_rule_to_sql_api

app = FastAPI()
llm, db = get_stuff()
table_name = list_tables(db, llm)
engine = load_database()
metadata = MetaData()
metadata.reflect(bind=engine)


# table_name = "conventional_power_plants_DEe"
# column_name = "postcode"
# rule = "The 'postcode' column should always contain values that are exactly 5 characters long."
@app.get("/convert_rule_to_sql/")
def convert_rule_to_sql_api_okay(table_name: str, column_name: str, rule: str):
    output = convert_rule_to_sql_api(table_name, column_name, rule)
    return JSONResponse(content={"sql": output})

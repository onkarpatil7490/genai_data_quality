from langchain_community.agent_toolkits.sql.toolkit import SQLDatabaseToolkit
from langchain_community.utilities.sql_database import SQLDatabase
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_community.tools.sql_database.tool import (
    QuerySQLDatabaseTool,
    QuerySQLCheckerTool,
    InfoSQLDatabaseTool,
)
from dotenv import load_dotenv
from project.dq_poc.utils import load_database
import re

load_dotenv()
model = ChatGoogleGenerativeAI(model="gemini-2.5-flash")
engine = load_database()
db = SQLDatabase(engine)

query_sql_database_tool = QuerySQLDatabaseTool(db=db)
query_sql_checker_tool = QuerySQLCheckerTool(db=db, llm=model)
info_sql_database_tool = InfoSQLDatabaseTool(db=db)

def _clean_sql(q: str) -> str:
    if not isinstance(q, str):
        return q
    q = re.sub(r"^```(?:sql)?\s*", "", q.strip(), flags=re.IGNORECASE)
    q = re.sub(r"\s*```$", "", q)
    return q.strip()

bad_query = "SELECT nam_bnetza, companny FROM conventional_power_plants_DE LIMIT 5;"

schema = info_sql_database_tool.invoke("conventional_power_plants_DE")
checked_query = query_sql_checker_tool.invoke({
    "query": bad_query,
    "dialect": "sqlite",
    "table_info": schema
})
checked_query = _clean_sql(checked_query)
result = query_sql_database_tool.invoke(checked_query)

print("Input:", bad_query)
print("Fixed:", checked_query)
print("Output:", result)

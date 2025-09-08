from utils import (convert_rule_to_sql, get_stuff, list_tables, checkpointer)
from prompts import (generate_query_system_prompt, check_query_system_prompt)


rule = "The 'postcode' column should always contain values that are exactly 5 characters long."
column_name = "postcode"

llm, db = get_stuff()
table_name = list_tables(db, llm)
# output = convert_rule_to_sql(checkpointer, rule, table_name, column_name, generate_query_system_prompt, check_query_system_prompt)

def convert_rule_to_sql_api(table_name, column_name, rule):
    output = convert_rule_to_sql(checkpointer, rule, table_name, column_name, generate_query_system_prompt, check_query_system_prompt)
    return output


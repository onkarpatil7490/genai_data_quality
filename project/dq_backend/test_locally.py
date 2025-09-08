from utils import get_stuff, checkpointer, call_know_all_agent, \
get_schema_of_table, convert_rule_to_sql, get_rule_on_column_agent, \
      get_rule_from_response, list_tables, run_query, get_bad_rows_num
from prompts import col_know_all_prompt_with_rules, suggest_rule_prompt, get_rule_out_prompt, \
generate_query_system_prompt, check_query_system_prompt

# inputs
column_name = "postcode"
existing_rules = []
llm, db = get_stuff()
table_name = list_tables(db,llm)
schema = get_schema_of_table(table_name, db, llm)
# breakpoint()
# test know_all_agent
user_input = input("Want to chat with AI agent?? yes/no:")
# user_input = "no"
start_chat = False
if user_input.lower() == "yes":
    start_chat = True

while start_chat:
    print("")
    user_input = input("User:")
    if user_input.lower() == "exit":
        break
    response = call_know_all_agent(user_input, col_know_all_prompt_with_rules)
    print("")
    print("AI: ",response)

    if "rule:" in response.lower():
        print("")
        print("Rule Suggested, want to add the suggested rule?")
        user_input = input("yes/no:")
        print("")
        if user_input.lower() == "yes":
            breakpoint()
            rule = get_rule_from_response(llm, get_rule_out_prompt, response)
            existing_rules.append(rule)

    

# existing_rules = ["The 'postcode' column should always contain values that are exactly 5 characters long."]
# test get_rule_on_column_agent
values = []
ai_suggestions = True
# ai_suggestions = False
while ai_suggestions:
    print("")
    user_input = input(f"Get rule from AI on {column_name}? yes/no:")
    if user_input.lower() == "no":
        break
    suggested_rule = get_rule_on_column_agent(llm, values, column_name, table_name, schema, existing_rules, suggest_rule_prompt)
    if suggest_rule_prompt.lower() == "none":
        print("No Rule suggested by AI")
    else:
        rule = get_rule_from_response(llm, get_rule_out_prompt, suggested_rule)
        existing_rules.append(rule)
        print("Rule suggested by AI: ", rule)
        print(" ")


# test rule_to_sql_agent
for rule in existing_rules:
    while True:
        print("")
        query_ready, output = convert_rule_to_sql(llm, db, checkpointer, rule, table_name, schema, column_name, generate_query_system_prompt, check_query_system_prompt)
        print("Rule Submitted: ", rule)
        if query_ready:
            print("Generated Query: ", output)
            query = output
            result = get_bad_rows_num(query)
            total_number_rows = run_query(f"SELECT COUNT(*) FROM {table_name}")[0][0]
            print(f"Number of bad rows: {total_number_rows - len(result)} out of {total_number_rows}")
            break
        else:
            question = output
            print("Clarifying Question: ", output)
            print("")
            rule = input("User:")
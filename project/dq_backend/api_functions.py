from utils import get_rule_on_column_agent

column_name = "postcode"
table_name = "conventional_power_plants_DE"
existing_rules = []
suggested_rule = get_rule_on_column_agent(column_name, table_name, existing_rules)

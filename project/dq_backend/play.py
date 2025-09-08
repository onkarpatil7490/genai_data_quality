# THIS SCRIPT IS FOR TESTING PURPOSES ONLY
# PLEASE IGNORE

from utils import load_col_values


column_name = "postcode"
table_name = "conventional_power_plants_DE"
existing_rules = []

values = load_col_values(table_name, column_name, 0, 10)

breakpoint()
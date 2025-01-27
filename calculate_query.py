#Calculating max input for clipboard per query

attribute = 'DBKEY'

log = """
12342\n
3222\n
982\n
12\n
"""

records = """
12342\n
3221\n
982\n
4621\n
"""

def calculate_input(attribute, new_data, old_data):
    character_limit = 100
    extra_characters = int(len(attribute) + 4)
    print(f'Attributes: {attribute}')
    record_line = set(new_data.strip().splitlines())
    cleared_lines = set(old_data.strip().splitlines())
    new_lines = record_line - cleared_lines
    print(new_lines)
    return new_lines





def register_executed_records(user_input, executed_records):
    executed_data = executed_records.strip().splitlines()
    for executed_line in executed_data:
        print(f'Record: {executed_line}')
        executing_data = user_input.strip().splitlines()
        for executing_line in executing_data:
            print(executing_line)

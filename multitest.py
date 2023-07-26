import os
import re
import subprocess
import pandas as pd
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime


def update_script(file_name, new_values, new_instance_type, new_start_instance_index):
    with open(file_name, 'r') as file:
        data = file.read()

    new_values_str = str(new_values).replace("\n", "")

    data = re.sub(r"(node_type_selection_probability = ).*?(\n)",
                  r"\g<1>" + new_values_str + r"\g<2>", data, flags=re.DOTALL)

    data = re.sub(r"(instance_type = ').*?(')",
                  r"\g<1>" + new_instance_type + r"\g<2>", data)
    data = re.sub(r"(start_instance_index = ).*?((?![\d])|\Z)",
                  r"\g<1>" + str(new_start_instance_index) + r"\2", data)

    data = re.sub(r"(instance_file = 'heur__).*?(\.gr')",
                  r"\g<1>" + str(new_start_instance_index).zfill(3) + r"\g<2>", data)

    new_file_name = f"new_{file_name}_{new_start_instance_index}"
    with open(new_file_name, 'w') as file:
        file.write(data)

    return new_file_name


def process_instance(new_start_instance_index):
    print(f"\nStart processing instance number {new_start_instance_index}")
    results = []
    for i in range(10):
        new_script = update_script(
            'ils_solver.py', node_type_selection_probability, new_instance_type, new_start_instance_index)

        instance_name = f"--heur__{new_start_instance_index:03d}.gr"
        print(f"Executing command: python3 {new_script} {instance_name}")
        process = subprocess.run(
            ["python3", new_script, instance_name], capture_output=True, text=True)

        print(f"Output for instance number {new_start_instance_index}:")
        print(process.stdout)

        output = process.stdout
        match = re.search(
            r"The tree depth for instance '(.*?)' is '(.*?)'", output)
        if match is None:
            print(
                f"No match found in the output for instance number {new_start_instance_index}")
            continue
        instance = match.group(1)
        tree_depth = int(match.group(2))
        results.append(tree_depth)

        print(
            f"Completed execution number {i+1} for instance number {new_start_instance_index}")

        # remove the script file after use
        os.remove(new_script)

    return [instance] + results


node_type_selection_probability = {'subtree': 0, 'internal': 10, 'leaf': 10, 'leafs': 10, 'root': 10,
                                   'top': 10, 'bottom': 10, 'level': 10, 'path': 10, 'partial_path': 10, 'partial_path_bottom': 10}

new_instance_type = 'heur'

with ThreadPoolExecutor() as executor:
    data = list(executor.map(process_instance, range(1, 11)))

print("Finished all instances.")

df = pd.DataFrame(data, columns=["Instance"] +
                  [f"Execution {i+1}" for i in range(10)])

# Add node_type_selection_probability to the end of DataFrame
df_probabilities = pd.DataFrame(
    [node_type_selection_probability], index=['Node Probabilities'])
df = pd.concat([df, df_probabilities])

# current date and time as a string
timestamp = datetime.now().strftime('%Y%m%d%H%M')
excel_file = f"exectest_{timestamp}.xlsx"  # dynamic Excel file name
df.to_excel(excel_file, index=False)
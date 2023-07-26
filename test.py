import re
import subprocess
import pandas as pd



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

    new_file_name = f"new_{file_name}"
    with open(new_file_name, 'w') as file:
        file.write(data)

    return new_file_name


node_type_selection_probability = {'subtree': 0, 'internal': 10, 'leaf': 10, 'leafs': 10, 'root': 10,
                                   'top': 10, 'bottom': 10, 'level': 10, 'path': 10, 'partial_path': 10, 'partial_path_bottom': 10}

new_instance_type = 'heur'

data = []

for new_start_instance_index in range(1, 3):
    print(f"Processing instance number {new_start_instance_index}")
    results = []
    for i in range(10):
        new_script = update_script(
            'ils_solver.py', node_type_selection_probability, new_instance_type, new_start_instance_index)

        instance_name = f"--heur__{new_start_instance_index:03d}.gr"
        process = subprocess.run(
            ["python3", new_script, instance_name], capture_output=True, text=True)

        print(f"Command executed: {process.args}")
        print(f"Command stdout: {process.stdout}")

        output = process.stdout
        match = re.search(
            r"The tree depth for instance '(.*?)' is '(.*?)'", output)
        instance = match.group(1)
        tree_depth = int(match.group(2))
        results.append(tree_depth)

        print(
            f"Completed execution number {i+1} for instance number {new_start_instance_index}")

    data.append([instance] + results)

print("Finished all instances.")

df = pd.DataFrame(data, columns=["Instance"] + [f"Execution {i+1}" for i in range(10)])
df.to_excel("exectest.xlsx", index=False)

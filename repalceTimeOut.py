import pandas as pd

# List of Excel files that need to be replaced
files_to_process = [
    "bottom_0.xlsx", "level_0.xlsx", "internal_0.xlsx", "partial_path_0.xlsx", 
    "root_0.xlsx", "leaf_0.xlsx", "partial_path_bottom_0.xlsx", "subtree_0.xlsx", 
    "leafs_0.xlsx", "path_0.xlsx", "top_0.xlsx"
]

# List of instance names to be deleted
instances_to_delete = [f"heur__{i}.gr" for i in range(101, 201)]

for file_path in files_to_process:
    # Load the Excel sheet into a DataFrame
    df = pd.read_excel(file_path, engine='openpyxl')

    # Drop the rows that contain instance names in the 'instances_to_delete' list
    df = df[~df["Instance"].isin(instances_to_delete)].reset_index(drop=True)

    # Loop through each row of the dataframe
    for index, row in df.iterrows():
        # Filter out non-numeric values, get the max, and replace "timeout" with the max value for that row
        max_value = row[row.apply(lambda x: isinstance(x, (int, float)))].max()
        df.loc[index] = row.replace('timeout', max_value)

    # Save the modified DataFrame back to the Excel file
    df.to_excel(file_path, index=False, engine='openpyxl')

    print(f"Processed {file_path}. Deleted rows with instance names from 'heur__101.gr' to 'heur__200.gr' and replaced 'timeout' values with max value for each row.")

print("All files processed successfully!")

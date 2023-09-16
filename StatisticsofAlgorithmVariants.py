import pandas as pd
import numpy as np

file_names = [
    "bottom_0.xlsx", "leaf_0.xlsx", "leafs_0.xlsx", "internal_0.xlsx",
    "level_0.xlsx", "partial_path_0.xlsx", "path_0.xlsx", "root_0.xlsx",
    "subtree_0.xlsx", "top_0.xlsx", "partial_path_bottom_0.xlsx"
]

summary_statistics = []

for file_name in file_names:
    # Read the excel file
    df = pd.read_excel(f"analizat/{file_name}")

    # Get all numerical data
    numerical_data = df.select_dtypes(include=[np.number]).values.flatten()

    # Calculate statistics
    sample_size = len(numerical_data)
    mean = np.mean(numerical_data)
    variance = np.var(numerical_data)
    std_dev = np.std(numerical_data)
    
    # Get the algorithm variant from the file name (adding '_zero' to the name)
    algorithm_variant = file_name.replace(".xlsx", "_zero")
    
    # Append statistics to the summary list
    summary_statistics.append([algorithm_variant, sample_size, mean, variance, std_dev])

# Create a new DataFrame with the summary statistics
summary_df = pd.DataFrame(summary_statistics, columns=["Algorithm Variant", "Sample Size", "Mean", "Variance", "Standard Deviation"])

# Write the summary statistics to a new excel file
summary_df.to_excel("summary_statistics.xlsx", index=False)

print("Summary statistics have been written to 'summary_statistics.xlsx'")

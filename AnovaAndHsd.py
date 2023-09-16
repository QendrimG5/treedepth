import pandas as pd
import numpy as np
from scipy.stats import f, f_oneway
from statsmodels.stats.multicomp import MultiComparison


def load_data(file_names):
    """Load data from Excel files into a dictionary of dataframes."""
    data_dict = {}
    for file_name in file_names:
        label = file_name.rsplit('_', 1)[0]
        try:
            data_dict[label] = pd.read_excel(f"analizat/{file_name}")
        except FileNotFoundError as e:
            print(f"File not found: {e.filename}")
            continue
    return data_dict


def calculate_sum_and_count(data_dict):
    """Calculate the sum and the count of all numerical values in the data dictionary."""
    total_sum = 0
    total_count = 0
    for df in data_dict.values():
        numeric_df = df.select_dtypes(include=[np.number])
        total_sum += numeric_df.sum().sum()
        total_count += numeric_df.size
    print(f"Total sum of all numerical values: {total_sum}")
    print(f"Total number of numerical data points: {total_count}")


def calculate_anova(data_dict):
    """Perform ANOVA analysis on the loaded data."""
    anova_list = [df.select_dtypes(
        include=[np.number]).to_numpy().ravel() for df in data_dict.values()]

    # Perform ANOVA using scipy's f_oneway function
    anova_result = f_oneway(*anova_list)

    # Correcting Degrees of Freedom Calculation
    n_groups = len(data_dict)
    n_total_data_points = sum([group.size for group in anova_list])

    dof_between = n_groups - 1
    dof_within = n_total_data_points - n_groups
    dof_total = n_total_data_points - 1

    grand_mean = np.mean([np.mean(group) for group in anova_list])
    SS_between = sum(
        [len(group) * (np.mean(group) - grand_mean)**2 for group in anova_list])
    SS_within = sum([((group - np.mean(group))**2).sum()
                    for group in anova_list])
    SS_total = SS_between + SS_within

    MS_between = SS_between / dof_between if dof_between else 0
    MS_within = SS_within / dof_within if dof_within else 0

    # Calculating critical value for F statistic
    alpha = 0.05
    f_critical = f.ppf(1 - alpha, dof_between, dof_within)

    anova_table = pd.DataFrame({
        'Source of Variation': ['Between Groups', 'Within Groups', 'Total'],
        'Sum of Squares (SS)': [SS_between, SS_within, SS_total],
        'Degrees of Freedom (df)': [dof_between, dof_within, dof_total],
        'Mean Square (MS)': [MS_between, MS_within, ''],
        'F Statistic (F)': [anova_result.statistic, '', ''],
        'P-value': [anova_result.pvalue, '', ''],
        'Critical Value of F (F Critical)': [f_critical, '', '']
    })

    # Print the number of data points being calculated for each variant
    for label, df in data_dict.items():
        print(
            f"Number of data points for variant '{label}': {len(df.select_dtypes([np.number]).to_numpy().ravel())}")

    # Return the ANOVA table and the list of data for each group
    return anova_table, anova_list


def perform_tukey_hsd(data_dict):
    """Perform Tukey's HSD test on the loaded data."""
    combined_data = []
    for label, df in data_dict.items():
        flattened_data = df.select_dtypes(
            include=[np.number]).to_numpy().ravel()
        combined_data.append(pd.DataFrame(
            {'variant': label, 'value': flattened_data}))

    combined_df = pd.concat(combined_data)

    mc = MultiComparison(combined_df['value'], combined_df['variant'])
    tukey_result = mc.tukeyhsd()

    res_data = tukey_result._results_table.data[1:]
    headers = ['X1', 'X2', 'meandiff',
               'Adjusted p-value', 'lower', 'upper', 'reject']

    tukey_table = pd.DataFrame(data=res_data, columns=headers)

    tukey_table['Critical Mean'] = tukey_table['upper'] - \
        tukey_table['meandiff']  # Updated critical mean calculation
    tukey_table['Difference'] = abs(tukey_table['meandiff'])
    tukey_table['Pair'] = tukey_table['X1'] + ' - ' + tukey_table['X2']

    return tukey_table


def save_results(anova_table, tukey_table):
    """Save ANOVA and Tukey's HSD results to an Excel file."""
    with pd.ExcelWriter('analizat/analysis_results1.xlsx') as writer:
        anova_table.to_excel(writer, sheet_name='ANOVA', index=False)
        tukey_table.to_excel(writer, sheet_name='HSD', index=False)


def print_sum_of_variants(data_dict, anova_list):
    """Print the sum of all variants data for each group."""
    for label, _ in data_dict.items():
        total_sum = np.sum(anova_list[list(data_dict.keys()).index(label)])
        print(f"Total sum of data for variant '{label}': {total_sum:.4f}")


def main():
    file_names = [
        "bottom_0.xlsx", "leaf_0.xlsx", "leafs_0.xlsx", "internal_0.xlsx",
        "level_0.xlsx", "partial_path_0.xlsx", "path_0.xlsx", "root_0.xlsx",
        "subtree_0.xlsx", "top_0.xlsx", "partial_path_bottom_0.xlsx"
    ]

    data_dict = load_data(file_names)

    if not data_dict:
        print("No data was loaded. Exiting.")
        return

    # New function call to calculate and print sum and count of numerical values
    calculate_sum_and_count(data_dict)

    anova_table, anova_list = calculate_anova(data_dict)
    tukey_table = perform_tukey_hsd(data_dict)

    # Print the sum of all variants data for each group
    print_sum_of_variants(data_dict, anova_list)

    save_results(anova_table, tukey_table)

    # Find the best variant based on the lowest adjusted p-value
    min_p_value = tukey_table['Adjusted p-value'].min()
    best_variant = tukey_table[tukey_table['Adjusted p-value']
                               == min_p_value]['X1'].values[0]

    print("Analysis results have been saved to 'analizat/analysis_results1.xlsx'.")
    print(f"The best variant is: {best_variant}")


if __name__ == '__main__':
    main()

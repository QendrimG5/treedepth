import openpyxl
import os

# Create a new Excel workbook and select the active sheet
wb = openpyxl.Workbook()
sheet = wb.active
sheet.title = "Graph Data"

# Set the headers for the Excel columns
sheet['A1'] = 'Grafi'
sheet['B1'] = 'Numri i Nyjeve'
sheet['C1'] = 'Numri i Degeve'

# Directory containing the .gr files
directory_path = "instances/"

# Loop through the files from heur__001.gr to heur__100.gr
for i in range(1, 101):
    filename = os.path.join(directory_path, f'heur_{i:03}.gr')

    if os.path.exists(filename):
        with open(filename, 'r') as file:
            first_line = file.readline().strip()
            _, _, nodes, edges = first_line.split()

            # Write data to the Excel sheet
            sheet.append([f'heur__{i:03}', nodes, edges])
    else:
        print(f"File {filename} not found.")

# Save the workbook
wb.save("GraphData.xlsx")

print("Excel file 'GraphData.xlsx' has been created.")

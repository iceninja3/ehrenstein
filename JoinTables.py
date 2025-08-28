import pandas as pd
import glob
import os

# Path where your 87 CSVs are stored
path = "/Users/vishal/Library/CloudStorage/Box-Box/Bangladesh Nutrition Data Cleaning 2025/AllTables"   # <-- change this to your folder path

# Get all CSV files in the folder
csv_files = glob.glob(os.path.join(path, "*.csv"))

# Read and combine them
df_list = []
for file in csv_files:
    try:
        df = pd.read_csv(file)
        df["source_file"] = os.path.basename(file)  # optional: track source
        df_list.append(df)
    except Exception as e:
        print(f"Error reading {file}: {e}")

# Concatenate into one master table
master_df = pd.concat(df_list, ignore_index=True)

# Save as one CSV
master_df.to_csv("master_table.csv", index=False)

print("✅ All CSVs combined into master_table.csv")
import pandas as pd
import glob
import re

# Get a sorted list of all table*.csv files.
files = sorted(glob.glob('table*.csv'), key=lambda x: int(x.replace('table', '').replace('.csv', '')))

# Group files into sets of three
sets_of_files = [files[i:i+3] for i in range(0, len(files), 3)]

all_merged_data = []

for file_set in sets_of_files:
    if len(file_set) == 3:
        content_file, elements_file, vitamins_file = file_set

        # Read the files into dataframes
        df_content = pd.read_csv(content_file)
        df_elements = pd.read_csv(elements_file)
        df_vitamins = pd.read_csv(vitamins_file)

        # A function to clean and prepare each dataframe
        def clean_and_prepare(df):
            # Drop rows where the food name is missing
            df = df.dropna(subset=['Food name in English'])
            
            # --- NEW: Normalize the food names to fix matching errors ---
            def normalize_food_name(name):
                if isinstance(name, str):
                    name = re.sub(r'[\\r\\n]+', ' ', name) # Replace newlines with a space
                    name = re.sub(r'\\s+', ' ', name)      # Replace multiple spaces with one
                    name = name.strip()                  # Remove leading/trailing whitespace
                return name
            
            df['Food name in English'] = df['Food name in English'].apply(normalize_food_name)
            # -----------------------------------------------------------

            # Remove metadata rows
            df = df[~df['Code'].isin(['SD or min- max', 'n'])]
            
            # Set the clean food name as the index for merging
            df = df.set_index('Food name in English')
            
            # Drop columns that are not needed or would be redundant
            df = df.drop(columns=['Code', 'Food name in Bengali'], errors='ignore')
            return df

        df_content = clean_and_prepare(df_content)
        df_elements = clean_and_prepare(df_elements)
        df_vitamins = clean_and_prepare(df_vitamins)
        
        # Store the original column names before joining
        content_cols = df_content.columns
        elements_cols = df_elements.columns
        vitamins_cols = df_vitamins.columns

        # Join the three dataframes
        merged_set = df_content.join([df_elements, df_vitamins], how='outer')

        # Fill NaN values with the source file information
        merged_set[content_cols] = merged_set[content_cols].fillna(f"information not found in {content_file}")
        merged_set[elements_cols] = merged_set[elements_cols].fillna(f"information not found in {elements_file}")
        merged_set[vitamins_cols] = merged_set[vitamins_cols].fillna(f"information not found in {vitamins_file}")

        all_merged_data.append(merged_set)

# Concatenate all the merged sets
if all_merged_data:
    master_df = pd.concat(all_merged_data)
    master_df = master_df.reset_index()
    master_df.to_csv('master_nutrition_table_final.csv', index=False)
    print("Successfully created master_nutrition_table_final.csv")
else:
    print("No files were processed.")

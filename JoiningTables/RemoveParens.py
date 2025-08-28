import pandas as pd

# Define the input and a new output filename
input_file = 'master_nutrition_no_brackets.csv'
output_file = 'master_nutrition_final.csv'

# Read the CSV file into a DataFrame
df = pd.read_csv(input_file)

# The column name is 'Energy (kcal) kJ'. We'll extract the number from the parentheses.
# The .str.extract() method is perfect for this. The regular expression r'\((\d+)\)' does the following:
#   - \( and \) look for the literal parentheses.
#   - (\d+) looks for one or more digits (\d+) and "captures" them.
df['Energy (kcal)'] = df['Energy (kcal) kJ'].str.extract(r'\((\d+)\)')

# Now we can drop the old, messy column
df = df.drop(columns=['Energy (kcal) kJ'])

# Save the final cleaned DataFrame to a new CSV file
df.to_csv(output_file, index=False)

print(f"Successfully extracted kcal values and saved the final result to '{output_file}'")

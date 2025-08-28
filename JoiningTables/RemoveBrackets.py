import pandas as pd
import re

# Read the CSV file into a DataFrame
df = pd.read_csv('master_nutrition_cleaned.csv')

# The .replace() method with a regex is efficient for this.
# The regex '[\[\]]' will match any character that is either '[' or ']'.
# We replace all matches with an empty string ''.
# This is applied to the entire DataFrame at once.
df = df.replace(to_replace='[\[\]]', value='', regex=True)

# Save the cleaned DataFrame to a new CSV file, without the pandas index.
df.to_csv('master_nutrition_no_brackets.csv', index=False)

print(f"Successfully removed all brackets and saved the result to 'master_nutrition_no_brackets.csv'")

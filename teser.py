import pandas as pd
from fuzzywuzzy import process

# Load the food diary dataset
dummy_data_path = "Dummy data with cleaning example.xlsx"
df_dummy = pd.read_excel(dummy_data_path, sheet_name="Tabelle1")

# Load the Bangladesh Food Composition Table
nutrition_table_path = "Bangladesh Food Composition PDF to Excel.xlsx"
df_nutrition = pd.read_excel(nutrition_table_path, sheet_name="Table 1")

# Extract actual food data from the nutrition table
food_data_start_idx = 0
for idx, row in df_nutrition.iterrows():
    if "Food name in English" in str(row.values):  # Find the row where food data starts
        food_data_start_idx = idx + 1
        break

df_food_composition = df_nutrition.iloc[food_data_start_idx:].reset_index(drop=True)
df_food_composition = df_food_composition.rename(columns={df_food_composition.columns[0]: "Food_Item"})
df_food_composition = df_food_composition[["Food_Item"]].dropna()
df_food_composition["Food_Item"] = df_food_composition["Food_Item"].str.strip().replace("\n", " ", regex=True)

# Define manual mappings for foods that don't have exact matches
food_mappings = {
    "rice": "Rice, BR-28, boiled* (without salt)",  
    "boiled rice": "Rice, BR-28, boiled* (without salt)",
    "parboiled rice": "Rice, BR-28, parboiled, milled, raw",
    "white rice": "Rice, white, sunned, polished, milled, boiled* (without salt)",
    "brown rice": "Rice, brown, parboiled, milled, boiled* (without salt)",
    "bata": "Bata, raw",
    "boal": "Boal, without bones, raw",
    "catfish": "Catfish, Pabda, raw",
    "anchovy": "Anchovy, Gangetic hairfin, raw",
    "barb": "Barb, Pool barb, raw"
}

# Function to clean food entries
def clean_food_entry(original_entry):
    if pd.isna(original_entry):
        return None, None

    original_entry_lower = original_entry.lower()
    food_items = original_entry_lower.split(",")
    cleaned_items = []
    raw_cooked_items = []

    for item in food_items:
        item = item.strip()
        matched = None
        raw_cooked = None
        
        # Exact match in nutrition table
        for food in df_food_composition["Food_Item"]:
            if food.lower() in item:
                matched = food
                raw_cooked = food  # Store for raw_cooked column
                break

        # Manual mapping
        if not matched:
            for keyword, mapped_food in food_mappings.items():
                if keyword in item:
                    matched = mapped_food
                    raw_cooked = mapped_food
                    break

        # Fuzzy matching as a last resort
        if not matched:
            best_match, score = process.extractOne(item, df_food_composition["Food_Item"])
            if score > 85:  # Only accept high-confidence matches
                matched = best_match
                raw_cooked = best_match

        # If no match found
        if not matched:
            matched = f"UNKNOWN: {item}"
        
        cleaned_items.append(matched)
        raw_cooked_items.append(raw_cooked if raw_cooked else "")

    return "; ".join(cleaned_items), "; ".join(raw_cooked_items)

# Apply cleaning function
df_cleaned = df_dummy.copy()
df_cleaned[["Description of the food_CLEAN", "raw_cooked"]] = df_cleaned["Description of the food_ORIGINAL"].apply(
    lambda x: pd.Series(clean_food_entry(x))
)

# Save cleaned data
output_path = "/Users/riverngo/Desktop/Nutrition/Cleaned_Food_Diary.xlsx"
df_cleaned.to_excel(output_path, index=False)

print(f"Cleaning complete. Cleaned data saved as '{output_path}'")

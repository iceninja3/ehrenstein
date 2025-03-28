import pandas as pd
import openpyxl
import re
from food_mappings import food_mappings
from meat_mappings import fish_meat_table
from ingredient_categories import ingredient_categories
from fuzzywuzzy import process
from baseWeights import baseWeights

# ✅ Load food diary dataset
dummy_data_path = "Dummy data with cleaning example.xlsx"
df_dummy = pd.read_excel(dummy_data_path, sheet_name="Tabelle1")

# ✅ Load Bangladesh Food Composition Table
nutrition_table_path = "Bangladesh Food Composition PDF to Excel.xlsx"
df_nutrition = pd.read_excel(nutrition_table_path, sheet_name="Table 1")

# ✅ Extract actual food data from nutrition table
for idx, row in df_nutrition.iterrows():
    if "Rice" in str(row.values):
        food_data_start_idx = idx
        break
df_food_composition = df_nutrition.iloc[food_data_start_idx:].reset_index(drop=True)
df_food_composition = df_food_composition.rename(columns={df_food_composition.columns[0]: "Food_Item"})
df_food_composition = df_food_composition[["Food_Item"]].dropna()
df_food_composition["Food_Item"] = df_food_composition["Food_Item"].str.strip().replace("\n", " ", regex=True)

# ✅ Fuzzy Matching Function
def fuzzy_match(item, mapping_dict):
   item = item.strip()
   filtered_keys = []
   for word in mapping_dict.keys():
       if(abs(len(word)-len(item) ) <= 2):
           filtered_keys.append(word)
   if filtered_keys:
       bestMatch, score = process.extractOne(item, filtered_keys)
       if score >= 80:
           return mapping_dict[bestMatch]
   return None


def extract_quantity(text):
   match = re.search("\((.*?)\)", text.lower())
   if not match:
       return None, None, None
   quantityString = match.group(1).strip()
   if "half" in quantityString:
       for unit in baseWeights:
           return 0.5 * baseWeights[unit], unit, quantityString
   match = re.match(r"(\d+(?:\.\d+)?|\d+/\d+)\s*(\w+)", quantityString)
   if match:
       numString, unit = match.groups()
       if "/" in numString:
           num = eval(numString)
       else:
           num = float(numString)
       if unit in baseWeights:
            return num * baseWeights[unit], unit, quantityString
   return None, None, quantityString


# ✅ Quantity Column Parser
def parse_quantity_column(text):
    
    if not isinstance(text, str):
        return 300
    total = 0
    text = text.lower().replace("halfbowl", "half bowl")
    parts = text.split(",")
    for part in parts:
        part = part.strip()
        if "half" in part:
            for unit in baseWeights:
                if unit in part:
                    total += 0.5 * baseWeights[unit]
                    break
        else:
            match = re.match(r"(\d+(?:\.\d+)?|\d+/\d+)\s*(\w+)", part)
            if match:
                num_str, unit = match.groups()
                num = eval(num_str) if "/" in num_str else float(num_str)
                if unit in baseWeights:
                    total += num * baseWeights[unit]
    return total if total > 0 else 300

# ✅ Cleaning Function with Parenthetical Ingredient Expansion
def clean_food_entry(original_entry, quantity_text=None):
    if pd.isna(original_entry):
        return "", ""

    # Step 1: Expand ingredient-based parentheticals ONLY when safe
    def expand_parentheticals(entry):
        pattern = re.compile(r"(\w[\w ]*?)\s*\(([^)]+)\)")
        def replace_fn(match):
            base, inside = match.group(1).strip(), match.group(2).strip()
            if base.lower() in food_mappings or base.lower() in fish_meat_table:
                if not re.search(r"\d+|plate|pcs|bowl|glass|cup|ml|cm|pac", inside):
                    inner_items = ", ".join(i.strip() for i in inside.split(","))
                    return f"{base}, {inner_items}"
            return match.group(0)
        return pattern.sub(replace_fn, entry)

    original_entry = expand_parentheticals(original_entry)

    # Step 2: Split and clean individual food items
    food_items = re.split(r"\swith\s|\sand\s|,", original_entry)
    cleaned_items = []
    raw_cooked_items = []
    temp_storage = []

    for item in food_items:
        item = item.strip()
        weight, unit, quantity_str = extract_quantity(item)
        matching_item = re.sub(r"\(.*?\)", "", item).strip().lower()
        matched_food = food_mappings.get(matching_item, fuzzy_match(matching_item, food_mappings))
        matched_fish_meat = fish_meat_table.get(matching_item, fuzzy_match(matching_item, fish_meat_table))
        cleaned_name = matched_fish_meat or matched_food
        category = ingredient_categories.get(cleaned_name, None)

        if cleaned_name and not weight:
            if category == "garnish":
                weight = 10
            elif category == "oil":
                weight = 15

        temp_storage.append({
            "name": cleaned_name,
            "weight": weight,
            "category": category,
            "matched_fish_meat": matched_fish_meat
        })

    total_quantity = parse_quantity_column(quantity_text)

    fixed_items = [x for x in temp_storage if x["weight"] is not None]
    remaining_items = [x for x in temp_storage if x["weight"] is None and x["name"]]

    if remaining_items:
        proteins = [x for x in remaining_items if ingredient_categories.get(x["name"]) == "protein"]
        non_proteins = [x for x in remaining_items if ingredient_categories.get(x["name"]) != "protein"]
        if proteins and non_proteins:
            total_protein_weight = total_quantity * 0.65
            total_non_protein_weight = total_quantity * 0.35
            for item in proteins:
                item["weight"] = total_protein_weight / len(proteins)
            for item in non_proteins:
                item["weight"] = total_non_protein_weight / len(non_proteins)
        else:
            for item in remaining_items:
                item["weight"] = total_quantity / len(remaining_items)

    for item in temp_storage:
        if not item["name"]:
            cleaned_items.append("UNKNOWN")
        elif item["weight"] is not None:
            weight_per_100g = round(item["weight"] / 100, 2)
            cleaned_items.append(f"{item['name']} {{{weight_per_100g}}}")
            if item["matched_fish_meat"]:
                raw_cooked_items.append(item["name"])
        else:
            cleaned_items.append(item["name"])
            if item["matched_fish_meat"]:
                raw_cooked_items.append(item["name"])

    return "; ".join(cleaned_items), "; ".join(raw_cooked_items)

# ✅ Apply cleaning
df_cleaned = df_dummy.copy()
df_cleaned[["Description of the food_ CLEAN", "raw_cooked"]] = df_cleaned.apply(
    lambda row: pd.Series(clean_food_entry(row["Description of the food_ORIGINAL"], row.get("Quantity_ORIGINAL"))), axis=1
)

# ✅ Save output
df_cleaned.to_excel("Cleaned_Food_Diary.xlsx", index=False)
print("\u2705 Cleaning complete. Check 'Cleaned_Food_Diary.xlsx'")

#pickle and chips will be found in india food table (note: for now unknown items will be marked as suhc )
#weighting might need to be fixed?
# optional: consider adding minimum quantity for each item (nonproteins could always be at least X amount of grams
#proteins coudl always be at least Y amount of grams )
#fish curry 
#fish fry
import pandas as pd
import openpyxl
import re
from food_mappings import food_mappings
from meat_mappings import fish_meat_table
from ingredient_categories import ingredient_categories
from fuzzywuzzy import process
from baseWeights import baseWeights
from dish_mappings import dish_mappings
from variables import (
    PROTEIN_WEIGHT_RATIO,
    NON_PROTEIN_WEIGHT_RATIO,
    DEFAULT_TOTAL_WEIGHT,
    DEFAULT_OIL_WEIGHT,
    DEFAULT_GARNISH_WEIGHT,
    FUZZY_MATCH_THRESHOLD,
    NUM_ITEMS_NECESSARY_TO_EXPAND,
)


# ✅ Load food diary dataset
dummy_data_path = "jar.xlsx"
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
       if score >= FUZZY_MATCH_THRESHOLD:
           return mapping_dict[bestMatch]
   return None

def extract_quantity(text):
   match = re.search("\((.*?)\)", text.lower())
   if not match:
       return None, None, None
   quantityString = match.group(1).strip()
   
   
   if "half" in quantityString:
        for unit in baseWeights:
            if unit in quantityString:
                return 0.5 * baseWeights[unit], unit, quantityString
   if "quarter" in quantityString:
        for unit in baseWeights:
            if unit in quantityString:
                return 0.25 * baseWeights[unit], unit, quantityString

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
        return  DEFAULT_TOTAL_WEIGHT
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
        if "quarter" in part:
            for unit in baseWeights:
                if unit in part:
                    total += 0.25 * baseWeights[unit]
                    break
        else:
            match = re.match(r"(\d+(?:\.\d+)?|\d+/\d+)\s*(\w+)", part)
            if match:
                num_str, unit = match.groups()
                num = eval(num_str) if "/" in num_str else float(num_str)
                if unit in baseWeights:
                    total += num * baseWeights[unit]
    return total if total > 0 else DEFAULT_TOTAL_WEIGHT

# ✅ Cleaning Function with Enhanced Dish-Based Parenthetical Expansion
def clean_food_entry(original_entry, quantity_text=None):
    if pd.isna(original_entry):
        return "", ""
    original_entry = re.sub(r"\[.*?\]", "", original_entry)
    entry_lower = original_entry.strip().lower()

    # Step 1: Expand parentheticals with dish logic
    def expand_parentheticals(entry):
        pattern = re.compile(r"([\w\s]+?)\s*\(([^)]+)\)")

        def replace_fn(match):
            base = match.group(1).strip().lower()
            # base = match.group(2).strip().lower()
            inside = match.group(2).strip().lower()
            inside_items = [i.strip() for i in inside.split(",") if i.strip()]

            # Dish-based logic
            matched_dish = next((dish for dish in dish_mappings if dish in base), None)
            if matched_dish:
                if len(inside_items) < NUM_ITEMS_NECESSARY_TO_EXPAND:
                    return ", ".join(dish_mappings[matched_dish])

                # Find main protein
                main_protein = (
                    food_mappings.get(base)
                    or fish_meat_table.get(base)
                    or next((ing for ing in dish_mappings[matched_dish] if ing in fish_meat_table or ing in food_mappings), None)
                )

                seen = set()
                combined = []

                # Start with main protein (if available)
                if main_protein:
                    combined.append(main_protein)
                    seen.add(main_protein)

                for item in inside_items:
                    if item not in seen:
                        combined.append(item)
                        seen.add(item)

                return ", ".join(combined)

            if base in food_mappings or base in fish_meat_table:
                is_quantity = any(unit in inside.lower() for unit in baseWeights)
                if not is_quantity:
                    return f"{base}, {', '.join(inside_items)}"

            return match.group(0)

        return pattern.sub(replace_fn, entry.lower())

    original_entry = expand_parentheticals(original_entry)

    # Step 2: Split and clean individual food items
    food_items = re.split(r"\swith\s|\sand\s|,", original_entry)
    cleaned_items = []
    raw_cooked_items = []
    temp_storage = []

    i = 0
    while i < len(food_items):
        item = food_items[i].strip().lower()
        base_item = re.sub(r"\s*\(.*?\)", "", item).strip()

        if base_item in dish_mappings:
            expanded_items = dish_mappings[base_item]
            food_items[i:i+1] = expanded_items  # replace in place
            continue  # re-check current index
        else:
            weight, unit, quantity_str = extract_quantity(item)
            matching_item = re.sub(r"\(.*?\)", "", item).strip().lower()
            matched_food = food_mappings.get(matching_item, fuzzy_match(matching_item, food_mappings))
            matched_fish_meat = fish_meat_table.get(matching_item, fuzzy_match(matching_item, fish_meat_table))
            cleaned_name = matched_fish_meat or matched_food
            category = ingredient_categories.get(cleaned_name, None)

            if cleaned_name and not weight:
                if category == "garnish":
                    weight = DEFAULT_GARNISH_WEIGHT
                elif category == "oil":
                    weight = DEFAULT_OIL_WEIGHT

            temp_storage.append({
                "name": cleaned_name,
                "weight": weight,
                "category": category,
                "matched_fish_meat": matched_fish_meat
            })

        i += 1

    total_quantity = parse_quantity_column(quantity_text)

    fixed_items = [x for x in temp_storage if x["weight"] is not None]
    remaining_items = [x for x in temp_storage if x["weight"] is None and x["name"]]

    if remaining_items:
        proteins = [x for x in remaining_items if ingredient_categories.get(x["name"]) == "protein"]
        non_proteins = [x for x in remaining_items if ingredient_categories.get(x["name"]) != "protein"]
        if proteins and non_proteins:
            total_protein_weight = total_quantity * PROTEIN_WEIGHT_RATIO
            total_non_protein_weight = total_quantity * NON_PROTEIN_WEIGHT_RATIO

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
print(clean_food_entry("small chicken curry"))
print(clean_food_entry("small fish curry"))
#print(clean_food_entry("biscuit (half bowl)"))
# print(clean_food_entry("biscuit (half bowl, 11.5cm)"))
# print(clean_food_entry("fish curry"))

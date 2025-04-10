import pandas as pd
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
    FILE_NAME,
)


def fuzzy_match(item, mapping_dict):
    item = item.strip()
    filtered_keys = [word for word in mapping_dict if abs(len(word) - len(item)) <= 2]
    if filtered_keys:
        bestMatch, score = process.extractOne(item, filtered_keys)
        if score >= FUZZY_MATCH_THRESHOLD:
            return mapping_dict[bestMatch]
    return None

def fuzzy_match_key(item, mapping_dict):
    item = item.strip()
    filtered_keys = [word for word in mapping_dict if abs(len(word) - len(item)) <= 2]
    if filtered_keys:
        bestMatch, score = process.extractOne(item, filtered_keys)
        if score >= FUZZY_MATCH_THRESHOLD:
            return bestMatch
    return None

def extract_quantity(text):
    match = re.search(r"\((.*?)\)", str(text).lower())
    if not match:
        return None, None, None
    
    quantity_string = match.group(1).strip()
    
    parts = [p.strip() for p in quantity_string.split(",")]
    for part in parts:
        lowered = part.lower()
        if lowered in baseWeights:
            return baseWeights[lowered], lowered, quantity_string
        
        if "half" in part:
            for unit in baseWeights:
                if unit in part:
                    return 0.5 * baseWeights[unit], unit, quantity_string
                
        if "quarter" in part:
            for unit in baseWeights:
                if unit in part:
                    return 0.25 * baseWeights[unit], unit, quantity_string
        match = re.match(r"(\d+(?:\.\d+)?|\d+/\d+)\s*(\w+)", part)
        if match:
            num_str, unit = match.groups()
            num = eval(num_str) if "/" in num_str else float(num_str)
            if unit in baseWeights:
                return num * baseWeights[unit], unit, quantity_string
    return None, None, quantity_string

def parse_quantity_column(text):
    if not isinstance(text, str):
        return DEFAULT_TOTAL_WEIGHT
    total = 0
    text = text.lower().replace("halfbowl", "half bowl")
    parts = text.split(",")
    for part in parts:
        part = part.strip()
        lowered = part.lower()

        # Handle special named units like "all time"

        
        if "half" in part:
            for unit in baseWeights:
                if unit in part:
                    total += 0.5 * baseWeights[unit]
                    break
        elif "quarter" in part:
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

def clean_food_entry(original_entry, quantity_text=None):
    if pd.isna(original_entry):
        return "", ""
    original_entry = re.sub(r"\[.*?\]", "", original_entry)
    entry_lower = original_entry.strip().lower()

    # Step 1: Expand parentheticals with dish logic
    def expand_parentheticals(entry):  # handles our () contents
        pattern = re.compile(r"([\w\s]+?)\s*\(([^)]+)\)")  # splits contents into what is in the () and what is outside them 

        def replace_fn(match):
            base = match.group(1).strip().lower()
            inside = match.group(2).strip().lower()
            itemsList = inside.split(",")
            inside_items = []
            for item in itemsList:
                cleaned = item.strip()
                if cleaned: 
                    inside_items.append(cleaned)

            # Dish-based logic
            matched_dish = next((dish for dish in dish_mappings if dish.lower() == base.lower()), None)
            
            if not matched_dish:
                matched_dish = fuzzy_match_key(base, dish_mappings)

            if matched_dish:
                if len(inside_items) < NUM_ITEMS_NECESSARY_TO_EXPAND:
                    return ", ".join(dish_mappings[matched_dish])

                
                matched_ingredient = next(
                    (ing for ing in list(food_mappings) + list(fish_meat_table)
                     if ing in base and ing not in inside_items),
                    None
                )

                seen = set()
                combined = []

                if matched_ingredient:
                    combined.append(matched_ingredient)
                    seen.add(matched_ingredient)

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
    food_items = re.split(r"\swith\s|\sand\s|,(?![^()]*\))", original_entry)

    cleaned_items = []
    raw_cooked_items = []
    temp_storage = []

    i = 0
    while i < len(food_items):
        item = food_items[i].strip().lower()
        base_item = re.sub(r"\s*\(.*?\)", "", item).strip()
        matched_dish = dish_mappings.get(base_item)
        if not matched_dish:
            matched_dish = dish_mappings.get(fuzzy_match_key(base_item, dish_mappings))

        if matched_dish:
            food_items[i:i+1] = matched_dish  # replace in place
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



if __name__ == "__main__":
    input_file = FILE_NAME
    df = pd.read_excel(input_file, sheet_name="Tabelle1", header=1)
    
    description_cols = []
    quantity_cols = []
    for i, col in enumerate(df.columns):
        if isinstance(col, str) and "description of the food" in col.lower():
            description_cols.append(col)
            quantity_cols.append(df.columns[i + 1] if i + 1 < len(df.columns) else None)

    for i, (desc_col, quant_col) in enumerate(zip(description_cols, quantity_cols)):
        new_clean_col = f"{desc_col}_CLEAN"
        new_raw_col = f"raw_cooked_{i+1}"

        cleaned_data = df.apply(
            lambda row: pd.Series(clean_food_entry(row[desc_col], row.get(quant_col))), axis=1
        )
        cleaned_data.columns = [new_clean_col, new_raw_col]

        quant_index = df.columns.get_loc(quant_col)
        for col_name in reversed(cleaned_data.columns): 
            df.insert(quant_index + 1, col_name, cleaned_data[col_name])
    
    df.to_excel("Cleaned_Bangladesh_Food_Diary.xlsx", index=False)
    print("✅ Cleaning complete.")

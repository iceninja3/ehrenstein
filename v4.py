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
unknown_itemsed = set()

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
    if not isinstance(text, str): #if this not a string assume 300 
        return DEFAULT_TOTAL_WEIGHT #variable used to determine weight to be split among dishes that were given no metric 

    total = 0
    text = text.lower().replace("halfbowl", "half bowl")
    parts = text.split(",")

    for part in parts:
        part = part.strip()
        lowered = part.lower()

        
        if lowered in baseWeights:
            total += baseWeights[lowered] #if the variable is found in base weights change it 
            continue  

        
        if "half" in lowered:
            for unit in baseWeights: 
                if unit in lowered:
                    total += 0.5 * baseWeights[unit] #if the unit in base weights is found in the table, add it 
                    break

        
        elif "quarter" in lowered:
            for unit in baseWeights:
                if unit in lowered:
                    total += 0.25 * baseWeights[unit]
                    break

        
        else:
            match = re.match(r"(\d+(?:\.\d+)?|\d+/\d+)\s*(.+)", lowered)
            if match:
                num_str, unit = match.groups()
                num = eval(num_str) if "/" in num_str else float(num_str)
                unit = unit.strip()
                if unit in baseWeights:
                    total += num * baseWeights[unit]

    return total if total > 0 else DEFAULT_TOTAL_WEIGHT


def clean_food_entry(original_entry, quantity_text=None):
    if pd.isna(original_entry):
        return "", ""
    original_entry = re.sub(r"\[.*?\]", "", original_entry)
    entry_lower = original_entry.strip().lower()

    # Step 1: Expand parentheticals with dish logic - skip quantity items
    def expand_parentheticals(entry):
        pattern = re.compile(r"([\w\s]+?)\s*\(([^)]+)\)")
        
        def replace_fn(match):
            base = match.group(1).strip().lower()
            inside = match.group(2).strip().lower()
            
            # Skip expansion if parentheses contain a quantity
            weight, _, _ = extract_quantity(f"({inside})")
            if weight is not None:
                return match.group(0)  # return original without expansion
            
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
            
            matched_base = (
                food_mappings.get(base)
                or fish_meat_table.get(base)
                or fuzzy_match(base, food_mappings)
                or fuzzy_match(base, fish_meat_table)
            )

            if matched_base:
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
        
        # Handle dish with quantity
        dish_quantity_match = re.match(r"^\s*([\w\s]+?)\s*\((.*?)\)\s*$", item)
        if dish_quantity_match:
            base_item = dish_quantity_match.group(1).strip()
            inside_str = dish_quantity_match.group(2).strip()
            
            # Check if base_item is a recognized dish
            dish_key = None
            if base_item in dish_mappings:
                dish_key = base_item
            else:
                dish_key = fuzzy_match_key(base_item, dish_mappings)
                
            if dish_key:
                dish_ingredients = dish_mappings[dish_key]
                dish_weight, _, _ = extract_quantity(f"({inside_str})")
                
                if dish_weight is not None:
                    # Create lists to track ingredients by type
                    proteins = []
                    non_proteins = []
                    dish_items = []  # Will store all ingredients in order
                    
                    # Process each ingredient in ORIGINAL ORDER
                    for ing in dish_ingredients:
                        # Clean ingredient name
                        cleaned_ing = None
                        category = None
                        matched_fish_meat = False
                        
                        # Try food mappings
                        cleaned_ing = food_mappings.get(ing)
                        if not cleaned_ing:
                            cleaned_ing = fuzzy_match(ing, food_mappings)
                        
                        # Try meat/fish mappings
                        if not cleaned_ing:
                            cleaned_ing = fish_meat_table.get(ing)
                            if cleaned_ing:
                                matched_fish_meat = True
                        if not cleaned_ing:
                            cleaned_ing = fuzzy_match(ing, fish_meat_table)
                            if cleaned_ing:
                                matched_fish_meat = True
                        
                        # If still not found, use original
                        if not cleaned_ing:
                            cleaned_ing = ing
                        
                        # Get category
                        category = ingredient_categories.get(cleaned_ing, None)
                        
                        # Create ingredient object
                        ingredient_obj = {
                            "name": cleaned_ing,
                            "category": category,
                            "matched_fish_meat": matched_fish_meat,
                            "weight": None
                        }
                        
                        # Set fixed weights if applicable
                        if category == "garnish":
                            ingredient_obj["weight"] = DEFAULT_GARNISH_WEIGHT
                        elif category == "oil":
                            ingredient_obj["weight"] = DEFAULT_OIL_WEIGHT
                        
                        # Add to appropriate list
                        if category == "protein":
                            proteins.append(ingredient_obj)
                        else:
                            non_proteins.append(ingredient_obj)
                            
                        # Always add to dish_items to maintain order
                        dish_items.append(ingredient_obj)
                    
                    # Distribute dish_weight ONLY to non-fixed ingredients
                    non_fixed_proteins = [p for p in proteins if p["weight"] is None]
                    non_fixed_non_proteins = [np for np in non_proteins if np["weight"] is None]
                    
                    if non_fixed_proteins and non_fixed_non_proteins:
                        protein_total = dish_weight * PROTEIN_WEIGHT_RATIO
                        non_protein_total = dish_weight * NON_PROTEIN_WEIGHT_RATIO
                        
                        # Assign weights to non-fixed proteins
                        for item in non_fixed_proteins:
                            item["weight"] = protein_total / len(non_fixed_proteins)
                        
                        # Assign weights to non-fixed non-proteins
                        for item in non_fixed_non_proteins:
                            item["weight"] = non_protein_total / len(non_fixed_non_proteins)
                    else:
                        # Combine all non-fixed items
                        non_fixed_items = [item for item in dish_items if item["weight"] is None]
                        if non_fixed_items:
                            each_weight = dish_weight / len(non_fixed_items)
                            for item in non_fixed_items:
                                item["weight"] = each_weight
                    
                    # Add all dish ingredients to temp_storage in ORIGINAL ORDER
                    temp_storage.extend(dish_items)
                    i += 1
                    continue

        # Existing processing for non-dish items
        base_item = re.sub(r"\s*\(.*?\)", "", item).strip()
        dish_key = None
        if base_item in dish_mappings:
            dish_key = base_item
        else:
            dish_key = fuzzy_match_key(base_item, dish_mappings)

        if dish_key:
            # Replace dish with its ingredients in original order
            food_items[i:i+1] = dish_mappings[dish_key]
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
        
    # Process quantity column for remaining items
    total_quantity = parse_quantity_column(quantity_text)

    fixed_items = [x for x in temp_storage if x["weight"] is not None]
    remaining_items = [x for x in temp_storage if x["weight"] is None and x["name"]]

    if remaining_items:
        proteins = [x for x in remaining_items if x["category"] == "protein"]
        non_proteins = [x for x in remaining_items if x["category"] != "protein"]
        
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

    for i, item in enumerate(temp_storage):
        if not item["name"]:
            cleaned_items.append("UNKNOWN")
            original_str = food_items[i].strip() if i < len(food_items) else ""
            if original_str:
                unknown_itemsed.add(original_str)
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


input_file = FILE_NAME
df = pd.read_excel(input_file, sheet_name="Tabelle1", header=1)

description_cols = [] 
quantity_cols = []
for i, col in enumerate(df.columns): #finds all our columns that need to be cleaned 
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
print("Cleaning complete.")
print(clean_food_entry("pulao (oil, onion, raisins)"))
if unknown_itemsed:
    print("\n UNKNOWN items found:")
    for item in sorted(unknown_itemsed):
        print(f" - {item}")

        #papaya vegetable (pulse,lentils,onion,chili,coriander leaves)
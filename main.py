import pandas as pd
import openpyxl
import re
from fuzzywuzzy import process
# Load the food diary dataset

dummy_data_path = "Dummy data with cleaning example.xlsx"


df_dummy = pd.read_excel(dummy_data_path, sheet_name="Tabelle1")
# Load the Bangladesh Food Composition Table
nutrition_table_path = "Bangladesh Food Composition PDF to Excel.xlsx"
df_nutrition = pd.read_excel(nutrition_table_path, sheet_name="Table 1")
# Extract actual food data from the nutrition table
for idx, row in df_nutrition.iterrows():
    if "Rice" in str(row.values):  # Find the row where food data starts
        food_data_start_idx = idx
        break
df_food_composition = df_nutrition.iloc[food_data_start_idx:].reset_index(drop=True)
df_food_composition = df_food_composition.rename(columns={df_food_composition.columns[0]: "Food_Item"})
df_food_composition = df_food_composition[["Food_Item"]].dropna()
df_food_composition["Food_Item"] = df_food_composition["Food_Item"].str.strip().replace("\n", " ", regex=True)

food_mappings = {
    # General Rice Terms
    "rice": "Rice, BR-28, boiled* (without salt)",  # Override raw versions with boiled
    "boiled rice": "Rice, BR-28, boiled* (without salt)",
    "parboiled rice": "Rice, BR-28, parboiled, milled, raw",
    "white rice": "Rice, white, sunned, polished, milled, boiled* (without salt)",
    "brown rice": "Rice, brown, parboiled, milled, boiled* (without salt)",
    "puffed rice": "Rice, puffed, salted",
    "rice puffs": "Rice, puffed, salted",
    "popped rice": "Rice, popped",
    "Rice pops": "Rice, popped",
    "flaked rice": "Rice flaked",
    "rice flakes": "Rice flakes, white grain, water-soaked",
    "chira": "Rice flakes, white grain, water-soaked",
    # Corn/Maize
    "corn": "Maize/corn, yellow, dried, raw",
    "fish oil": "Fish oil, cod liver",
    "cod liver oil": "Fish oil, cod liver",
    # Margarine & Mayonnaise
    "margarine": "Margarine",
    "mayonnaise": "Mayonnaise, salted",
    "salted mayonnaise": "Mayonnaise, salted",
    # Beverages and Drinks
    "coconut water": "Coconut water",
    # Common Carbonated Drinks
    "cola": "Soft drinks, carbonated",
    "coke": "Soft drinks, carbonated",
    "pepsi": "Soft drinks, carbonated",
}


fish_meat_table = {
    "salmon": "Salmon, raw",
    "tilapia": "Tilapia, raw",
    "pangas": "Pangasius, raw",
    "carp": "Carp, raw",
    "pomfret": "Pomfret, raw",
    "beef": "Beef, raw",
    "chicken": "Chicken, raw",
    "mutton": "Mutton, raw",
    "lamb": "Lamb, raw",
    "duck": "Duck, raw",
    "pork": "Pork, raw",
}

# ✅ Preprocessing Function
def preprocess_text(text):
    """Removes numbers, units, and extra words inside parentheses."""
    text = text.lower()
    text = re.sub(r"\(.*?\)", "", text)  # Remove parentheses content
    text = re.sub(r"\b\d+(\.\d+)?\b", "", text)  # Remove numbers
    text = re.sub(r"\bpcs\b|\bbowl\b|\bglass\b|\bplate\b", "", text)  # Remove size units
    return text.strip()

# ✅ Fuzzy Matching Function
def fuzzy_match(item, mapping_dict):
    """Applies fuzzy matching to improve recognition of slightly misspelled items."""
    item = item.strip()

    # 🔹 Filter words by length (±2 characters)
    filtered_keys = [word for word in mapping_dict.keys() if abs(len(word) - len(item)) <= 2]

    # 🔹 Use fuzzy matching only within filtered words
    if filtered_keys:
        best_match, score = process.extractOne(item, filtered_keys)
        if score >= 80:  # Accept only highly confident matches
            return mapping_dict[best_match]

    return None  # Return None if no match is found

# ✅ **Cleaning Function with Raw_Cooked Integration**
def clean_food_entry(original_entry):
    if pd.isna(original_entry):
        return "", ""  # Skip empty entries, return empty raw_cooked

    original_entry = preprocess_text(original_entry)
    food_items = original_entry.split(",")
    cleaned_items = []
    raw_cooked_items = []

    for item in food_items:
        item = item.strip()
        
        # ✅ Try fuzzy matching in `food_mappings`
        matched_food = food_mappings.get(item, fuzzy_match(item, food_mappings))
        
        # ✅ Try fuzzy matching in `fish_meat_table`
        matched_fish_meat = fish_meat_table.get(item, fuzzy_match(item, fish_meat_table))
        
        # ✅ If it's in `fish_meat_table`, add to both clean & raw_cooked
        if matched_fish_meat:
            cleaned_items.append(matched_fish_meat)  # Add to cleaned column
            raw_cooked_items.append(matched_fish_meat)  # Also add to raw_cooked column
        elif matched_food:
            cleaned_items.append(matched_food)  # Add normal food item
        else:
            cleaned_items.append(f"UNKNOWN: {item}")  # Fallback for unknowns

    return "; ".join(cleaned_items), "; ".join(raw_cooked_items)

# ✅ Apply function to clean dataset & update `raw_cooked`
df_cleaned = df_dummy.copy()
df_cleaned[["Description of the food_ CLEAN", "raw_cooked"]] = df_cleaned["Description of the food_ORIGINAL"].apply(
    lambda x: pd.Series(clean_food_entry(x))
)

# ✅ Save cleaned dataset
df_cleaned.to_excel("Cleaned_Food_Diary.xlsx", index=False)
print("✅ Cleaning complete. Check 'Cleaned_Food_Diary.xlsx'")



#
#def preprocess_text(text):
#    """Removes numbers, units, and extra words inside parentheses."""
#    text = text.lower()
#    text = re.sub(r"\(.*?\)", "", text)  # Remove content inside parentheses
#    text = re.sub(r"\b\d+(\.\d+)?\b", "", text)  # Remove standalone numbers
#    text = re.sub(r"\bpcs\b|\bbowl\b|\bglass\b|\bplate\b", "", text)  # Remove size units
#    return text.strip()
#
#def fuzzy_match(item, food_mappings):
#    """Improved fuzzy matching to prevent incorrect big leaps."""
#    item = item.strip()
#
#    #Filter food names by similar length (±2 characters)
#    filtered_food_keys = [word for word in food_mappings.keys() if abs(len(word) - len(item)) <= 2]
#
#
#    # exact_substring_matches = [word for word in filtered_food_keys if item in word]
#    # if exact_substring_matches:
#    #     return food_mappings[exact_substring_matches[0]]  # Return the first best match
#
#    # 3️⃣ **Use fuzzy matching only within the filtered words**
#    if filtered_food_keys:
#        best_match, score = process.extractOne(item, filtered_food_keys)
#        if score >= 80:  # Only accept confident matches
#            return food_mappings[best_match]
#
#    return f"UNKNOWN: {item}"  # Return unknown if no match is found
#
## ✅ **Updated Cleaning Function with Fuzzy Matching Integrated**
#def clean_food_entry(original_entry):
#    if pd.isna(original_entry):
#        return "UNKNOWN"  # Skip empty entries
#    
#    original_entry = preprocess_text(original_entry)
#    food_items = original_entry.split(",")
#    cleaned_items = []
#
#    for item in food_items:
#        item = item.strip()
#        matched = food_mappings.get(item)
#
#        # ✅ **Apply fuzzy matching if no exact match found**
#        if not matched:
#            matched = fuzzy_match(item, food_mappings)
#
#        cleaned_items.append(matched)
#
#    return "; ".join(cleaned_items)
#
## ✅ **Apply the function to clean the dataset**
#df_cleaned = df_dummy.copy()
#df_cleaned["Description of the food_ CLEAN"] = df_cleaned["Description of the food_ORIGINAL"].apply(clean_food_entry)
#
## ✅ **Save the cleaned dataset**
#df_cleaned.to_excel("Cleaned_Food_Diary.xlsx", index=False)
#print("Cleaning complete. Check 'Cleaned_Food_Diary.xlsx'")
#
#
#
#
#
#
#
#
#
#
#
#
#
#
#





















#import pandas as pd
#import openpyxl
#import re
## Load the food diary dataset
#
#dummy_data_path = "Dummy data with cleaning example.xlsx"
#
#
#df_dummy = pd.read_excel(dummy_data_path, sheet_name="Tabelle1")
## Load the Bangladesh Food Composition Table
#nutrition_table_path = "Bangladesh Food Composition PDF to Excel.xlsx"
#df_nutrition = pd.read_excel(nutrition_table_path, sheet_name="Table 1")
## Extract actual food data from the nutrition table
#for idx, row in df_nutrition.iterrows():
#    if "Rice" in str(row.values):  # Find the row where food data starts
#        food_data_start_idx = idx
#        break
#df_food_composition = df_nutrition.iloc[food_data_start_idx:].reset_index(drop=True)
#df_food_composition = df_food_composition.rename(columns={df_food_composition.columns[0]: "Food_Item"})
#df_food_composition = df_food_composition[["Food_Item"]].dropna()
#df_food_composition["Food_Item"] = df_food_composition["Food_Item"].str.strip().replace("\n", " ", regex=True)
#
#food_mappings = {
#    # General Rice Terms
#    "rice": "Rice, BR-28, boiled* (without salt)",  # Override raw versions with boiled
#    "boiled rice": "Rice, BR-28, boiled* (without salt)",
#    "parboiled rice": "Rice, BR-28, parboiled, milled, raw",
#    "white rice": "Rice, white, sunned, polished, milled, boiled* (without salt)",
#    "brown rice": "Rice, brown, parboiled, milled, boiled* (without salt)",
#    "puffed rice": "Rice, puffed, salted",
#    "rice puffs": "Rice, puffed, salted",
#    "popped rice": "Rice, popped",
#    "Rice pops": "Rice, popped",
#    "flaked rice": "Rice flaked",
#    "rice flakes": "Rice flakes, white grain, water-soaked",
#    "chira": "Rice flakes, white grain, water-soaked",
#    # Corn/Maize
#    "corn": "Maize/corn, yellow, dried, raw",
#    "maize": "Maize/corn, yellow, dried, raw",
#    "corn flour": "Maize/corn flour, whole, white",
#    "maize flour": "Maize/corn flour, whole, white",
#    "cornmeal": "Maize/corn, yellow, dried, raw",
#    "sweet corn": "Sweet corn, yellow, on the cob, raw",
#    "popcorn": "Popcorn, maize (salt added)",
#    "barley": "Barley, whole-grain, raw",
#    "sweet biscuit": "Biscuit, sweet*",
#    "biscuit": "Biscuit, sweet*",
#    "cake": "Biscuit, sweet*",
#     "bread": "Bread, bun/roll",
#    "bread roll": "Bread, bun/roll",
#    "bun": "Bread, bun/roll",
#    "white bread": "Bread, white, for toasting",
#   "toast": "Bread, white, for toasting",
#   "toasted bread": "Bread, white, for toasting",
#    # Millets and Sorghum
#    "foxtail millet": "Millet, Foxtail, raw",
#    "proso millet": "Millet, Proso, whole-grain, raw",
#    "millet": "Millet, Proso, whole-grain, raw",  # General millet maps to Proso
#    "pear millet": "Pear millet, whole-grain, raw",
#    "sorghum": "Sorghum, raw",
#    "broomcorn": "Sorghum, raw",
#    "Broom corn": "Sorghum, raw",
#    # Wheat and Flour
#    "wheat": "Wheat, whole, raw",
#    "wheat flour": "Wheat, flour, white",
#    "white wheat flour": "Wheat flour, white, refined",
#    "whole wheat flour": "Wheat flour, brown, whole grain, raw",
#    "whole wheat": "Wheat, whole, raw",
#    "semolina": "Semolina, wheat, raw",
#    "vermicelli": "Vermicelli, boiled* (without salt)",
#    "ruti": "Ruti*",
#    "gourd": "Gourd, bitter, boiled* (without salt)",  # Override raw gourds with best cooked option
#    "ash gourd": "Gourd, ash, raw",
#    "bitter gourd": "Gourd, bitter, boiled* (without salt)",
#    "bottle gourd": "Gourd, bottle, raw",
#    "pointed gourd": "Gourd, pointed, boiled* (without salt)",
#    "ridge gourd": "Gourd, ridge, raw",
#    "snake gourd": "Gourd, snake, raw",
#    "sponge gourd": "Gourd, sponge, raw",
#    "teasle gourd": "Gourd, teasle, boiled* (without salt)",
#    "gourd fry": "Gourd, bitter, fry*",  # New addition
#    # Vegetables
#    "amaranth": "Amaranth, stem, raw",
#    "scarlet runner bean": "Bean, scarlet runner, raw",
#    "beans": "Bean, seeds and pods, raw",
#    "beetroot": "Beet root, red, raw",
#    "brinjal": "Brinjal, purple, long, boiled* (without salt)",
#    "eggplant": "Brinjal, purple, long, boiled* (without salt)",  # Eggplant = Brinjal
#    "broad beans": "Broad beans, raw",
#    "cabbage": "Cabbage, boiled* (without salt)",
#    "carrot": "Carrot, boiled* (without salt)",
#    "cauliflower": "Cauliflower, boiled* (without salt)",
#    "cowpea": "Cowpea, boiled* (without salt)",
#    "black-eyed pea": "Cowpea, boiled* (without salt)",
#    "black eyed pea": "Cowpea, boiled* (without salt)",
#    "cucumber": "Cucumber, peeled, raw",
#    "drumstick": "Drumstick, pods, raw",
#    "moringa": "Drumstick, pods, raw",
#    "garlic": "Garlic, raw",
#    # Lentils, Grams, and Beans (with alternative names)
#    "bengal gram": "Bengal gram, whole, boiled* (without salt)",
#    "chickpeas": "Bengal gram, whole, boiled* (without salt)",
#    "black gram": "Black gram, split, dried, raw",
#    "urad beans": "Black gram, split, dried, raw",  # Alternative name for Black Gram
#    "green gram": "Green gram, split, boiled* (without salt)",
#    "mung beans": "Green gram, split, boiled* (without salt)",  # Alternative name for Green Gram
#    "red gram": "Red gram, split, dried, raw",
#    "pigeon pea": "Red gram, split, dried, raw",  # Alternative name for Red Gram
#    "grass pea": "Grass pea, split, boiled* (without salt)",
#    "pea": "Pea, boiled* (without salt)",
#    "soybean": "Soybean, dried, raw",
#    # Okra & Onions (handling all name variations)
#    "okra": "Okra/ladies finger, boiled* (without salt)",
#    "ladies finger": "Okra/ladies finger, boiled* (without salt)",
#    "lady fingers": "Okra/ladies finger, boiled* (without salt)",
#    "ladyfingers": "Okra/ladies finger, boiled* (without salt)",
#    "onion": "Onion, raw",
#    "papaya": "Papaya, unripe, boiled* (without salt)",
#    "plantain": "Plantain, boiled* (without salt)",
#    "pumpkin": "Pumpkin, boiled* (without salt)",
#    "radish": "Radish, boiled* (without salt)",
#    "tomato": "Tomato, red, ripe, boiled* (without salt)",
#    "green tomato": "Tomato, green, raw",
#    "turnip": "Turnip, raw",
#    "agathi": "Agathi, raw",
#    "alligator weed": "Alligator weed, raw",
#    "amaranth leaves": "Amaranth, leaves, green, boiled* (without salt)",
#    "red amaranth": "Amaranth, leaves, red, boiled* (without salt)",
#    "red amaranth leaves": "Amaranth, leaves, red, boiled* (without salt)",
#    "green amaranth leaves": "Amaranth, leaves, green, boiled* (without salt)",
#    "dock leaves": "Dock leaves, raw",
#    "beet greens": "Beet greens leaves",
#    "beet greens leaves": "Beet greens leaves",
#    "bengal dayflower": "Bengal dayflower, leaves, raw",
#    "dayflower": "Bengal dayflower, leaves, raw",
#    "bengal leaves": "Bengal dayflower, leaves, raw",
#    "bengal dayflower leaves": "Bengal dayflower, leaves, raw",
#    "bitter gourd leaves": "Bitter gourd leaves, green, raw",
#    "bottle gourd leaves": "Bottle gourd leaves, raw",
#    "bugleweed": "Bugleweed, raw",
#    "cassava leaves": "Cassava, leaves, raw",
#    "colocasia leaves": "Colocasia leaves, green, raw",
#    "cowpea leaves": "Cowpea, leaves, raw",
#    "dima leaves": "Dima leaves, raw",
#    "drumstick leaves": "Drumstick, leaves, raw",
#    "fern leaves": "Fern, leaves, raw",
#    "fenugreek leaves": "Fenugreek, leaves, raw",
#    "indian spinach": "Indian spinach, boiled* (without salt)",
#    "jute leaves": "Jute leaves, raw",
#    "pumpkin leaves": "Pumpkin leaves, raw",
#    "radish leaves": "Radish leaves, raw",
#    "slender amaranth leaves": "Slender amaranth leaves, boiled* (without salt)",
#    "spinach": "Spinach, boiled* (without salt)",
#    "sweet potato leaves": "Sweet potato leaves, raw",
#    "dark green sweet potato leaves": "Sweet potato leaves, SP4, dark green, mature, raw",
#    "light green sweet potato leaves": "Sweet potato leaves, SP8, light green, mature, raw",
#    "colocasia": "Colocasia/Taro, boiled* (without salt)",
#    "taro": "Colocasia/Taro, boiled* (without salt)",
#    "elephant foot": "Elephant foot, corm, boiled* (without salt)",
#    "giant taro": "Giant taro, corm, boiled* (without salt)",
#    "potato": "Potato, Diamond, boiled* (without salt)",
#    "potato mash": "Potato Mash*",
#    "sweet potato": "Sweet potato, pale-yellow flesh, boiled* (without salt)",
#    "orange sweet potato": "Sweet potato, Komola Sundori, orange flesh, boiled* (without salt)",
#    "pale yellow sweet potato": "Sweet potato, pale-yellow flesh, boiled* (without salt)",
#    "yellow sweet potato": "Sweet potato, pale-yellow flesh, boiled* (without salt)",
#    "purple skin sweet potato": "Sweet potato, skin purple, flesh pale-yellow, boiled* (without salt)",
#    "purple skinned sweet potato": "Sweet potato, skin purple, flesh pale-yellow, boiled* (without salt)",
#    "purple sweet potato": "Sweet potato, skin purple, flesh pale-yellow, boiled* (without salt)",
#    "yam": "Yam, tuber, boiled* (without salt)",
#    "white sweet potato": "Sweet potato, white flesh, boiled* (without salt)",
#    "white skinned sweet potato": "Sweet potato, white flesh, boiled* (without salt)",
#    "cashew": "Cashew nuts, raw",
#    "sunflower seeds": "Sunflower seeds, dried",
#    "cashew nuts": "Cashew nuts, raw",
#    "chilgoza pine": "Chilgoza pine, dried",
#    "coconut milk": "Coconut milk",
#    "coconut": "Coconut, mature kernel",
#    "desiccated coconut": "Coconut, desiccated",
#    "groundnut": "Groundnuts/Peanut, raw",
#    "peanut": "Groundnuts/Peanut, raw",
#    "jackfruit seeds": "Jackfruit seeds, raw",
#    "linseed": "Linseed, raw",
#    "lotus seeds": "Lotus seeds, dried",
#    "green lotus seeds": "Lotus seeds, green",
#    "mustard seeds": "Mustard seeds, dried",
#    "pistachio": "Pistachio nuts, dried",
#    "pumpkin seeds": "Pumpkin seeds, dried",
#    "sesame seeds": "Sesame seeds, whole, dried",
#    "walnuts": "Walnuts",
#    # Spices & Herbs
#    "bay leaf": "Bay leaf, dried",
#    "bay leaves": "Bay leaf, dried",
#    "cardamom": "Cardamom",
#    "chilli": "Chilli, red, dry",
#    "green chilli": "Chilli, green, with seeds, raw",
#    "red chilli": "Chilli, red, dry",
#    "dried chilli": "Chilli, red, dry",
#    "cinnamon": "Cinnamon, ground",
#    "cloves": "Cloves, dried",
#    "coriander leaves": "Coriander leaves, raw",
#    "cilantro": "Coriander leaves, raw",  # Cilantro = Coriander Leaves
#    "coriander seeds": "Coriander seed, dry",
#    "coriander": "Coriander seed, dry",
#    "cumin": "Cumin seeds",
#    "cumin seeds": "Cumin seeds",
#    "fennel": "Fennel seeds",
#    "fennel seeds": "Fennel seeds",
#    "fenugreek": "Fenugreek seeds",
#    "ginger": "Ginger root, raw",
#    "ginger root": "Ginger root, raw",
#    "indian pennywort": "Indian pennywort, raw",
#    "pennywort": "Indian pennywort, raw",
#    "lemon grass": "Lemon grass, raw",
#    "lemon peel": "Lemon peel, raw",
#    "mace": "Mace, ground",
#    "nutmeg": "Nutmeg, dried",
#    "black pepper": "Pepper, black",
#    "pepper": "Pepper, black",
#    "poppy seeds": "Poppy seeds",
#    "spearmint leaves": "Spearmint leaves, fresh",
#    "spearmint": "Spearmint leaves, fresh",
#    "turmeric": "Turmeric, dried",
#    "termaric": "Tumeric, dried",
#    # Fruits
#    "apple": "Apple, with skin, raw",
#    "apple slices": "Apple, with skin, raw",
#    "apple without skin": "Apple, without skin, raw",
#    "asian pears": "Asian pears, raw",
#    "pears": "Asian pears, raw",
#    "banana": "Banana, Sagar, ripe, raw",
#    "breadfruit": "Breadfruit, raw",
#    "bullocks heart": "Bullocks Heart, ripe, raw",
#    "ox heart": "Bullocks Heart, ripe, raw",
#    "carambola": "Carambola, raw",
#    "star fruit": "Carambola, raw",
#    "starfruit": "Carambola, raw",
#    "custard apple": "Custard apple, raw",
#    "dates": "Dates, dried",
#    "raw dates": "Dates, raw",
#    "elephant apple": "Elephant apple, ripe, raw",
#    "emblic": "Emblic, raw",
#    "indian gooseberry": "Emblic, raw",
#    "gooseberry": "Emblic, raw",
#    "amla": "Emblic, raw",
#    "amloki": "Emblic, raw",
#    "fig": "Fig, ripe, raw",
#    "grapes": "Grapes, green, raw",
#    "green grapes": "Grapes, green, raw",
#    "guava": "Guava, green, raw",
#    "hog plum": "Hog plum, raw",
#    "plum": "Hog plum, raw",
#    "jackfruit": "Jackfruit, ripe, raw",
#    # Jambolan and its Variants
#    "jambolan": "Jambolan, raw",
#    "black plum": "Jambolan, raw",
#    "java plum": "Jambolan, raw",
#    "malabar plum": "Jambolan, raw",
#    "jamun": "Jambolan, raw",
#    "jaman": "Jambolan, raw",
#    "jambul": "Jambolan, raw",
#    "jambos": "Jambos, raw",
#    "java apple": "Java apple, raw",
#    "jujube": "Jujube, raw",
#    "jujuba": "Jujube, raw",
#    "lemon": "Lemon, Kagoji, raw",
#    "lime": "Lime, sweet, raw",
#    "lychee": "Lychee, raw",
#    "mango": "Mango, Fazli, orange flesh, ripe, raw",
#    "fazli mango": "Mango, Fazli, orange flesh, ripe, raw",
#    "langra mango": "Mango, Langra, yellow flesh, ripe, raw",
#    "melon": "Melon, Futi, orange flesh, ripe, raw",
#    "monkey-jack": "Monkey-jack, yellowish-orange flesh, raw",
#    "monkey jack": "Monkey-jack, yellowish-orange flesh, raw",
#    "monkey fruit": "Monkey-jack, yellowish-orange flesh, raw",
#    "muskmelon": "Muskmelon, Bangee, light orange flesh, ripe, raw",
#    "juice": "Orange juice, raw (unsweetened)",
#    "orange juice": "Orange juice, raw (unsweetened)",
#    "orange": "Orange, raw",
#    "sweet orange": "Orange, sweet, ripe, raw",
#    "palmyra palm": "Palmyra palm, cotyledon, raw",
#    "palmyra palm pulp": "Palmyra palm, pulp, orange flesh, ripe, raw",
#    "persimmon": "Persimmon, ripe, raw",
#    "pineapple": "Pineapple, ripe, raw",
#    "joldugee pineapple": "Pineapple, Joldugee, ripe, raw",
#    "pomegranate": "Pomegranate, ripe, with seed, raw",
#    "pomelo": "Pomelo, raw",
#    "tamarind": "Tamarind, pulp, ripe, raw",
#    "watermelon": "Watermelon, ripe, raw",
#    "wood apple": "Wood apple, ripe, raw",
#    "egg with potato": "Egg, chicken, farmed, boiled* (without salt); Potato, Diamond, boiled* (without salt)",
#    "egg": "Egg, chicken, farmed, boiled* (without salt)",  # Override raw with boiled
#    "chicken egg": "Egg, chicken, farmed, boiled* (without salt)",
#    "farmed egg": "Egg, chicken, farmed, boiled* (without salt)",
#    "boiled egg": "Egg, chicken, farmed, boiled* (without salt)",
#    "boiled chicken egg": "Egg, chicken, farmed, boiled* (without salt)",
#    # Native Chicken Eggs
#    "native egg": "Egg, chicken, native, boiled* (without salt)",
#    "native chicken egg": "Egg, chicken, native, boiled* (without salt)",
#    "native boiled egg": "Egg, chicken, native, boiled* (without salt)",
#    "native raw egg": "Egg, chicken, native, raw",
#    "egg yolk": "Egg, chicken, native, yolk, raw",
#    # Duck Eggs
#    "duck egg": "Egg, duck, whole, boiled* (without salt)",
#    "boiled duck egg": "Egg, duck, whole, boiled* (without salt)",
#    # Butter & Ghee
#    "butter": "Butter, salted",
#    "salted butter": "Butter, salted",
#    "ghee": "Ghee, cow",  # Default to cow ghee unless specified
#    "cow ghee": "Ghee, cow",
#    "vegetable ghee": "Ghee, vegetable",
#    # Oils
#    "oil": "Soybean oil",
#    "mustard oil": "Mustard oil",
#    "palm oil": "Palm oil",
#    "peanut oil": "Peanut oil",
#    "groundnut oil": "Peanut oil",  # Alternative name
#    "sesame oil": "Sesame oil",
#    "soybean oil": "Soybean oil",
#    "cottonseed oil": "Cottonseed oil",
#    "fish oil": "Fish oil, cod liver",
#    "cod liver oil": "Fish oil, cod liver",
#    # Margarine & Mayonnaise
#    "margarine": "Margarine",
#    "mayonnaise": "Mayonnaise, salted",
#    "salted mayonnaise": "Mayonnaise, salted",
#    # Beverages and Drinks
#    "coconut water": "Coconut water",
#    "coffee": "Coffee infusion (instant with sugar and milk powder, whole fat)",
#    "instant coffee": "Coffee infusion (instant with sugar and milk powder, whole fat)",
#    "coffee powder": "Coffee, powder",
#    "soft drink": "Soft drinks, carbonated",
#    "soda": "Soft drinks, carbonated",
#    "carbonated drink": "Soft drinks, carbonated",
#    "soy milk": "Soya milk (not sweetened)",
#    "soya milk": "Soya milk (not sweetened)",
#    "sugarcane juice": "Sugar cane Juice",
#    "tea": "Tea infusion (with sugar and milk powder, whole fat)",
#    "sweet tea": "Tea, infusion (with sugar)",
#    "tea powder": "Tea, powder",
#    "drinking water": "Water, drinking",
#    "water": "Water, drinking",
#    # Common Carbonated Drinks
#    "cola": "Soft drinks, carbonated",
#    "coke": "Soft drinks, carbonated",
#    "pepsi": "Soft drinks, carbonated",
#    "sprite": "Soft drinks, carbonated",
#    "7up": "Soft drinks, carbonated",
#    "fanta": "Soft drinks, carbonated",
#    "mountain dew": "Soft drinks, carbonated",
#    "dr pepper": "Soft drinks, carbonated",
#    "root beer": "Soft drinks, carbonated",
#    "ginger ale": "Soft drinks, carbonated",
#    "club soda": "Soft drinks, carbonated",
#    "tonic water": "Soft drinks, carbonated",
#    "seltzer": "Soft drinks, carbonated",
#    "sparkling water": "Soft drinks, carbonated",
#    "energy drink": "Soft drinks, carbonated",
#    "red bull": "Soft drinks, carbonated",
#    "monster": "Soft drinks, carbonated",
#    "mug root beer": "Soft drinks, carbonated"
#}
#def preprocess_text(text):
#    """Removes numbers, units, and extra words inside parentheses."""
#    text = text.lower()  # Convert to lowercase
#    text = re.sub(r"\(.*?\)", "", text)  # Remove content inside parentheses
#    text = re.sub(r"\b\d+(\.\d+)?\b", "", text)  # Remove standalone numbers
#    text = re.sub(r"\bpcs\b|\bbowl\b|\bglass\b|\bplate\b", "", text)  # Remove size units
#    return text.strip()
#
#def clean_food_entry(original_entry):
#    if pd.isna(original_entry):
#        return None  # Skip empty entries
#    
#    original_entry = preprocess_text(original_entry)  # Preprocess input
#    food_items = original_entry.split(",")  # Split by commas
#    cleaned_items = []
#    
#    for item in food_items:
#        item = item.strip()
#        matched = food_mappings.get(item, f"UNKNOWN: {item}")  # Lookup in food_mappings
#        cleaned_items.append(matched)
#    
#    return "; ".join(cleaned_items)
#
## Apply the function to clean the dataset
#df_cleaned = df_dummy.copy()
#df_cleaned["Description of the food_ CLEAN"] = df_cleaned["Description of the food_ORIGINAL"].apply(clean_food_entry)
#
## Save the cleaned dataset
#df_cleaned.to_excel("Cleaned_Food_Diary.xlsx", index=False)
#print("Cleaning complete. Cleaned data saved as 'Cleaned_Food_Diary.xlsx'")







# Function to clean food entries using only `food_mappings`
# def clean_food_entry(original_entry):
#     if pd.isna(original_entry):
#         return None  # Skip empty entries
    
#     original_entry_lower = original_entry.lower()  # Convert to lowercase
#     food_items = original_entry_lower.split(",")  # Split by commas
#     cleaned_items = []
    
#     for item in food_items:
#         item = item.strip()  # Remove extra spaces
#         matched = food_mappings.get(item, f"UNKNOWN: {item}")  # Lookup in food_mappings

#         cleaned_items.append(matched)
    
#     return "; ".join(cleaned_items)  # Join cleaned food items with semicolons

# # Apply the function to clean the dataset
# df_cleaned = df_dummy.copy()
# df_cleaned["Description of the food_ CLEAN"] = df_cleaned["Description of the food_ORIGINAL"].apply(clean_food_entry)

# # Save the cleaned dataset
# df_cleaned.to_excel("Cleaned_Food_Diary.xlsx", index=False)
# print("Cleaning complete. Cleaned data saved as 'Cleaned_Food_Diary.xlsx'")












# # Function to clean food entries
# def clean_food_entry(original_entry):
#     if pd.isna(original_entry):
#         return None  # Skip empty entries
#     original_entry_lower = original_entry.lower()  # Convert to lowercase
#     food_items = original_entry_lower.split(",")  # Split by commas
#     cleaned_items = []
    
#     for item in food_items:
#         item = item.strip()  # Remove extra spaces
#         matched = None
#         # Try direct match with the food composition table
#         for food in df_food_composition["Food_Item"]:
#             if food.lower() in item:
#                 matched = food
#                 break
#         # Try extended predefined mappings
#         if not matched:
#             for keyword, mapped_food in food_mappings.items():
#                 if keyword in item:
#                     matched = mapped_food
#                     break
#         # If still unmatched, flag it
#         if not matched:
#             matched = f"UNKNOWN: {item}"
#         cleaned_items.append(matched)
#     return "; ".join(cleaned_items)  # Join cleaned food items with semicolons
# # Apply the function to clean the dataset
# df_cleaned = df_dummy.copy()
# df_cleaned["Description of the food_ CLEAN"] = df_cleaned["Description of the food_ORIGINAL"].apply(clean_food_entry)
# # Save the cleaned dataset to an Excel file
# df_cleaned.to_excel("Cleaned_Food_Diary.xlsx", index=False)
# print("Cleaning complete. Cleaned data saved as 'Cleaned_Food_Diary.xlsx'")

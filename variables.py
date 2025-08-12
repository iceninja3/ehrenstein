# cleaning_config.py

# Weight distribution for protein vs non-protein
PROTEIN_WEIGHT_RATIO = 0.35
NON_PROTEIN_WEIGHT_RATIO = 0.65

# Default weight for unknown quantities
DEFAULT_TOTAL_WEIGHT = 300

# Weights for special categories
DEFAULT_OIL_WEIGHT = 15
DEFAULT_GARNISH_WEIGHT = 10

# Fuzzy matching threshold
FUZZY_MATCH_THRESHOLD = 85

#this is at least the number of items that must be in a dish's () for it to not use the default version 
NUM_ITEMS_NECESSARY_TO_EXPAND = 2

#name of file in which the data shall be processed 
FILE_NAME = "/Users/riverngo/Library/CloudStorage/Box-Box/Bangladesh Nutrition Data Cleaning 2025/Diet_data_real.xlsx"
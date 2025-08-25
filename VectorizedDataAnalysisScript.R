# Title: Bangladesh diet data analysis
# Author: Sophie Michel
# Date: August 22, 2025
# Notes: CONFIDENTIAL- DO NOT DISTRIBUTE- Project in progress

# Clean memory and load libraries
rm(list = ls())
library(dplyr)
library(tidyr)
library(readr)
library(readxl)

### =========================================================================
### Step 1: Consolidate Food Composition Tables into a Single Master Table
### =========================================================================
# This replaces looping through a list of 104 files for every lookup.
# A single table allows for a highly efficient, one-time join operation.

setwd("/Users/vishal/Library/CloudStorage/Box-Box/Bangladesh Nutrition Data Cleaning 2025/AllTables")

food_comp_master <- list.files(pattern = "*.csv") %>%
  # Read all CSVs, forcing columns to character to prevent parsing errors on mixed types.
  lapply(read_csv, col_types = cols(.default = "c")) %>%
  bind_rows() %>%
  mutate(
    # Clean up food names by removing newline characters.
    `Food name in English` = gsub("[\n]", " ", `Food name in English`),
    # Convert all columns that are NOT the food name to numeric.
    across(where(is.character) & !matches("Food name"), ~as.numeric(.))
  )

### =========================================================================
### Step 2: Load and Tidy the Food Diary Data
### =========================================================================
# This section transforms the diary from a "wide" format (many columns)
# to a "tidy" long format (one row per observation), which is ideal for analysis.

setwd("/Users/vishal/Desktop/ehrenstein")
FD <- read_excel("Cleaned_Bangladesh_Food_Diary.xlsx")

tidy_diary <- FD %>%
  fill(Study_ID) %>%
  # Pivot from wide to long, robustly selecting all day columns.
  pivot_longer(
    cols = starts_with("Description of the food."), # Robustly selects all day columns.
    names_to = "Day",
    values_to = "Food_Entry",
    names_pattern = "Description of the food.(\\d+)_CLEAN", # Extracts day number.
    values_drop_na = TRUE
  ) %>%
  # Split semicolon-separated foods (e.g., "Rice {1.5}; Lentils {2}") into separate rows.
  separate_rows(Food_Entry, sep = ";") %>%
  mutate(Food_Entry = trimws(Food_Entry)) %>%
  filter(nzchar(Food_Entry)) %>%
  # Extract the food name and the number of 100g servings from the string.
  extract(
    Food_Entry,
    into = c("Food_Name_Clean", "Servings_100g"),
    regex = "^(.*)\\{([0-9.]+)\\}$",
    convert = TRUE # Automatically convert servings to a numeric type.
  ) %>%
  mutate(Food_Name_Clean = trimws(Food_Name_Clean))

### =========================================================================
### Step 3: Define Nutrients and Pivot the Food Composition Table
### =========================================================================
# A long food composition table is needed for an efficient join.

all_nutrients <- c("Energy (kcal) kJ", "Water (g)", "Protein (g)", "Fat (g)", "Carbohydrate available (g)",
                   "Total dietary fibre (g)", "Ash (g)", "Ca (mg)", "Fe (mg)", "Mg (mg)", "P (mg)", "K (mg)",
                   "Na (mg)", "Zn (mg)", "Cu (mg)", "Vitamin A (mcg)", "Retinol (mcg)",
                   "Beta-carotene equivalents (mcg)", "Vitamin D (mcg)", "Vitamin E (mg)", "Thiamin (mg)",
                   "Riboflavin (mg)", "Niacin equivalents (mg)", "Vitamin B6 (mg)", "Folate (mcg)", "Vitamin C (mg)")

food_comp_long <- food_comp_master %>%
  pivot_longer(
    cols = all_of(all_nutrients),
    names_to = "Nutrient",
    values_to = "Value_per_100g"
  )

### =========================================================================
### Step 4: Join Diary with Composition Table & Calculate Nutrient Intake
### =========================================================================
# This is the core of the analysis, replacing all the original loops.

intake_data <- tidy_diary %>%
  left_join(
    food_comp_long,
    by = c("Food_Name_Clean" = "Food name in English")
  ) %>%
  # CORRECTED CALCULATION: (Value per 100g) * (Number of 100g servings).
  mutate(Nutrient_Intake = Value_per_100g * Servings_100g) %>%
  # LOGIC REPLICATION: Instead of filtering out unmatched foods, we replace their
  # NA intake with 0. This perfectly replicates your original for-loop's logic.
  mutate(Nutrient_Intake = replace_na(Nutrient_Intake, 0))

### =========================================================================
### Step 5: Calculate Per-Child Averages
### =========================================================================
# First, find the number of unique days with data for each child to use as the denominator.
days_per_child <- tidy_diary %>%
  distinct(Study_ID, Day) %>%
  count(Study_ID, name = "Days_With_Data")

# Now, aggregate the total intake and calculate the average.
child_results <- intake_data %>%
  group_by(Study_ID, Nutrient) %>%
  summarise(TotalIntake = sum(Nutrient_Intake, na.rm = TRUE), .groups = 'drop') %>%
  left_join(days_per_child, by = "Study_ID") %>%
  mutate(AvgIntakePerDay = TotalIntake / Days_With_Data)

### =========================================================================
### Step 6: Calculate Nutrient Deficiency Percentages
### =========================================================================
# Store thresholds in a data frame for easy joining.
nutrient_thresholds <- c(
  "Energy (kcal) kJ" = 1300, "Water (g)" = 1600, "Protein (g)" = 19, "Fat (g)" = 44,
  "Carbohydrate available (g)" = 130, "Total dietary fibre (g)" = 25, "Ash (g)" = 49,
  "Ca (mg)" = 1000, "Fe (mg)" = 10, "Mg (mg)" = 100, "P (mg)" = 500, "K (mg)" = 3800,
  "Na (mg)" = 1200, "Zn (mg)" = 5, "Cu (mg)" = 0.44, "Vitamin A (mcg)" = 400,
  "Retinol (mcg)" = 300, "Beta-carotene equivalents (mcg)" = 1200, "Vitamin D (mcg)" = 15,
  "Vitamin E (mg)" = 7, "Thiamin (mg)" = 0.6, "Riboflavin (mg)" = 0.6,
  "Niacin equivalents (mg)" = 8, "Vitamin B6 (mg)" = 0.6, "Folate (mcg)" = 200,
  "Vitamin C (mg)" = 25
)
threshold_df <- data.frame(
  Nutrient = names(nutrient_thresholds),
  Threshold = nutrient_thresholds
)

# Calculate deficiencies using joins and group_by, which is much faster than a loop.
deficiency_results <- child_results %>%
  left_join(threshold_df, by = "Nutrient") %>%
  filter(!is.na(Threshold)) %>% # Only consider nutrients with a defined threshold
  group_by(Nutrient) %>%
  summarise(
    Total_Children = n(),
    Deficient_Count = sum(AvgIntakePerDay < Threshold, na.rm = TRUE),
    .groups = 'drop'
  ) %>%
  mutate(PercentDeficient = (Deficient_Count / Total_Children) * 100)

### =========================================================================
### Step 7: View Final Results
### =========================================================================
View(child_results)
View(deficiency_results)


# Title: Bangladesh diet data analysis (Optimized Version)
# Date: June 24, 2025
# Author: Sophie Michel
# Notes: CONFIDENTIAL- DO NOT DISTRIBUTE- Project in progress

### --- Setup: Load Libraries and Clean Environment ---
# It's good practice to clear the environment to avoid conflicts.
rm(list = ls())

# Load necessary packages.
library(hash)
library(readr)
library(readxl)
library(dplyr)
library(tidyr)

### --- Section 1: Load and Consolidate Food Composition Data ---
# This section has been optimized to load all 104 tables into one
# master data frame for fast, "hash-map-like" lookups.

# Set your working directory to where the CSV files are.
setwd("/Users/vishal/Library/CloudStorage/Box-Box/Bangladesh Nutrition Data Cleaning 2025/AllTables")

# Get a list of all CSV files in the directory.
csv_files <- list.files(pattern = "\\.csv$", full.names = TRUE)

# Read all CSV files and combine them into a single data frame using bind_rows().
# This is much faster than loading them into a list one-by-one.
food_composition_table <- bind_rows(lapply(csv_files, read_csv))

# --- CRITICAL OPTIMIZATION: Clean and pre-process the data ONCE ---
# This avoids running cleaning functions (like gsub) inside every lookup.
# It also removes duplicate food entries, which could cause unpredictable results.
food_composition_table <- food_composition_table %>%
  mutate(`Food name in English` = gsub("[\n]", " ", `Food name in English`)) %>%
  distinct(`Food name in English`, .keep_all = TRUE)

# You can save this combined table to reuse it later without reloading all 104 files.
# saveRDS(food_composition_table, "combined_food_table.rds")
# To load it back: food_composition_table <- readRDS("combined_food_table.rds")


### --- Section 2: Optimized Data Retrieval Function ---

# This new getData function is much faster. It operates on the single,
# combined 'food_composition_table' instead of looping through 104 separate tables.
getData <- function(foodName, columnName) {
  # Directly filter the main table and pull the desired value.
  # This is highly optimized and replaces the entire original for-loop and tryCatch block.
  value <- food_composition_table %>%
    filter(`Food name in English` == foodName) %>%
    pull(all_of(columnName))

  # If the food or column isn't found, pull() returns an empty vector.
  # Return NA instead of letting errors occur.
  if (length(value) > 0) {
    return(value)
  } else {
    return(NA_real_) # Return a numeric NA for consistency.
  }
}

# Example lookups using the new, fast function:
print(getData("Wheat, flour, white","Energy (kcal) kJ"))
print(getData("Rice, BR-28, boiled* (without salt)","Vitamin E (mg)" ))


### --- Section 3: Define Nutrient Lists ---

# Lists of Nutrients for analysis
Macronutrients <- list("Energy (kcal) kJ", "Water (g)", "Protein (g)", "Fat (g)", "Carbohydrate available (g)",
                       "Total dietary fibre (g)")

Micronutrients <- list("Ash (g)", "Ca (mg)", "Fe (mg)", "Mg (mg)", "P (mg)", "K (mg)", "Na (mg)", "Zn (mg)", "Cu (mg)",
                       "Vitamin A (mcg)", "Retinol (mcg)", "Beta-carotene equivalents (mcg)", "Vitamin D (mcg)",
                       "Vitamin E (mg)", "Thiamin (mg)", "Riboflavin (mg)", "Niacin equivalents (mg)",
                       "Vitamin B6 (mg)", "Folate (mcg)", "Vitamin C (mg)")

Nutrients <- list(Macronutrients, Micronutrients)
all_nutrients <- unlist(Nutrients)


### --- Section 4: Load and Prepare Food Diary Data ---

# Set working directory to the food diary location.
setwd("/Users/vishal/Desktop/ehrenstein")

FD <- read_excel("Cleaned_Bangladesh_Food_Diary.xlsx")

# Prepare the diary by ensuring Study_ID is numeric and filled down for all rows.
FD_1 <- FD %>%
  mutate(Study_ID = as.numeric(Study_ID)) %>%
  fill(Study_ID)


### --- Section 5: Helper Functions for Diary Processing ---

# Helper to extract weight from a diary entry string like "Rice {100}".
extract_weight <- function(item) {
  if (is.na(item)) return(NA_real_)
  # Suppress warnings for items with no weight, which will correctly become NA.
  weight <- suppressWarnings(as.numeric(sub(".*\\{(.*)\\}", "\\1", item)))
  return(weight)
}

# Helper to get the nutrient value for a single food and weight.
get_food_nutrient_value <- function(foodName, nutrient, weight) {
  # Call our new, super-fast getData function.
  val <- getData(foodName, nutrient)
  
  # Check for valid numeric values before multiplying.
  if (is.na(val) || is.na(weight)) {
    return(0)
  }
  
  return(as.numeric(val) * weight)
}


### --- Section 6: Main Calculation Function ---

# Function to compute total and average intake for one child.
getChildNutrientTotal <- function(child_id, nutrient) {
  child_data <- FD_1 %>% filter(Study_ID == child_id)
  diary_columns <- grep("Description of the food.\\d+_CLEAN", names(child_data), value = TRUE)
  
  total <- 0
  days_with_data <- 0
  
  for (col in diary_columns) {
    column_data <- child_data[[col]]
    
    # If any food was recorded on this day, count it as a day of data.
    if (any(nzchar(column_data) & !is.na(column_data))) {
      days_with_data <- days_with_data + 1
    }
    
    for (entry in column_data) {
      if(is.na(entry)) next # Skip if the entry is NA
      
      # Split entries like "Rice {100}; Dal {50}" into individual items.
      items <- unlist(strsplit(entry, ";"))
      
      for (item in trimws(items)) {
        if (nzchar(item)) {
          # Extract food name and weight.
          food <- trimws(sub("\\{.*\\}", "", item))
          weight <- extract_weight(item)
          
          # Calculate and add to total.
          total <- total + get_food_nutrient_value(food, nutrient, weight)
        }
      }
    }
  }
  
  # Calculate average, avoiding division by zero.
  avg <- if (days_with_data > 0) total / days_with_data else NA_real_
  
  return(list(total = total, avg = avg))
}

# Example test for a single child:
print(getChildNutrientTotal(3, "Ca (mg)"))


### --- Section 7: Build Final Results Data Frame (Optimized) ---

# Get a unique, non-NA list of all children IDs.
all_children <- unique(FD_1$Study_ID)
all_children <- all_children[!is.na(all_children)]

# --- OPTIMIZATION: Avoid using rbind() in a loop ---
# Instead, we will add results to a list and combine them all at the end.
# This is significantly more efficient.

# 1. Initialize an empty list to store results.
results_list <- list()

# 2. Loop through each child and nutrient, appending results to the list.
for (child in all_children) {
  for (nutrient in all_nutrients) {
    res <- getChildNutrientTotal(child, nutrient)
    
    # Append a new data frame to the list. This is a fast operation.
    results_list[[length(results_list) + 1]] <- data.frame(
      Study_ID = child,
      Nutrient = nutrient,
      TotalIntake = res$total,
      AvgIntakePerDay = res$avg
    )
  }
  # Optional: Print progress
  print(paste("Processed child:", child))
}

# 3. Combine the list of data frames into one final table. This is very fast!
child_results_final <- bind_rows(results_list)

# View the final, complete results.
View(child_results_final)
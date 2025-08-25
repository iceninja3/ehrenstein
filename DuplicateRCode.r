
rm() # good practice to clean memory
rm(list = ls())
library(hash) # use "install.packages("package name") first, as needed
library(readr)
library(readxl)
library(dplyr)
library(tidyr)


#Load food comp table
setwd("~/Desktop/AllTables")
table <- vector(mode='list')
temp = list.files(pattern="*.csv")
for(i in 1:104) {
  table[[i]] <- read_csv(temp[i])
  #print(i)
}
#View(table[[1]])


#gets the data for particular value and column.
getData <- function(foodName, columnName){
  for(i in table) {
    tryCatch(expr = {
      i$"Food name in English" <-gsub("[\n]"," ", i$"Food name in English")
      value <- ((i[which(i$"Food name in English" == foodName ),][columnName])[[1]])
      if(length(value)>0){
        return (value)}},
      error=function(e){
      })
  }
}

#print(getData("Rice flaked","Protein (g)" ))
#print(getData("Rice, BR-28, boiled* (without salt)","Vitamin A (mcg)" ))
#print(getData("Wheat, flour, white","Protein (g)" ))
#print(getData("Wheat, flour, white","Water (g)" ))
#

print(getData("Wheat, flour, white","Energy (kcal) kJ"))

print(getData("Rice, BR-28, boiled* (without salt)","Vitamin E (mg)" ))
#Lists of Nutrients:
Macronutrients <- list("Energy (kcal) kJ", "Water (g)", "Protein (g)", "Fat (g)", "Carbohydrate available (g)",
               "Total dietary fibre (g)")
               
Micronutrients <- list("Ash (g)", "Ca (mg)", "Fe (mg)", "Mg (mg)", "P (mg)", "K (mg)", "Na (mg)", "Zn (mg)", "Cu (mg)",
                    "Vitamin A (mcg)", "Retinol (mcg)", "Beta-carotene equivalents (mcg)", "Vitamin D (mcg)",
                    "Vitamin E (mg)", "Thiamin (mg)", "Riboflavin (mg)", "Niacin equivalents (mg)",
                    "Vitamin B6 (mg)", "Folate (mcg)", "Vitamin C (mg)")
Nutrients <- list(Macronutrients, Micronutrients)

#Make a for loop and print the items in the list 
#for (i in Nutrients) {
 # for (j in i)
  #  print (j)
#}

#Get list of nutrients for specific items
#for (i in (Macronutrients)) {
#  print(getData("Orange juice, raw (unsweetened)", (i)))
#}

#for (i in (Micronutrients)) {
#  print(getData("Rice flaked", (i)))
#}

#for (i in Nutrients) {
#  for (j in i)
#    print(getData("Rice flaked", (j)))
#}

#Get the diary entries
setwd("~/Desktop/DummyData")
FD <- read_excel("Cleaned_Bangladesh_Food_Diary.xlsx")
#FD<- read_excel("C:/Users/Michel/Box/Bangladesh analyses/DummyData_2025.xlsx", skip = 1)
#View(FD)
#Get list of all foods eaten by all subjects on particular day
FD_1 <- FD %>%
  mutate(Study_ID = as.numeric(Study_ID)) %>%  # ensure numeric or NA
  fill(Study_ID)  # fill down the last known Study_ID

Day1_all <- FD_1 %>% filter(Study_ID == 108021) %>%
  pull("Description of the food_1_Clean")
Day1_all

#####################
#Function that integrates:
#1) looking up nutrition information for any food item in specified amount
#2) looking up nutrition information for food diary data

getDiaryEntryNutrientData <- function(foodName, nutrient,
                                      amount = NULL,
                                      child = NULL,
                                      day = NULL,
                                      meal = NULL) {
  # Direct lookup (no diary data used)
  if (!is.null(amount) && is.null(child) && is.null(day) && is.null(meal)) {
    val <- getData(foodName, nutrient)
    return(if (!is.null(val) && !is.na(val)) as.numeric(val) * amount else NA)
  }
  
  data <- FD_1
  if (!is.null(child)) data <- filter(data, Study_ID == child)
  if (!is.null(meal)) data <- slice(data, meal)
  
  day_cols <- if (!is.null(day)) {
    paste0("Description of the food_", day, "_Clean")
  } else {
    grep("Description of the food_\\d+_Clean", names(data), value = TRUE)
  }
  
  total <- 0
  for (i in seq_len(nrow(data))) {
    for (col in day_cols) {
      items <- unlist(strsplit(data[[col]][i], ";"))
      for (item in trimws(items)) {
        if (nzchar(item) && grepl(foodName, item, fixed = TRUE)) {
          food <- trimws(sub("\\{.*\\}", "", item))
          w <- if (!is.null(amount)) amount else as.numeric(sub(".*\\{(.*)\\}", "\\1", item))
          val <- getData(food, nutrient)
          if (!is.null(val) && !is.na(val)) total <- total + as.numeric(val) * w
        }
      }
    }
  }
  total
}


# ---- Helper: Extract food names from diary string ----

#Extract all food names from a cleaned diary entry line 
extract_food_names <- function(entry) {
  if (is.na(entry)) return(character(0))
  items <- unlist(strsplit(entry, ";"))
  foods <- trimws(sub("\\{.*\\}", "", items))
  return(foods)
}

# --- Helper: Extract weight ---
extract_weight <- function(item) {
  if (is.na(item)) return(NA_real_)
  weight <- as.numeric(sub(".*\\{(.*)\\}", "\\1", item))
  return(weight)
}

# --- Helper: Get nutrient value for a single food and weight ---
get_food_nutrient_value <- function(foodName, nutrient, weight, child_id = NULL) {
  val <- getData(foodName, nutrient)
  
  # Make sure val is a valid coercible scalar
  if (is.null(val) || length(val) != 1 || is.na(val)) return(0)
  
  val_num <-(as.numeric(val))
  
  # FINAL CHECK to prevent crash
  if (!is.na(val_num) && !is.na(weight)) {
    return(val_num * weight)
  }
  
  return(0)
}




# --- Compute total and average intake for one child ---
getChildNutrientTotal <- function(child_id, nutrient) {
  child_data <- FD_1 %>% filter(Study_ID == child_id)
  diary_columns <- grep("Description of the food_\\d+_Clean", names(child_data), value = TRUE)
  #filter to the specific child ID, then filter out to only the columns with the clean data 
  #Diary columns is the description of the food clean columns for a particular child 
  total <- 0
  days_with_data <- 0
  
  for (col in diary_columns) {
    #for each column of containing the clean data, so long as one of each of their rows
    #contains valid food data, that counts as a day of food 
    column_data <- child_data[[col]]
    #column_data is now a specific column/day filled with the specified child's data  
    if (any(nzchar(column_data) & !is.na(column_data))) {
      days_with_data <- days_with_data + 1
    }
    
    for (i in seq_along(column_data)) {
      #iterate through column_data (one days worth of food) one row at a time  
      #seq_along generates a seqeuence of indices for column_data
      items <- unlist(strsplit(column_data[i], ";"))
      #column_data[i] contains a single semicolon-separated string of food items
      for (item in trimws(items)) {
        #for each food item, extract its name, weight, and then get the info for the desired nutrient 
        if (nzchar(item)) {
          food <- trimws(sub("\\{.*\\}", "", item))
          weight <- extract_weight(item)
          total <- total + get_food_nutrient_value(food, nutrient, weight)
        }
      }
    }
  }
  
  avg <- if (days_with_data > 0) total / days_with_data else NA_real_
  return(list(total = total, avg = avg))
}


getChildNutrientTotal(3, "Ca (mg)")

# --- Build results data frame ---
all_children <- unique(FD_1$Study_ID)
all_children <- all_children[!is.na(all_children)]
all_nutrients <- unlist(Nutrients)




child_results <- data.frame(Study_ID = numeric(),
                            Nutrient = character(),
                            TotalIntake = numeric(),
                            AvgIntakePerDay = numeric(),
                            stringsAsFactors = FALSE)

for (child in all_children) {
  for (nutrient in all_nutrients) {
    res <- getChildNutrientTotal(child, nutrient)
    
    # Always append row, even if total is 0
    child_results <- rbind(child_results, data.frame(
      Study_ID = child,
      Nutrient = nutrient,
      TotalIntake = res$total,
      AvgIntakePerDay = res$avg,
      stringsAsFactors = FALSE
    ))
  }
}
View(child_results)

# Define thresholds
nutrient_thresholds <- list(
  "Energy (kcal) kJ" = 1300,
  "Water (g)" = 1600,
  "Protein (g)" = 19,
  "Fat (g)" = 44,
  "Carbohydrate available (g)" = 130,
  "Total dietary fibre (g)" = 25,
  "Ash (g)" = 49,
  "Ca (mg)" = 1000,
  "Fe (mg)" = 10,
  "Mg (mg)" = 100,
  "P (mg)" = 500,
  "K (mg)" = 3800,
  "Na (mg)" = 1200,
  "Zn (mg)" = 5,
  "Cu (mg)" = 0.44,
  "Vitamin A (mcg)" = 400,
  "Retinol (mcg)" = 300,
  "Beta-carotene equivalents (mcg)" = 1200,
  "Vitamin D (mcg)" = 15,
  "Vitamin E (mg)" = 7,
  "Thiamin (mg)" = 0.6,
  "Riboflavin (mg)" = 0.6,
  "Niacin equivalents (mg)" = 8,
  "Vitamin B6 (mg)" = 0.6,
  "Folate (mcg)" = 200,
  "Vitamin C (mg)" = 25
)


#Step 1: Define thresholds


# --- Step 2: Initialize results ---
deficiency_results <- data.frame(
  Nutrient = character(),
  PercentDeficient = numeric(),
  stringsAsFactors = FALSE
)

# --- Step 3: Calculate from child_results table ---
for (nutrient in names(nutrient_thresholds)) {
  #for each of the nutrients in our defined thresholds 
  threshold <- nutrient_thresholds[[nutrient]]
  #extracts from the table the numeric threshold the nutrient corresponds to 
  
  #becomes a smaller data frame that contains only the entires for the current nutrient 
  
  nutrient_data <- subset(child_results, Nutrient == nutrient)
  
  # Count how many children fall below the threshold
  deficient_count <- sum(!is.na(nutrient_data$AvgIntakePerDay) & nutrient_data$AvgIntakePerDay < threshold)
  #accesses the AvgIntakePerDay column in the nutrient_data data frame 
  #!is.na makes sure we only consider children who actually have data 
  #nutrient_data$AvgIntakePerDay < threshold compares each child's average daily intake 
  #for one specific nutrient and makes a true/false logical vector 
  
  
  total_count <- sum(!is.na(nutrient_data$AvgIntakePerDay))
  #sums all the AvgIntakePerDay nutrients that have data amd caculates the percent 
  percent <- (deficient_count / total_count) * 100
  #calculates percent using total 
  deficiency_results <- rbind(deficiency_results, data.frame(
    Nutrient = nutrient,
    PercentDeficient = percent
  ))
}

View(deficiency_results)

# only need to fix things until here

# # Step 1: Get all foods ever mentioned in the food diaries
# library(stringr)

# # Extract food names from all diary columns
# diary_columns <- grep("Description of the food_\\d+_Clean", names(FD_1), value = TRUE)
# diary_text <- unlist(FD_1[diary_columns])

# # Extract food names from strings like "Rice {1.5}; Lentils {2}"
# extract_food_names <- function(entry) {
#   items <- unlist(strsplit(entry, ";"))
#   foods <- trimws(sub("\\{.*\\}", "", items))
#   return(foods)
# }

# # Get all unique cleaned food names
# all_diary_foods <- unique(unlist(lapply(diary_text, extract_food_names)))
# all_diary_foods <- all_diary_foods[!is.na(all_diary_foods) & nzchar(all_diary_foods)]


# all_nutrients <- unlist(Nutrients)

# #Initialize result storage
# results <- data.frame(Food = character(),
#                       Nutrient = character(),
#                       Total = numeric(),
#                       stringsAsFactors = FALSE)

# #Loop and compute
# for (food in all_diary_foods) {
#   for (nutrient in all_nutrients) {
#     val <- getDiaryEntryNutrientData(food, nutrient)
#     if (!is.null(val) && !is.na(val)) {
#       results <- rbind(results, data.frame(Food = food, Nutrient = nutrient, Total = val, stringsAsFactors = FALSE))
#     }
#   }
# }

# # View results
# head(results)












# #Look up a food directly (not from diary), per specified amount, e.g., 100 grams = 1
# getDiaryEntryNutrientData("Rice, BR-28, boiled* (without salt)", "Protein (g)", amount = 1)

# #Total across entire dataset (all kids, all days, all meals) - we should also alter the function to consider all food items, not just one
# #Also note that right now we only have data for day 1, but can add cleaned data
# #for other days and check if this works
# getDiaryEntryNutrientData("Rice, BR-28, boiled* (without salt)", "Protein (g)")

# #For child 108021, Day 1, Meal 3
# getDiaryEntryNutrientData("Rice, BR-28, boiled* (without salt)", "Protein (g)", child = 108021, day = 1, meal = 3)

# #Intake for one day (Day 1), all children
# getDiaryEntryNutrientData("Rice, BR-28, boiled* (without salt)", "Protein (g)", day = 1)

# #Total intake of one food for child 108021, across all days - note that we only have clean data for day 1, but one can add cleaned data
# #for other days and check if this works
# getDiaryEntryNutrientData("Rice, BR-28, boiled* (without salt)", "Protein (g)", child = 108021)





# #not functional? 





#Title: Bangladesh diet data analysis
#Date: June 24, 2025
#Author: Sophie Michel
#Notes: CONFIDENTIAL- DO NOT DISTRIBUTE- Project in progress 



rm() 

rm(list = ls())

library(hash) 
library(readr)
library(readxl)
library(dplyr)
library(tidyr)



# setwd("/Users/vishal/Library/CloudStorage/Box-Box/Bangladesh Nutrition Data Cleaning 2025/AllTables2")
setwd("/Users/vishal/Library/CloudStorage/Box-Box/Bangladesh Nutrition Data Cleaning 2025/FinalTable")

table <- vector(mode='list')

temp = list.files(pattern="*.csv")

for(i in 1:1) {
  
  table[[i]] <- read_csv(temp[i])
  
  
}


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





print(getData("Wheat, flour, white","Energy (kcal) kJ"))



print(getData("Rice, BR-28, boiled* (without salt)","Vitamin E (mg)" ))



Macronutrients <- list("Energy (kcal)", "Water (g)", "Protein (g)", "Fat (g)", "Carbohydrate available (g)",
                       
                       "Total dietary fibre (g)")



Micronutrients <- list("Ash (g)", "Ca (mg)", "Fe (mg)", "Mg (mg)", "P (mg)", "K (mg)", "Na (mg)", "Zn (mg)", "Cu (mg)",
                       
                       "Vitamin A (mcg)", "Retinol (mcg)", "Beta-carotene equivalents (mcg)", "Vitamin D (mcg)",
                       
                       "Vitamin E (mg)", "Thiamin (mg)", "Riboflavin (mg)", "Niacin equivalents (mg)",
                       
                       "Vitamin B6 (mg)", "Folate (mcg)", "Vitamin C (mg)")

Nutrients <- list(Macronutrients, Micronutrients)






setwd("/Users/vishal/Desktop/ehrenstein")

FD <- read_excel("Cleaned_Bangladesh_Food_Diary.xlsx")



FD_1 <- FD %>%
  
  mutate(Study_ID = as.numeric(Study_ID)) %>% # ensure numeric or NA
  
  fill(Study_ID) # fill down the last known Study_ID



Day1_all <- FD_1 %>% filter(Study_ID == 108021) %>%
  
  pull("Description of the food.1_CLEAN")

Day1_all





getDiaryEntryNutrientData <- function(foodName, nutrient,
                                      
                                      amount = NULL,
                                      
                                      child = NULL,
                                      
                                      day = NULL,
                                      
                                      meal = NULL) {
  

  
  if (!is.null(amount) && is.null(child) && is.null(day) && is.null(meal)) {
    
    val <- getData(foodName, nutrient)
    
    return(if (!is.null(val) && !is.na(val)) as.numeric(val) * amount else NA)
    
  }
  
  
  
  data <- FD_1
  
  if (!is.null(child)) data <- filter(data, Study_ID == child)
  
  if (!is.null(meal)) data <- slice(data, meal)
  
  
  
  day_cols <- if (!is.null(day)) {
    
    paste0("Description of the food.", day, "_CLEAN")
    
  } else {
    
    grep("Description of the food.\\d+_CLEAN", names(data), value = TRUE)
    
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





extract_food_names <- function(entry) {
  
  if (is.na(entry)) return(character(0))
  
  items <- unlist(strsplit(entry, ";"))
  
  foods <- trimws(sub("\\{.*\\}", "", items))
  
  return(foods)
  
}





extract_weight <- function(item) {
  
  if (is.na(item)) return(NA_real_)
  
  weight <- as.numeric(sub(".*\\{(.*)\\}", "\\1", item))
  
  return(weight)
  
}




get_food_nutrient_value <- function(foodName, nutrient, weight, child_id = NULL) {
  
  val <- getData(foodName, nutrient)
  
  
  

  
  if (is.null(val) || length(val) != 1 || is.na(val)) return(0)
  
  
  
  val_num <-(as.numeric(val))
  
  
  
  # FINAL CHECK to prevent crash
  
  if (!is.na(val_num) && !is.na(weight)) {
    
    return(val_num * weight)
    
  }
  
  
  
  return(0)
  
}







getChildNutrientTotal <- function(child_id, nutrient) {
  
  child_data <- FD_1 %>% filter(Study_ID == child_id)
  
  diary_columns <- grep("Description of the food.\\d+_CLEAN", names(child_data), value = TRUE)
  

  
  total <- 0
  
  days_with_data <- 0
  
  
  
  for (col in diary_columns) {
    

    
    column_data <- child_data[[col]]
    
    if (any(nzchar(column_data) & !is.na(column_data))) {
      
      days_with_data <- days_with_data + 1
      
    }
    
    
    
    for (i in seq_along(column_data)) {
      
      
      items <- unlist(strsplit(column_data[i], ";"))
      
      #column_data[i] contains a single semicolon-separated string of food items
      
      for (item in trimws(items)) {
        
        
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





nutrient_thresholds <- list(
  
  "Energy (kcal)" = 1300,
  
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




deficiency_results <- data.frame(
  
  Nutrient = character(),
  
  PercentDeficient = numeric(),
  
  stringsAsFactors = FALSE
  
)



for (nutrient in names(nutrient_thresholds)) {
  

  
  threshold <- nutrient_thresholds[[nutrient]]
  
  
  
  nutrient_data <- subset(child_results, Nutrient == nutrient)
  
  
  
  deficient_count <- sum(!is.na(nutrient_data$AvgIntakePerDay) & nutrient_data$AvgIntakePerDay < threshold)
  
  
  
  
  
  total_count <- sum(!is.na(nutrient_data$AvgIntakePerDay))
  
  percent <- (deficient_count / total_count) * 100
  
  deficiency_results <- rbind(deficiency_results, data.frame(
    
    Nutrient = nutrient,
    
    PercentDeficient = percent
    
  ))
  
}



View(deficiency_results)

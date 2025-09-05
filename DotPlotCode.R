# --- 1. Load Required Libraries ---
# If you don't have this package installed, uncomment the line below and run it once.
# install.packages("tidyverse")

library(tidyverse)
library(stringr)

# --- 2. Create a Directory for the Plots ---
# This will create a folder named "Dot Plots" in your current working directory.
# The `showWarnings = FALSE` part prevents an error if the folder already exists.
dir.create("Dot Plots", showWarnings = FALSE)
print("Created 'Dot Plots' folder to save the images.")

# --- 3. Load the Data ---
# Make sure your CSV file is in the same directory as your R script.
file_path <- "/Users/vishal/Library/CloudStorage/Box-Box/Bangladesh Nutrition Data Cleaning 2025/FinalTables(WithKCal)/child_results.csv"
nutrient_data <- read_csv(file_path)

# --- 4. Define Nutrient Deficiency Thresholds ---
# These are the values you provided.
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

# --- 5. Loop Through Each Nutrient and Create a Dot Plot ---
# We loop through the names of the thresholds list to ensure we only process nutrients with a defined threshold.
for (nutrient_name in names(nutrient_thresholds)) {
  
  # Filter the data for the current nutrient
  nutrient_subset <- filter(nutrient_data, Nutrient == nutrient_name)
  
  # Get the threshold value for the current nutrient
  threshold_value <- nutrient_thresholds[[nutrient_name]]
  
  # Create the dot plot using ggplot2
  dot_plot <- ggplot(nutrient_subset, aes(x = AvgIntakePerDay)) +
    # geom_dotplot helps visualize the distribution of individual data points
    geom_dotplot(binaxis = 'x', stackdir = 'center', dotsize = 0.7, fill = "dodgerblue") +
    
    # Add a vertical line for the deficiency threshold
    geom_vline(
      xintercept = threshold_value,
      color = "red",
      linetype = "dashed", # Makes the line dashed
      size = 1 # Makes the line a bit thicker
    ) +
    
    # Add a text label for the threshold line
    annotate(
      "text",
      x = threshold_value,
      y = Inf, # Position at the top
      label = "Deficiency Threshold",
      hjust = 1.05, # Adjust horizontal position to be just left of the line
      vjust = 2,    # Adjust vertical position to be just below the top
      color = "red",
      angle = 90 # Rotate text to be vertical
    ) +
    
    # Set the titles and axis labels
    labs(
      title = paste("Dot Plot of", nutrient_name, "Intake"),
      subtitle = paste("Deficiency Threshold:", threshold_value),
      x = "Average Intake Per Day",
      y = "Frequency"
    ) +
    theme_minimal()
  
  # --- 6. Save the Dot Plot to the new folder ---
  
  # Create a clean filename
  safe_filename <- str_replace_all(nutrient_name, "[^[:alnum:]]", "_")
  output_filename <- paste0(safe_filename, "_dotplot.jpg")
  
  # Create the full path to save the file inside the "Dot Plots" folder
  full_save_path <- file.path("Dot Plots", output_filename)
  
  # Save the plot
  #ggsave(plot = dot_plot, filename = full_save_path, width = 10, height = 6, dpi = 300)
  ggsave(plot = dot_plot, filename = full_save_path, width = 10, height = 15, dpi = 300)
  
  print(paste("Saved dot plot for:", nutrient_name, "as", full_save_path))
}

print("All dot plots have been generated and saved in the 'Dot Plots' folder!")

# --- 1. Load Required Libraries ---
library(tidyverse)
library(stringr)

# --- 2. Create a Directory for the Plots ---
dir.create("Dot Plots", showWarnings = FALSE)
print("Ensured 'Dot Plots' folder exists.")

# --- 3. Load the Data ---
file_path <- "/Users/vishal/Library/CloudStorage/Box-Box/Bangladesh Nutrition Data Cleaning 2025/FinalTables(WithKCal)/child_results.csv"
nutrient_data <- read_csv(file_path)


# --- 4. Define Nutrient Deficiency Thresholds ---
nutrient_thresholds <- list(
  "Energy (kcal)" = 1300, "Water (g)" = 1600, "Protein (g)" = 19,
  "Fat (g)" = 44, "Carbohydrate available (g)" = 130, "Total dietary fibre (g)" = 25,
  "Ash (g)" = 49, "Ca (mg)" = 1000, "Fe (mg)" = 10, "Mg (mg)" = 100,
  "P (mg)" = 500, "K (mg)" = 3800, "Na (mg)" = 1200, "Zn (mg)" = 5,
  "Cu (mg)" = 0.44, "Vitamin A (mcg)" = 400, "Retinol (mcg)" = 300,
  "Beta-carotene equivalents (mcg)" = 1200, "Vitamin D (mcg)" = 15,
  "Vitamin E (mg)" = 7, "Thiamin (mg)" = 0.6, "Riboflavin (mg)" = 0.6,
  "Niacin equivalents (mg)" = 8, "Vitamin B6 (mg)" = 0.6, "Folate (mcg)" = 200,
  "Vitamin C (mg)" = 25
)

# --- 5. Loop Through Each Nutrient and Create a Dynamically Sized Plot ---
for (nutrient_name in names(nutrient_thresholds)) {
  
  nutrient_subset <- filter(nutrient_data, Nutrient == nutrient_name)
  threshold_value <- nutrient_thresholds[[nutrient_name]]
  
  # --- Create the plot object (no changes here) ---
  dot_plot <- ggplot(nutrient_subset, aes(x = AvgIntakePerDay)) +
    geom_dotplot(binaxis = 'x', stackdir = 'center', dotsize = 0.7, fill = "dodgerblue") +
    geom_vline(
      xintercept = threshold_value, color = "red", linetype = "dashed", linewidth = 1
    ) +
    annotate(
      "text", x = threshold_value, y = Inf, label = "Deficiency Threshold",
      hjust = 1.05, vjust = 2, color = "red", angle = 90
    ) +
    labs(
      title = paste("Dot Plot of", nutrient_name, "Intake"),
      subtitle = paste("Deficiency Threshold:", threshold_value),
      x = "Average Intake Per Day", y = "Frequency"
    ) +
    theme_minimal()
  
  # --- DYNAMIC SIZING LOGIC ---
  # 1. Build the plot data to inspect its properties before rendering
  plot_data <- ggplot_build(dot_plot)
  
  # 2. Find the maximum stack count from the plot's data layer
  #    The 'count' variable tells us how many dots are in the tallest stack.
  max_stack_count <- max(plot_data$data[[1]]$count)
  
  # 3. Calculate a dynamic height for the output image
  #    - We start with a base height of 3 inches.
  #    - We add 0.1 inches for each dot in the tallest stack.
  #    - You can TWEAK these numbers (3 and 0.1) to change the final look!
  dynamic_height <- 3 + (max_stack_count * 0.1)
  
  # --- 6. Save the Dot Plot with the new dynamic height ---
  safe_filename <- str_replace_all(nutrient_name, "[^[:alnum:]]", "_")
  output_filename <- paste0(safe_filename, "_dotplot.jpg")
  full_save_path <- file.path("Dot Plots", output_filename)
  
  ggsave(
    plot = dot_plot, 
    filename = full_save_path, 
    width = 10, 
    height = dynamic_height, # Use our calculated dynamic height
    dpi = 300
  )
  
  print(paste("Saved plot for:", nutrient_name, "with dynamic height:", round(dynamic_height, 2), "inches"))
}

print("All dot plots have been generated and saved with dynamic sizing!")
# Install and load necessary packages
# If you don't have these packages installed, uncomment the following lines and run them once.
# install.packages("tidyverse")

library(tidyverse)
library(stringr)

# --- 1. Load the Data ---
# Replace "path/to/your/Untitled spreadsheet.xlsx - Sheet1.csv" with the actual path to your file.
# If the file is in the same directory as your R script, you can just use the filename.
file_path <- "/Users/vishal/Library/CloudStorage/Box-Box/Bangladesh Nutrition Data Cleaning 2025/FinalTables(WithKCal)/child_results.csv"
nutrient_data <- read_csv(file_path)

# --- 2. Get the list of unique nutrients ---
unique_nutrients <- unique(nutrient_data$Nutrient)

# --- 3. Loop through each nutrient and create a histogram ---
for (nutrient_name in unique_nutrients) {
  
  # Filter the data for the current nutrient
  nutrient_subset <- filter(nutrient_data, Nutrient == nutrient_name)
  
  # Create the histogram using ggplot2
  # - `aes(x = AvgIntakePerDay)`: Sets the data for the x-axis.
  # - `geom_histogram()`: Creates the histogram.
  #   - `bins = 10`: Sets the number of bins to 10.
  #   - `fill = "skyblue"`: Sets the color of the bars.
  #   - `color = "black"`: Sets the color of the bar outlines.
  # - `labs()`: Sets the title and axis labels.
  # - `theme_minimal()`: Applies a clean and simple theme.
  
  histogram_plot <- ggplot(nutrient_subset, aes(x = AvgIntakePerDay)) +
    geom_histogram(bins = 10, fill = "skyblue", color = "black") +
    labs(
      title = paste("Histogram of", nutrient_name, "Intake"),
      x = "Average Intake Per Day",
      y = "Frequency"
    ) +
    theme_minimal()
  
  # --- 4. Save the histogram as a JPG file ---
  
  # Create a clean filename by replacing special characters and spaces
  # For example, "Energy (kcal)" becomes "Energy_kcal_histogram.jpg"
  safe_filename <- str_replace_all(nutrient_name, "[^[:alnum:]]", "_")
  output_filename <- paste0(safe_filename, "_histogram.jpg")
  
  # Save the plot
  # - `plot = histogram_plot`: The plot to save.
  # - `filename = output_filename`: The name of the file.
  # - `width = 8`, `height = 6`, `dpi = 300`: Sets the size and resolution of the image.
  ggsave(plot = histogram_plot, filename = output_filename, width = 8, height = 6, dpi = 300)
  
  # Print a message to the console to track progress
  print(paste("Saved histogram for:", nutrient_name, "as", output_filename))
}

print("All histograms have been generated and saved!")


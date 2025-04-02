How It Works: 


The program takes each line of data and converts it to a cleaned version following these steps and rules: 

If a food item contains more food items in (), then all food items will be cleaned normally, as if listed individually
If a dish name (like fish curry) contains food items in (), if there is more than one food item in the (),  then expand all food items in the (). Then, check if there is a recognized word in the name of the dish (in this case fish). If there is, and it is not already in the (), then add it to the expanded version of the dish. Example: fish curry (tomato, onion) -> fish, tomato, onion 
If the dish () contains one or zero items (nothing is in the parentheses), then expand the dish name using a default ingredients list found in dish_mappings. 
If a food item has its quantity specified in the () immediately following it, then it is measured appropriately. Example: rice (1 plate) 
If a food item does not have its quantity specified, but there is a quantity given in the quantity_ORIGINAL column, then apply that quantity to all remaining food items without a metric. Nonproteins will in total get 65% of the amount, while proteins get 35%. 
If a food item does not have its quantity specified, and there is no quantity given in the quantity_ORIGINAL column, then 300 grams will be divided among all remaining food items using the same distribution specified above.
Oils, unless specified otherwise, are always assumed to be 15 grams each. 
Garnishes, unless specified otherwise, are always assumed to be 10 grams each. 
If an item is unrecognized, it is flagged as UNKNOWN and will not be taken into account for the quantity distribution x


How to Use: 

All variables in the file variables.py are labeled and can be adjusted accordingly to suit interests. 
If an item appears as unknown, examine it. It could be an unknown metric, an unrecognized individual food item (pulse is another word for bean), or an unrecognized dish name. 
If it is an unknown metric, add it to the baseWeights map. 
If it is an unrecognized name for a food item (we discover Hacha is another word for tomato that the Bangladesh use) then Owe find the cleaned version of tomato in either meat_mappings or ingredient_categories. On the left, write the new name for the food item (in this case Hacha). On the right, put the cleaned name for the food (in this case "Tomato, red, ripe, boiled* (without salt)"). This will allow all instances of Hacha to be cleaned appropriately. 
If the food item does not have a corresponding clean item name (say tomato was not found in the Bangladesh nutrition chart), then consult the Indian food diary. Follow the same steps as above, and also add the cleaned erosion to ingredient_categories, categorizing it appropriately (protein, nonprotein, garnish or oil)  
If it is an unrecognized dish name, add it to the dish_mappings table, using Google to find the most standard ingredients used in the dish.  

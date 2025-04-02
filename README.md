**How It Works:**


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


**How to Use:** 

All variables in the file variables.py are labeled and can be adjusted accordingly to suit interests. 

If an item appears as unknown, examine it. It could be an unknown metric, an unrecognized individual food item (pulse is another word for bean), or an unrecognized dish name. 

If it is an unknown metric, add it to the baseWeights map. 

If it is an unrecognized name for a food item (we discover Hacha is another word for tomato that the Bangladesh use) then Owe find the cleaned version of tomato in either meat_mappings or ingredient_categories. On the left, write the new name for the food item (in this case Hacha). On the right, put the cleaned name for the food (in this case "Tomato, red, ripe, boiled* (without salt)"). This will allow all instances of Hacha to be cleaned appropriately. 

If the food item does not have a corresponding clean item name (say tomato was not found in the Bangladesh nutrition chart), then consult the Indian food diary. Follow the same steps as above, and also add the cleaned erosion to ingredient_categories, categorizing it appropriately (protein, nonprotein, garnish or oil)  

If it is an unrecognized dish name, add it to the dish_mappings table, using Google to find the most standard ingredients used in the dish.  

**Cases Will the Program May Not Work**

As of now, despite being popular food items in the dummy data, the Bangladesh food composition table does not contain any items similar to Pickles and Chips, and therefore cannot be cleaned. However, if able to access a different food table and attain a cleaned version from there, then fixing this is as simple as the process described in the section above. 

As of now, the program will never work on lines where the () are not closed and the commas are not placed properly. For example, Fish Curry (tomato, raddish, black chili, cucumber, oil, Cucurbit(2 pcs) Water (1 glass) is unable to be cleaned properly because the () for fish curry are never closed and there are no commas seperating cucurbit and water. This is because there is no pattern to determine where exactly the person met to place the closing ) or even the commas. In this case it may seem fairly obvious, but if a person were to list something like potato stew, potato and stew would not be seperated. The comma and ) could hypothetically be after any of the food items. However, these lines can be fixed rather easily by a human who can immediately identify the most likely place to put the ). The hope is that there are very few of these mistakes so that it would only take a few minutes at most to fix the lines that do have this problem. 

**Possible Other Features If Desired**

If desired, other possible features that could be implemented in the future include:

Each cleaned food item is assumed to have at least X amount of grams, even if the given portions suggest otherwise. 

For example, if a child wrote potato, onion, spinach, carrot, eggplant and 1 pcs in the quantity column, it is assumed each of these vegetables was 10 grams. (50/5). If a person would like to assume that each food item a child wrote was at least 15 grams, this could be done through a few more lines of code. 




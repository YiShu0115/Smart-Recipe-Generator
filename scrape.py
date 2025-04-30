import recipe

target_list = ['chicken', 'drumsticks']

recipe.scrape_recipes_to_json(target_list, 
                              driver_path='E:/Download Chrome/chromedriver-win64/chromedriver.exe', 
                              output_file='sample.json')
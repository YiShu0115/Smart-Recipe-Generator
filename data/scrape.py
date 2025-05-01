import recipe

proteins = [
    # 肉类
    'beef', 'pork', 'lamb', 'veal', 'mutton', 'goat', 'buffalo', 'bison', 'venison', 'wild boar',
    'rabbit', 'hare', 'squirrel', 'deer', 'elk', 'moose', 'caribou', 'reindeer', 'horse', 'donkey',

    # 禽类
    'chicken', 'turkey', 'duck', 'goose', 'quail', 'pigeon', 'ostrich', 'emu', 'pheasant', 'partridge',

    # 海鲜
    'salmon', 'tuna', 'cod', 'haddock', 'halibut', 'trout', 'mackerel', 'sardines', 'anchovies', 'herring',
    'flounder', 'sole', 'plaice', 'perch', 'pike', 'walleye', 'tilapia', 'catfish', 'bass', 'snapper',

    # 蛋类
    'chicken eggs', 'duck eggs', 'quail eggs', 'goose eggs', 'ostrich eggs',

    # 豆制品
    'tofu', 'tempeh', 'edamame', 'soybeans', 'lentils', 'chickpeas', 'black beans', 'kidney beans', 'navy beans', 'pinto beans',

    # 其他蛋白质
    'seitan', 'textured vegetable protein (TVP)', 'peanut butter', 'almond butter', 'cashew butter', 'sunflower seed butter',
    'pumpkin seed butter', 'sesame seed butter', 'hummus', 'black-eyed peas', 'split peas', 'navy beans', 'cannellini beans', 'adzuki beans'
    ]
vegetables_and_fruits = [
        # 蔬菜 (35种)
        'carrot', 'broccoli', 'cauliflower', 'spinach', 'kale', 'lettuce', 'arugula', 'celery', 'onion', 'garlic',
        'ginger', 'potato', 'sweet potato', 'yam', 'pumpkin', 'zucchini', 'eggplant', 'bell pepper', 'jalapeno', 'cucumber',
        'tomato', 'asparagus', 'artichoke', 'beet', 'cabbage', 'collard greens', 'fennel', 'leek', 'mushroom', 'radish',
        'rutabaga', 'turnip', 'watercress', 'chard', 'parsnip', 'okra', 'green beans', 'snow peas', 'string beans', 'kohlrabi',

        # 水果 (15种)
        'apple', 'banana', 'orange', 'strawberry', 'blueberry', 'raspberry', 'grape', 'pear', 'mango', 'pineapple',
        'kiwi', 'watermelon', 'cantaloupe', 'honeydew', 'lemon'
    ]
staple_foods = [
    'noodles',   # 面条
    'rice',      # 大米
    'pasta',     # 意大利面
    'bread',     # 面包
    'couscous',  # 库斯库斯
    'polenta',   # 玉米粥
    'quinoa',    # 藜麦
    'oatmeal',   # 燕麦粥
    'millet',    # 小米
    'barley'     # 大麦
]

target_list = proteins + vegetables_and_fruits + staple_foods
recipe.get_recipe_details(target_list) #4 servings
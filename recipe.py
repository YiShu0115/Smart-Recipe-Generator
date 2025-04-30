import json
import time
from typing import List, Dict, Optional

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup

def scrape_single_recipe(dish: str, driver_path: str) -> Optional[Dict]:
    """爬取单个菜品的内容并返回字典"""
    dish_to_search = '-'.join(dish.strip().split()) + '-'
    search_url = f"https://www.foodnetwork.com/search/{dish_to_search}"
    print(f"Accessing: {search_url}")

    options = Options()
    options.add_argument('--headless')
    options.add_argument('--disable-gpu')
    options.add_argument('--lang=en-US')
    options.add_argument('accept-language=en-US,en;q=0.9')

    service = Service(executable_path=driver_path)
    driver = webdriver.Chrome(service=service, options=options)

    try:
        driver.get(search_url)
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, 'div.o-ResultCard__m-MediaBlock'))
        )
        cards = driver.find_elements(By.CSS_SELECTOR, 'div.o-ResultCard__m-MediaBlock')

        recipe_link = None
        for card in cards:
            try:
                a_tag = card.find_element(By.TAG_NAME, 'a')
                href = a_tag.get_attribute('href')
                if href and '/recipes/' in href:
                    recipe_link = href
                    break
            except Exception:
                continue

        if not recipe_link:
            print(f"No recipe found for {dish}")
            driver.quit()
            return None

        print(f"Found recipe link: {recipe_link}")
        driver.get(recipe_link)
        time.sleep(2)

        soup = BeautifulSoup(driver.page_source, 'html.parser')

        ingredients = [item.text.strip() for item in soup.find_all('span', {'class': 'o-Ingredients__a-Ingredient--CheckboxLabel'})]
        steps = [item.text.strip() for item in soup.find_all('li', {'class': 'o-Method__m-Step'})]

        time_serving_details = soup.find_all('span', {'class': 'o-RecipeInfo__a-Description'})
        level = '-'
        total_time = '-'
        prep_time = '-'
        cook_time = '-'
        servings = '-'

        if time_serving_details != []:
            if len(time_serving_details) >= 12:
                level = time_serving_details[0].text.strip()
                total_time = time_serving_details[1].text.strip()
                prep_time = time_serving_details[2].text.strip() + '+' + time_serving_details[3].text.strip()
                cook_time = time_serving_details[4].text.strip()
                servings = time_serving_details[5].text.strip()
            elif len(time_serving_details) >= 10:
                level = time_serving_details[0].text.strip()
                total_time = time_serving_details[1].text.strip()
                prep_time = time_serving_details[2].text.strip()
                cook_time = time_serving_details[3].text.strip()
                servings = time_serving_details[4].text.strip()
            elif len(time_serving_details) >= 8:
                level = time_serving_details[0].text.strip()
                total_time = time_serving_details[1].text.strip()
                cook_time = time_serving_details[2].text.strip()
                servings = time_serving_details[3].text.strip()

        driver.quit()

        return {
            dish: {
                'ingredient': ingredients,
                'step': steps,
                'level': level,
                'total_time': total_time,
                'prep_time': prep_time,
                'cook_time': cook_time,
                'servings': servings
            }
        }

    except Exception as e:
        driver.quit()
        print(f"Error occurred for {dish}: {e}")
        return None

def scrape_recipes_to_json(dish_list: List[str], driver_path: str, output_file: str = "recipes.json"):
    """输入菜品列表，批量爬取并保存为 JSON 文件"""
    all_recipes = {}

    for dish in dish_list:
        recipe_data = scrape_single_recipe(dish, driver_path)
        if recipe_data:
            all_recipes.update(recipe_data)

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(all_recipes, f, ensure_ascii=False, indent=2)

    print(f"Saved {len(all_recipes)} recipes to {output_file}")

def load_recipes_from_json(file_path: str) -> Dict:
    """读取 JSON 文件并返回字典"""
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return data

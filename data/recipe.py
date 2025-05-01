import nltk
nltk.download('punkt')
nltk.download('averaged_perceptron_tagger')
import json
import requests
from bs4 import BeautifulSoup
import time
import random
from fake_useragent import UserAgent

recipe = {}
global_dish = ''
def extract_recipe_details(soup):
    details = {
        'level': None,
        'total_time': None,
        'prep_time': None,
        'cook_time': None,
        'servings': None
    }
    
    # 提取servings
    yield_heading = soup.find('span', class_='o-RecipeInfo__a-Headline', string='Yield:')
    if yield_heading:
        details['servings'] = yield_heading.find_next_sibling('span', class_='o-RecipeInfo__a-Description').text.strip()
    
    # 提取难度级别
    level_heading = soup.find('span', class_='o-RecipeInfo__a-Headline', string='Level:')
    if level_heading:
        details['level'] = level_heading.find_next_sibling('span', class_='o-RecipeInfo__a-Description').text.strip()
    
    # 提取总时间
    total_time_heading = soup.find('span', class_='o-RecipeInfo__a-Headline m-RecipeInfo__a-Headline--Total', string='Total:')
    if total_time_heading:
        details['total_time'] = total_time_heading.find_next_sibling('span', class_='o-RecipeInfo__a-Description').text.strip()
    
    # 提取准备时间
    prep_time_heading = soup.find('span', class_='o-RecipeInfo__a-Headline', string='Prep:')
    if prep_time_heading:
        details['prep_time'] = prep_time_heading.find_next_sibling('span', class_='o-RecipeInfo__a-Description').text.strip()

    # 提取等待时间
    prep_time_heading = soup.find('span', class_='o-RecipeInfo__a-Headline', string='Inactive:')
    if prep_time_heading:
        details['inactive_time'] = prep_time_heading.find_next_sibling('span', class_='o-RecipeInfo__a-Description').text.strip()
    
    # 提取烹饪时间
    cook_time_heading = soup.find('span', class_='o-RecipeInfo__a-Headline', string='Cook:')
    if cook_time_heading:
        details['cook_time'] = cook_time_heading.find_next_sibling('span', class_='o-RecipeInfo__a-Description').text.strip()

    # 找到营养信息表格
    nutrition_table = soup.find('dl', class_='m-NutritionTable_a-Content')
    if not nutrition_table:
        return details
    
    return details


import time
import random
from fake_useragent import UserAgent

def get_recipe_details(dish_list, max_results=8, output_file='recipe.json'):
    """
    获取多个菜品的详细信息，每个菜品保留多个菜谱结果
    参数:
        dish_list: 可以是一个字符串(单个菜品)或列表(多个菜品)
        max_results: 每个菜品保留的最大结果数(默认为3)
        output_file: 结果保存的文件名
    返回:
        包含所有菜谱详细信息的字典，key为recipe_name
    """
    # 初始化随机User-Agent生成器
    ua = UserAgent()
    
    # 如果输入是单个字符串，转换为列表
    if isinstance(dish_list, str):
        dish_list = [dish_list]
    
    all_recipes = {}  # 存储所有菜谱的字典
    
    for dish in dish_list:
        dish_to_search = '-'.join(dish.split(' '))
        print(f"正在搜索: {dish_to_search}")
        
        try:
            # 设置随机请求头和延迟
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
                'Accept-Language': 'en-US,en;q=0.9',
                'Referer': 'https://www.foodnetwork.com/',
                'Sec-Fetch-Dest': 'document',
                'Sec-Fetch-Mode': 'navigate'
            }
            
            # 随机延迟1-3秒
            time.sleep(random.uniform(3, 5))

            # 搜索菜品
            URL = f"https://www.foodnetwork.com/search/{dish_to_search}-"
            session = requests.Session()
            session.headers.update(headers)
            response = session.get(URL)
            # response = requests.get(URL, headers=headers)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')

            # 提取所有食谱链接 - 使用更稳健的选择器
            recipe_links = []
            for item in soup.select('div.m-MediaBlock__m-TextWrap'):
                if item.find('span', class_='m-Info__a-SubHeadline', string='Recipe'):
                    link_tag = item.find('a', href=True)
                    if link_tag:
                        recipe_links.append('https:' + link_tag['href'])

            if not recipe_links:
                print(f"未找到 {dish} 的食谱链接")
                continue

            # 限制结果数量
            recipe_links = recipe_links[:max_results]
            print(f"为 {dish} 找到 {len(recipe_links)} 个食谱链接")

            for link in recipe_links:
                try:
                    # 随机延迟
                    time.sleep(random.uniform(3,5))
                    
                    # 获取食谱详情页
                    headers['User-Agent'] = ua.random  # 更换User-Agent
                    response = requests.get(link, headers=headers)
                    response.raise_for_status()
                    soup = BeautifulSoup(response.text, 'html.parser')

                    # 提取菜谱名称 - 更稳健的提取方式
                    recipe_name = None
                    name_tag = soup.find('h1', class_='o-AssetTitle__a-Headline') or \
                               soup.find('span', class_='m-MediaBlock__a-HeadlineText')
                    if name_tag:
                        recipe_name = name_tag.get_text(strip=True)
                    
                    if not recipe_name:
                        print(f"无法提取菜谱名称，跳过: {link}")
                        continue
                    
                    # 确保名称唯一
                    if recipe_name in all_recipes:
                        recipe_name = f"{recipe_name} ({dish})"

                    # 提取时间和服务信息
                    recipe_details = extract_recipe_details(soup)
                    print(recipe_details)

                    # 提取配料
                    ingredients = []
                    for ing in soup.select('span.o-Ingredients__a-Ingredient--CheckboxLabel'):
                        text = ing.get_text(strip=True)
                        if text and not text.lower().startswith(('recipe', 'ingredients')):
                            ingredients.append(text)

                    # 提取步骤
                    steps = [step.get_text(strip=True) 
                            for step in soup.select('li.o-Method__m-Step') if step.get_text(strip=True)]

                    # 添加到结果字典
                    all_recipes[recipe_name] = {
                        'search_item': dish,
                        'ingredients': ingredients,
                        'steps': steps,
                        **recipe_details,
                        'source_url': link
                    }

                except Exception as e:
                    print(f"处理链接 {link} 时出错: {str(e)}")
                    continue

        except Exception as e:
            print(f"搜索 {dish} 时出错: {str(e)}")
            continue
    
    # 保存结果到JSON文件
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(all_recipes, f, ensure_ascii=False, indent=2)
    
    print(f"成功保存 {len(all_recipes)} 个菜谱到 {output_file}")
    return all_recipes

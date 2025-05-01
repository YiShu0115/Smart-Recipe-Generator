import nltk
nltk.download('punkt')
nltk.download('averaged_perceptron_tagger')
import numpy
import json
import re
import pandas as pd
from collections import Counter
import requests
from bs4 import BeautifulSoup
import spacy
from nltk import pos_tag
from nltk import RegexpParser
from fractions import Fraction
from transformers import pipeline
import tkinter as tk
import customtkinter
from functools import partial 
import pyttsx3
import tkinter as tk
import customtkinter
import speech_recognition as sr


recipe = {}
global_dish = ''
def get_recipe_details(dish_list, output_file='recipe.json'):
    """
    获取多个菜品的详细信息
    参数:
        dish_list: 可以是一个字符串(单个菜品)或列表(多个菜品)
    返回:
        包含所有菜品详细信息的字典
    """
    # 如果输入是单个字符串，转换为列表
    if isinstance(dish_list, str):
        dish_list = [dish_list]
    
    recipes = {}  # 存储所有菜品的字典
    
    for dish in dish_list:
        ingredient_list = []
        step_list = []
        level = '-'
        total_time = '-'
        prep_time = '-'
        cook_time = '-'
        servings = '-'

        dish_to_search = ''
        split_text = dish.split(' ')
        for i in split_text:
            dish_to_search += i
            dish_to_search += '-'
        
        print(f"正在搜索: {dish_to_search}")
        
        try:
            # 搜索菜品在foodnetwork网站
            URL = f"https://www.foodnetwork.com/search/{dish_to_search}"
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            response = requests.get(URL, headers=headers)
            response.encoding = 'utf-8'
            soup = BeautifulSoup(response.text, 'html.parser')

            # 提取所有食谱链接
            recipe_result_list = soup.find_all('div', {'class': 'm-MediaBlock__m-TextWrap'})
            recipe_links = []
            
            for i in recipe_result_list:
                if i.find('span', {'class': 'm-Info__a-SubHeadline'}) is not None:
                    is_result_recipe = i.find('span', {'class': 'm-Info__a-SubHeadline'}).text.strip() == 'Recipe'
                    if is_result_recipe:
                        recipe_link_tag = i.find('h3', {'class': 'm-MediaBlock__a-Headline'})
                        recipe_links.append('https:' + recipe_link_tag.find('a')['href'])

            if not recipe_links:
                print(f"未找到 {dish} 的食谱链接")
                continue

            recipe_link_url = recipe_links[0]
            print(f"找到食谱链接: {recipe_link_url}")

            # 获取食谱详情页
            response = requests.get(recipe_link_url, headers=headers)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 从<a>标签的title属性提取菜谱名称
            span_tag = soup.find('span', class_="m-MediaBlock__a-HeadlineText")
            # 提取文本内容
            if span_tag:
                recipe_name = span_tag.get_text(strip=True)
                
            # 提取时间和服务信息
            time_serving_details = soup.find_all('span', {'class': 'o-RecipeInfo__a-Description'})
            if time_serving_details:
                # 处理不同格式的时间信息
                if len(time_serving_details) >= 6:
                    level = time_serving_details[0].text.strip()
                    total_time = time_serving_details[1].text.strip()
                    prep_time = time_serving_details[2].text.strip() + '+' + time_serving_details[3].text.strip()
                    cook_time = time_serving_details[4].text.strip()
                    servings = time_serving_details[5].text.strip()
                elif len(time_serving_details) >= 5:
                    level = time_serving_details[0].text.strip()
                    total_time = time_serving_details[1].text.strip()
                    prep_time = time_serving_details[2].text.strip()
                    cook_time = time_serving_details[3].text.strip()
                    servings = time_serving_details[4].text.strip()
                else:
                    level = time_serving_details[0].text.strip()
                    total_time = time_serving_details[1].text.strip()
                    cook_time = time_serving_details[2].text.strip()
                    servings = time_serving_details[3].text.strip()

            # 提取配料
            ingredients = soup.find_all('span', {'class': 'o-Ingredients__a-Ingredient--CheckboxLabel'})
            ingredient_list = [ingredient.text.strip() for ingredient in ingredients]
            if ingredient_list:
                del ingredient_list[0]  # 删除第一个元素(通常是标题)

            # 提取步骤
            steps = soup.find_all('li', {'class': 'o-Method__m-Step'})
            step_list = [step.text.strip() for step in steps]

            # 添加到结果字典
            recipes[dish] = {
                'recipe_name':recipe_name,
                'ingredient': ingredient_list,
                'step': step_list,
                'level': level,
                'total_time': total_time,
                'prep_time': prep_time,
                'cook_time': cook_time,
                'servings': servings,
                'source_url': recipe_link_url
            }

        except Exception as e:
            print(f"处理 {dish} 时出错: {str(e)}")
            recipes[dish] = {'error': str(e)}
            # 保存结果到JSON文件
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(recipes, f, ensure_ascii=False, indent=2)
    
    print(f"结果已保存到 {output_file}")
    
    return recipes



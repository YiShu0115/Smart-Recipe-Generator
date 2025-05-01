# 在现有导入部分添加
from llama_index.core import PromptTemplate
from typing import Optional, List
import re

import nest_asyncio
import json
from llama_index.core import Settings
from llama_index.llms.ollama import Ollama
from core.prepare import prepare_documents, build_index
from core.query import query_answer, init_chat_engine, chat_turn, keyword_based_answer, suggest_recipes_by_ingredients, find_similar_recipes
from core.utils import get_keywords_from_llama, scale_ingredients
from core.embedding import get_embed_model
from fastapi import FastAPI 
from pydantic import BaseModel

# --- 初始化部分 ---
nest_asyncio.apply()

# 载入数据
with open("sample.json", 'r', encoding='utf-8') as f:
    recipe_data = json.load(f)

# 设置模型
Settings.llm = Ollama(model="tinyllama:1.1b", request_timeout=600.0)
Settings.embed_model = get_embed_model("nomic-embed-text")
Settings.chunk_size = 1024

# 准备索引
documents = prepare_documents(recipe_data)
index = build_index(documents)

# 准备多轮聊天引擎
chat_engine = init_chat_engine(index)

# 添加意图识别相关的辅助函数
intent_prompt = PromptTemplate("""
分析用户的食谱相关请求，判断其意图类型。可选类型有：
- suggest (根据食材推荐)
- scale (调整份量)
- similar (查找相似食谱)
- query (一般查询)
- chat (多轮对话)

只需返回类型名称，不要解释。

用户输入: {user_input}
意图:""")

def detect_intent(user_input: str) -> str:
    """使用LLM判断用户意图"""
    response = Settings.llm.complete(intent_prompt.format(user_input=user_input))
    return response.text.strip().lower()

def extract_ingredients(text: str) -> List[str]:
    """从用户输入中提取食材"""
    # 简单实现：提取引号内内容或特定模式
    quoted = re.findall(r'["「](.*?)["」]', text)
    if quoted:
        return [item.strip() for item in quoted[0].split("、") if item.strip()]
    
    # 提取"我有X、Y和Z"模式
    have_pattern = re.search(r'[我有包含].*?([^，。]+)', text)
    if have_pattern:
        items = have_pattern.group(1)
        return [item.strip() for item in re.split(r'[、和,]', items) if item.strip()]
    
    return []

def extract_scale_factor(text: str) -> float:
    """从用户输入中提取调整比例"""
    # 提取数字比例
    numbers = re.findall(r'(\d+\.?\d*)', text)
    if "减半" in text or "一半" in text:
        return 0.5
    elif "加倍" in text or "两倍" in text:
        return 2.0
    elif numbers:
        return float(numbers[0])
    return 1.0  # 默认不调整

# 添加统一请求体
class UnifiedRequest(BaseModel):
    query: str
    current_recipe: Optional[dict] = None  # 用于维护对话状态中的当前食谱

# 添加统一路由端点
@app.post("/unified_query")
async def unified_query(req: UnifiedRequest):
    # 1. 判断用户意图
    intent = detect_intent(req.query)
    
    # 2. 根据意图处理请求
    if intent == "suggest":
        ingredients = extract_ingredients(req.query)
        if not ingredients:
            return {"error": "未识别到有效食材，请尝试例如: '我有土豆和牛肉能做什么菜'"}
        result = suggest_recipes_by_ingredients(ingredients, index)
        return {"intent": "suggest", "result": result}
    
    elif intent == "scale":
        if not req.current_recipe:
            return {"error": "请先选择要调整份量的食谱"}
        scale_by = extract_scale_factor(req.query)
        scaled = scale_ingredients(req.current_recipe['ingredients'], scale_by)
        return {"intent": "scale", "result": scaled}
    
    elif intent == "similar":
        result = find_similar_recipes(req.query, index, Settings.embed_model)
        return {"intent": "similar", "result": result}
    
    elif intent == "query":
        result = query_answer(req.query, index)
        return {"intent": "query", "result": result}
    
    elif intent == "keywords":
        result = keyword_based_answer(req.query, index, get_keywords_from_llama)
        return {"intent": "keywords", "result": result}
    
    else:  # 默认为聊天
        result = chat_turn(req.query, chat_engine)
        return {"intent": "chat", "result": result}

# 导出初始化好的对象
def get_initialized_objects():
    return {
        "index": index,
        "chat_engine": chat_engine,
        "settings": Settings
    }

# 确保这些对象可以被导入
__all__ = [
    'get_initialized_objects',
    'detect_intent',
    'extract_ingredients',
    'extract_scale_factor',
    'UnifiedRequest'
]

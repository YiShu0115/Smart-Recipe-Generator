# app.py

from fastapi import FastAPI
from pydantic import BaseModel
from core.prepare import prepare_documents, build_index
from core.query import query_answer, init_chat_engine, chat_turn, keyword_based_answer, suggest_recipes_by_ingredients, find_similar_recipes
from core.utils import get_keywords_from_llama, scale_ingredients
from core.embedding import get_embed_model

import nest_asyncio
import json
from llama_index.core import Settings
from llama_index.llms.ollama import Ollama

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

# --- FastAPI 应用 ---
app = FastAPI()

# --- 请求体 ---
class QueryRequest(BaseModel):
    query: str

class IngredientsRequest(BaseModel):
    ingredients: list

class ScaleRequest(BaseModel):
    ingredients: list
    scale_by: float

# --- API 路由 ---

@app.post("/query")
def query_recipe(req: QueryRequest):
    result = query_answer(req.query, index)
    return {"answer": result}

@app.post("/chat")
def chat_recipe(req: QueryRequest):
    result = chat_turn(req.query, chat_engine)
    return {"answer": result}

@app.post("/keyword_search")
def keyword_search_recipe(req: QueryRequest):
    result = keyword_based_answer(req.query, index, get_keywords_from_llama)
    return {"answer": result}

@app.post("/suggest")
def suggest_recipe_from_query(req: QueryRequest):
    result = suggest_recipes_by_query(req.query, index)
    return {"suggestions": result}

@app.post("/similar")
def similar_recipe(req: QueryRequest):
    result = find_similar_recipes(req.query, index, Settings.embed_model)
    return {"similar_recipes": result}

@app.post("/scale")
def scale_recipe(req: ScaleRequest):
    scaled = scale_ingredients(req.ingredients, req.scale_by)
    return {"scaled_ingredients": scaled}

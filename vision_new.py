# vision3.py
import streamlit as st
import re
import json
import nest_asyncio
from datetime import datetime
from typing import Dict, Any, Optional
from core.prepare import prepare_documents, build_index
from core.query import init_chat_engine, suggest_recipes_by_ingredients, find_similar_recipes
from core.smart_chat import smart_chat_turn  # 新增智能聊天模块
from core.embedding import get_embed_model
from core.utils import scale_ingredients, get_keywords_from_llama
from llama_index.core import Settings
from llama_index.llms.ollama import Ollama

# 初始化异步环境
nest_asyncio.apply()

# 应用配置
st.set_page_config(
    page_title="AI Recipe Assistant",
    page_icon="👩🍳",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 样式配置
def apply_custom_style():
    st.markdown("""
    <style>
        .recipe-card {
            padding: 2rem;
            border-radius: 10px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            margin: 1rem 0;
            background: white;
        }
        .metadata-row {
            display: flex;
            gap: 1rem;
            margin: 1rem 0;
        }
        .metadata-item {
            flex: 1;
            padding: 1rem;
            border-radius: 8px;
            background: #f8f9fa;
        }
        .ingredient-list {
            column-count: 2;
            margin: 1rem 0;
        }
    </style>
    """, unsafe_allow_html=True)

# 系统初始化（复用main.py逻辑）
def initialize_system():
    if "system_initialized" not in st.session_state:
        with st.spinner("🚀 正在初始化智能食谱系统..."):
            # 从main.py整合初始化逻辑
            with open("sample.json", 'r', encoding='utf-8') as f:
                recipe_data = json.load(f)

            # 严格使用core模块配置
            Settings.llm = Ollama(model="qwen:7b", request_timeout=600.0)
            Settings.embed_model = get_embed_model("nomic-embed-text")
            Settings.chunk_size = 1024

            # 使用core.prepare构建索引
            documents = prepare_documents(recipe_data)
            st.session_state.index = build_index(documents)
            
            # 初始化聊天引擎（来自core.query）
            st.session_state.chat_engine = init_chat_engine(st.session_state.index)
            
            st.session_state.system_initialized = True

# 解析食谱数据（复用prepare.py逻辑）
def parse_recipe_data(node_text: str) -> Dict[str, Any]:
    try:
        # 从原始文本解析元数据
        return {
            "name": re.search(r"Recipe: (.+)", node_text).group(1).strip(),
            "level": re.search(r"Level: (.+)", node_text).group(1).strip(),
            "total_time": re.search(r"Total Time: (.+)", node_text).group(1).strip(),
            "ingredients": [
                ing.strip() 
                for ing in re.search(r"Ingredients:\s*(.+?)\s*Steps:", node_text, re.DOTALL).group(1).split(",")
            ],
            "steps": [
                step.strip() 
                for step in re.search(r"Steps:\s*(.+)", node_text, re.DOTALL).group(1).split(".")
                if step.strip()
            ]
        }
    except Exception as e:
        st.error(f"解析食谱数据失败: {str(e)}")
        return {}

# 食谱卡片组件（增强版）
def render_recipe_card(recipe: Dict[str, Any]):
    with st.container():
        st.markdown(f'<div class="recipe-card">', unsafe_allow_html=True)
        
        # 头部信息
        st.subheader(f"🍳 {recipe.get('name', '未知食谱')}")
        
        # 元数据行
        st.markdown('<div class="metadata-row">', unsafe_allow_html=True)
        cols = st.columns(4)
        with cols[0]:
            st.markdown(f'<div class="metadata-item">⏱ 总时间<br><b>{recipe.get("total_time", "-")}</b></div>', unsafe_allow_html=True)
        with cols[1]:
            st.markdown(f'<div class="metadata-item">🌟 难度<br><b>{recipe.get("level", "-")}</b></div>', unsafe_allow_html=True)
        with cols[2]:
            st.markdown(f'<div class="metadata-item">👥 份量<br><b>{recipe.get("servings", "-")}</b></div>', unsafe_allow_html=True)
        with cols[3]:
            st.markdown(f'<div class="metadata-item">⏳ 准备时间<br><b>{recipe.get("prep_time", "-")}</b></div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

        # 原料列表
        with st.expander("📦 原料清单", expanded=True):
            st.markdown('<div class="ingredient-list">', unsafe_allow_html=True)
            for ing in recipe.get("ingredients", []):
                st.markdown(f"- {ing}")
            st.markdown('</div>', unsafe_allow_html=True)

        # 制作步骤
        with st.expander("👩🍳 制作步骤", expanded=True):
            for i, step in enumerate(recipe.get("steps", []), 1):
                st.markdown(f"{i}. {step}")

        st.markdown('</div>', unsafe_allow_html=True)

# 处理用户输入（严格使用core模块）
# 修改后的处理函数
def process_user_query(prompt: str):
    # 记录历史
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    try:
        # 使用核心模块处理不同类型的请求
        if "recommend" in prompt.lower():
            # 使用食材推荐逻辑
            ingredients = get_keywords_from_llama(prompt)
            response = suggest_recipes_by_ingredients(ingredients, st.session_state.index)
            response_type = "recommendation"
            
        elif "similar to" in prompt.lower():
            # 使用相似食谱逻辑
            target = prompt.lower().split("similar to")[-1].strip()
            response = find_similar_recipes(target, st.session_state.index, Settings.embed_model)
            response_type = "similar"
            
        elif any(kw in prompt.lower() for kw in ["scale", "adjust", "份量"]):
            # 使用缩放逻辑
            scale_factor = float(re.search(r"\d+", prompt).group())
            current_recipe = get_current_recipe()  # 需要实现获取当前食谱的逻辑
            scaled = scale_ingredients(current_recipe["ingredients"], scale_factor)
            response = "\n".join(scaled)
            response_type = "scale"
            
        else:
            # 使用普通聊天逻辑
            response = st.session_state.chat_engine.chat(prompt)
            response_type = "chat"
            
        # 记录响应
        st.session_state.messages.append({
            "role": "assistant",
            "content": str(response),
            "type": response_type
        })
        
    except Exception as e:
        st.error(f"处理请求时出错: {str(e)}")
        st.session_state.messages.append({
            "role": "assistant",
            "content": "😞 系统暂时不可用，请稍后再试"
        })

# 历史侧边栏（增强版）
def render_history_sidebar():
    with st.sidebar:
        st.header("📜 交互历史")
        if "history" not in st.session_state:
            st.session_state.history = []
        
        for idx, item in enumerate(reversed(st.session_state.history)):
            with st.expander(f"{item['timestamp']} - {item.get('recipe','')}", expanded=False):
                cols = st.columns([3,1])
                with cols[0]:
                    st.markdown(f"**查询**: {item['query']}")
                with cols[1]:
                    if item.get("operation"):
                        st.markdown(f"`{item['operation']}`")
                
                if item.get("data"):
                    if st.button("查看详情", key=f"detail_{idx}"):
                        st.session_state.current_recipe = item["data"]

# 主界面
def main_interface():
    apply_custom_style()
    initialize_system()
    
    # 初始化会话状态
    if "messages" not in st.session_state:
        st.session_state.messages = [{
            "role": "assistant",
            "content": "👩🍳 欢迎使用智能食谱助手！您可以使用自然语言：\n- 查询食谱步骤\n- 根据食材推荐\n- 调整食谱份量\n- 查找相似菜品"
        }]
    
    render_history_sidebar()
    
    with st.container():
        st.title("🍲 智能食谱助手")
        st.caption("基于RAG技术的智能烹饪解决方案")
        
        # 显示当前食谱
        if "current_recipe" in st.session_state:
            render_recipe_card(st.session_state.current_recipe)
            if st.button("← 返回对话界面"):
                del st.session_state.current_recipe
                st.rerun()
            return
            
        # 显示对话历史
        for msg in st.session_state.messages:
            with st.chat_message(msg["role"]):
                content = msg.get("content", "")
                metadata = msg.get("metadata", {})
                
                # 处理特殊响应
                if metadata.get("scaled_ingredients"):
                    st.markdown("**调整后的原料清单**")
                    for ing in metadata["scaled_ingredients"]:
                        st.markdown(f"- {ing}")
                elif metadata.get("similar_recipes"):
                    st.markdown("**相似食谱推荐**")
                    for recipe in metadata["similar_recipes"]:
                        st.markdown(f"- {recipe['name']} (相似度: {recipe['score']:.2f})")
                else:
                    st.markdown(content)
        
        # 用户输入处理
        if prompt := st.chat_input("输入您的烹饪问题（例如：如何做红烧肉？）"):
            # 记录历史上下文
            st.session_state.history.append({
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "query": prompt,
                "recipe": st.session_state.current_recipe.get("name") if "current_recipe" in st.session_state else None,
                "data": st.session_state.current_recipe if "current_recipe" in st.session_state else None,
                "operation": None
            })
            process_user_query(prompt)
            st.rerun()

if __name__ == "__main__":
    main_interface()

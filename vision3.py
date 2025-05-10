# vision3.py
import streamlit as st
import json
import re
import nest_asyncio
from datetime import datetime
from typing import Dict, Any, Optional, List
from core.prepare import prepare_documents, build_index
from core.query import init_chat_engine, query_answer, chat_turn
from core.smart_chat import smart_chat_turn, classify_query
from core.embedding import get_embed_model
from core.utils import scale_ingredients, get_keywords_from_llama, extract_number_from_text
from llama_index.core import Settings
from llama_index.llms.ollama import Ollama

# 初始化异步环境
nest_asyncio.apply()

# 应用配置
st.set_page_config(
    page_title="AI Recipe Assistant",
    page_icon="👩‍🍳",
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
            margin: 1rem 0;
        }
        .chat-message {
            margin: 1rem 0;
            padding: 1rem;
            border-radius: 8px;
        }
        .user-message {
            background: #e9f5ff;
            text-align: right;
        }
        .assistant-message {
            background: #f0f0f0;
        }
    </style>
    """, unsafe_allow_html=True)

# 系统初始化
def initialize_system():
    if "system_initialized" not in st.session_state:
        with st.spinner("🚀 Initializing AI Recipe System..."):
            with open("sample.json", 'r', encoding='utf-8') as f:
                recipe_data = json.load(f)

            Settings.llm = Ollama(model="qwen:7b", request_timeout=600.0)
            Settings.embed_model = get_embed_model("nomic-embed-text")
            Settings.chunk_size = 1024

            documents = prepare_documents(recipe_data)
            st.session_state.index = build_index(documents)
            
            st.session_state.chat_engine = init_chat_engine(st.session_state.index)

            st.session_state.system_initialized = True
            st.rerun()

# 食谱卡片组件
def render_recipe_card(recipe: Dict[str, Any]):
    with st.container():
        st.markdown(f'<div class="recipe-card">', unsafe_allow_html=True)
        
        st.subheader(f"🍳 {recipe.get('name', 'Unknown Recipe')}")
        
        cols = st.columns(4)
        with cols[0]:
            st.metric("⏱ Total Time", recipe.get("total_time", "-"))
        with cols[1]:
            st.metric("🌟 Difficulty", recipe.get("level", "-"))
        with cols[2]:
            st.metric("👥 Servings", recipe.get("servings", "-"))
        with cols[3]:
            st.metric("⏳ Prep Time", recipe.get("prep_time", "-"))

        with st.expander("📦 Ingredients", expanded=True):
            for ing in recipe.get("ingredients", []):
                st.markdown(f"- {ing}")

        with st.expander("👩‍🍳 Cooking Steps", expanded=True):
            for i, step in enumerate(recipe.get("steps", []), 1):
                st.markdown(f"{i}. {step}")

        st.markdown('</div>', unsafe_allow_html=True)

# 处理用户输入
def process_user_query(prompt: str):
    try:
        intent = classify_query(prompt)
        
        response = smart_chat_turn(
            query=prompt,
            chat_engine=st.session_state.chat_engine,
            index=st.session_state.index,
            embed_model=Settings.embed_model
        )
        
        st.session_state.messages.append({
            "role": "assistant",
            "content": response,
            "intent": intent
        })
        
        st.session_state.history.append({
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "query": prompt,
            "response": response,
            "intent": intent
        })
        
    except Exception as e:
        st.error(f"Error processing request: {str(e)}")
        st.session_state.messages.append({
            "role": "assistant",
            "content": f"😞 System temporarily unavailable: {str(e)}"
        })

# 显示历史消息对话框
@st.dialog("Conversation Details", width="large")
def show_detail_dialog(item):
    st.markdown(f"**Time:** {item['timestamp']}")
    
    st.markdown("### Question")
    st.markdown(item['query'])
    
    st.markdown("### Answer")
    st.markdown(item['response'])

# 历史侧边栏
def render_history_sidebar():
    with st.sidebar:
        st.header("📜 Query History")
        
        if "history" not in st.session_state:
            st.session_state.history = []
            st.info("No query history")
            return
        
        if not st.session_state.history:
            st.info("No query history")
            return
            
        for idx, item in enumerate(reversed(st.session_state.history)):
            with st.expander(f"{item['timestamp']}", expanded=False):
                st.markdown(f"**Query**: {item['query']}")
                st.markdown(f"**Type**: {item.get('intent', 'General Query')}")
                
                if st.button("Show Details", key=f"details_{idx}"):
                    # 直接调用对话框函数，不需要使用会话状态
                    show_detail_dialog(item)

# 主界面
def main_interface():
    # 防止重复初始化UI元素
    if "ui_initialized" not in st.session_state:
        st.session_state.ui_initialized = True
        apply_custom_style()
        
        # 只在第一次初始化messages
        if "messages" not in st.session_state:
            st.session_state.messages = [{
                "role": "assistant",
                "content": "👩‍🍳 Welcome to AI Recipe Assistant! You can:\n- Ask for recipe instructions\n- Get recommendations based on ingredients\n- Adjust recipe servings\n- Find similar recipes"
            }]
            
        initialize_system()
    else:
        # 已初始化过，只更新必要组件
        apply_custom_style()
    
    if "history" not in st.session_state:
        st.session_state.history = []
    
    if "waiting_for_response" not in st.session_state:
        st.session_state.waiting_for_response = False
    
    # 渲染侧边栏
    render_history_sidebar()
    
    # 主UI部分
    with st.container():
        st.title("👩‍🍳 AI Recipe Assistant")
        st.caption("Smart cooking solution powered by RAG technology")
        
        chat_container = st.container()
        with chat_container:
            for msg in st.session_state.messages:
                role = msg["role"]
                content = msg["content"]
                
                with st.chat_message(role):
                    st.markdown(content)
            
            if st.session_state.waiting_for_response:
                with st.chat_message("assistant"):
                    with st.spinner("🤔 Thinking..."):
                        process_user_query(st.session_state.last_user_message)
                        st.session_state.waiting_for_response = False
                        st.rerun()
        
        if prompt := st.chat_input("Enter your cooking question (e.g., recommend a simple Chinese dish, how to make scrambled eggs)"):
            st.session_state.messages.append({"role": "user", "content": prompt})
            st.session_state.waiting_for_response = True
            st.session_state.last_user_message = prompt
            st.rerun()

if __name__ == "__main__":
    main_interface() 
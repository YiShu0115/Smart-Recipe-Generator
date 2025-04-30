import streamlit as st
from llama_index.core import VectorStoreIndex, Document
from llama_index.llms.ollama import Ollama
from llama_index.embeddings.ollama import OllamaEmbedding
from llama_index.core import Settings
from llama_index.core.memory import ChatMemoryBuffer
import nest_asyncio
from PIL import Image
import base64
from typing import Dict, Any
from datetime import datetime  # 添加缺失的datetime导入

# 增强样式配置（修复函数名不一致问题）
def apply_enhanced_style():
    # 样式不再包含食材卡片和步骤分块
    st.markdown("""
    <style>
        /* 主容器样式 */
        .main-container {
            max-width: 1200px;
            margin: 0 auto;
        }
    </style>
    """, unsafe_allow_html=True)

# 菜谱卡片组件（直接文本输出）
def recipe_card(recipe_data: Dict[str, Any]):
    with st.container():
        ingredients = "\n".join(recipe_data.get("ingredient", []))
        steps = "\n".join([f"Step {i+1}: {step}" for i, step in enumerate(recipe_data.get("step", []))])
        
        st.markdown(f"""
        ### {recipe_data.get('recipe_name', '未知菜谱')}
        **🕒 时间**: {recipe_data.get('cook_time', '未知时间')}  
        **👨🍳 难度**: {recipe_data.get('difficulty', '未知难度')}  
        **🌍 菜系**: {recipe_data.get('cuisine', '未知菜系')}
        
        **📝 原料清单**
        {ingredients}
        
        **👩🍳 制作步骤**
        {steps}
        """)

# 历史记录侧边栏
def history_sidebar():
    with st.sidebar:
        st.header("📚 历史记录")
        if "history" not in st.session_state:
            st.session_state.history = []
            
        # 显示历史条目
        for idx, item in enumerate(st.session_state.history[::-1]):
            with st.expander(f"记录 #{len(st.session_state.history)-idx}"):
                st.markdown(f"""
                **时间**: {item['timestamp']}  
                **输入**: {item['query']}  
                **推荐菜谱**: {item['recipe_name']}
                """)
                if st.button("查看详情", key=f"view_{idx}"):
                    st.session_state.current_recipe = item

# 主界面增强
def enhanced_main():
    apply_enhanced_style()
    
    # 初始化会话状态
    if "messages" not in st.session_state:
        st.session_state.messages = [{
            "role": "assistant",
            "content": "👩🍳 欢迎使用智能菜谱助手！请提问烹饪相关问题："
        }]
    
    # 历史记录面板
    history_sidebar()
    
    # 主内容区
    col1, col2 = st.columns([3, 1])
    
    with col1:
        st.title("👩🍳 智能菜谱助手")
        st.caption("基于RAG的智能烹饪解决方案")
        
        # 当前菜谱展示
        if "current_recipe" in st.session_state:
            recipe_card(st.session_state.current_recipe)
            return
        
        # 动态消息展示
        for msg in st.session_state.messages:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])

        # 用户输入处理
        if prompt := st.chat_input("输入烹饪问题..."):
            handle_user_input(prompt)

# 输入处理逻辑（添加try-except处理）
def handle_user_input(prompt: str):
    try:
        st.session_state.messages.append({"role": "user", "content": prompt})
        
        with st.spinner("🔍 正在分析您的需求..."):
            # 调用RAG引擎
            response = st.session_state.rag_engine.chat(prompt)
            
            # 解析响应结构
            if "原料清单" in response.response and "制作步骤" in response.response:
                # 提取菜谱元数据
                metadata = {
                    "recipe_name": response.response.split("】")[0].split("【")[-1],
                    "cook_time": "20分钟",
                    "difficulty": "中等",
                    "cuisine": "中餐",
                    "ingredient": [],
                    "step": []
                }
                
                # 记录历史
                st.session_state.history.append({
                    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M"),
                    "query": prompt,
                    "recipe_name": metadata["recipe_name"],
                    "full_data": metadata
                })
            
            st.session_state.messages.append({
                "role": "assistant",
                "content": response.response
            })
        
        st.rerun()
    except Exception as e:
        st.error(f"处理请求时发生错误: {str(e)}")
        st.session_state.messages.append({
            "role": "assistant",
            "content": "抱歉，处理您的请求时出现问题，请尝试重新输入。"
        })

if __name__ == "__main__":
    # 初始化RAG系统
    def initialize_rag():
        recipe_data = {
            "Pasta": {
                "ingredient": ["200g pasta", "2 cloves garlic", "100ml olive oil"],
                "step": ["Boil pasta 8 mins", "Chop garlic", "Fry garlic", "Mix all"],
                "metadata": {
                    "cuisine": "Italian",
                    "cook_time": "20 mins",
                    "difficulty": "Easy"
                }
            },
            "Kung Pao Chicken": {
                "ingredient": ["500g chicken", "50g peanuts", "3 dried chilies"],
                "step": ["Marinate chicken", "Stir-fry chilies", "Add peanuts"],
                "metadata": {
                    "cuisine": "Chinese",
                    "cook_time": "30 mins",
                    "difficulty": "Medium"
                }
            }
        }

        def prepare_documents(data):
            documents = []
            for name, details in data.items():
                text = f"""
                菜谱名称：{name}
                菜系：{details['metadata']['cuisine']}
                烹饪时间：{details['metadata']['cook_time']}
                难度：{details['metadata']['difficulty']}
            
                原料：
                {', '.join(details['ingredient'])}
            
                步骤：
                {'; '.join(details['step'])}
                """
                documents.append(Document(
                    text=text,
                    metadata={"recipe_name": name, **details["metadata"]}
                ))
            return documents

        Settings.llm = Ollama(model="qwen:7b", request_timeout=600.0)
        Settings.embed_model = OllamaEmbedding(model_name="nomic-embed-text")
    
        documents = prepare_documents(recipe_data)
        index = VectorStoreIndex.from_documents(documents)
        memory = ChatMemoryBuffer.from_defaults(token_limit=3900)
    
        return index, memory
    
    if "rag_engine" not in st.session_state:
        index, memory = initialize_rag()
        st.session_state.rag_engine = index.as_chat_engine(
            chat_mode="condense_plus_context",
            memory=memory,
            system_prompt=(
                "您是一位专业厨师助手，请根据菜谱数据库回答用户问题。\n"
                "回答时请：\n"
                "1. 使用【菜谱名称】开头\n"
                "2. 分原料清单和制作步骤说明\n"
                "3. 给出3条烹饪小贴士\n"
                "4. 使用emoji图标增强可读性"
            )
        )
    
    enhanced_main()

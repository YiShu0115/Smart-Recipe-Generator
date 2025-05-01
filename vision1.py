import streamlit as st
import re
from datetime import datetime
from typing import Dict, Any
from llama_index.core import VectorStoreIndex, Document
from llama_index.llms.ollama import Ollama
from llama_index.embeddings.ollama import OllamaEmbedding
from llama_index.core import Settings
from llama_index.core.memory import ChatMemoryBuffer
import nest_asyncio

# 初始化异步环境
nest_asyncio.apply()

# 应用配置
st.set_page_config(
    page_title="智能菜谱助手",
    page_icon="👩🍳",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 常量配置
MAX_HISTORY = 10
SYSTEM_PROMPT = """请严格按以下格式回答：
【菜谱名称】
⏱ 时间：xx分钟
🌟 难度：初级/中等/困难
🌍 菜系：xx菜系

📝 原料清单：
- 材料1（用量）
- 材料2（用量）

👩🍳 制作步骤：
1. 步骤说明
2. 步骤说明

💡 小贴士：
- 实用提示1
- 实用提示2

要求：
1. 必须使用中文方括号【】包裹菜谱名称
2. 时间、难度、菜系需列在名称下方
3. 原料和步骤必须使用列表格式"""

# 样式配置
def apply_custom_style():
    st.markdown("""
    <style>
        .recipe-card {
            padding: 2rem;
            border-radius: 10px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            margin-bottom: 2rem;
        }
        .history-item {
            border-left: 4px solid #4CAF50;
            padding: 0.5rem 1rem;
            margin: 0.5rem 0;
            background: #f8f9fa;
        }
        .ingredient-list { color: #2e7d32; }
        .step-list { color: #1565c0; }
    </style>
    """, unsafe_allow_html=True)

# 菜谱卡片组件（增强版）
def recipe_card(recipe_data: Dict[str, Any]):
    with st.container():
        st.markdown('<div class="recipe-card">', unsafe_allow_html=True)
        
        # 头部信息
        st.subheader(f"🍳 {recipe_data.get('recipe_name', '未知菜谱')}")
        cols = st.columns(3)
        with cols[0]:
            st.metric("⏱ 烹饪时间", recipe_data.get("cook_time", "未注明"))
        with cols[1]:
            st.metric("🌟 制作难度", recipe_data.get("difficulty", "未注明"))
        with cols[2]:
            st.metric("🌍 菜品菜系", recipe_data.get("cuisine", "未注明"))

        # 原料和步骤分栏
        tab_ing, tab_step = st.tabs(["📦 原料清单", "👩🍳 制作步骤"])
        
        with tab_ing:
            if ingredients := recipe_data.get("ingredient"):
                st.markdown('<div class="ingredient-list">', unsafe_allow_html=True)
                for item in ingredients:
                    st.markdown(f"🍴 {item}")
                st.markdown('</div>', unsafe_allow_html=True)
            else:
                st.warning("暂无原料信息")

        with tab_step:
            if steps := recipe_data.get("step"):
                st.markdown('<div class="step-list">', unsafe_allow_html=True)
                for i, step in enumerate(steps, 1):
                    st.markdown(f"{i}. {step}")
                st.markdown('</div>', unsafe_allow_html=True)
            else:
                st.warning("暂无步骤说明")

        st.markdown('</div>', unsafe_allow_html=True)

# 增强版解析逻辑
def parse_response(response_text: str) -> Dict[str, Any]:
    metadata = {
        "recipe_name": "未知菜谱",
        "cook_time": "未注明",
        "difficulty": "未注明",
        "cuisine": "未注明",
        "ingredient": [],
        "step": []
    }

    try:
        # 菜谱名称解析（增强正则匹配）
        name_match = re.search(r"[【《](.+?)[】》]", response_text)
        if name_match:
            metadata["recipe_name"] = name_match.group(1)

        # 元数据解析（时间/难度/菜系）
        meta_pattern = r"^(⏱|时间|🌟|难度|🌍|菜系)[：:]?\s*(.+)$"
        for match in re.finditer(meta_pattern, response_text, re.MULTILINE):
            key, value = match.groups()
            key = key.strip()
            if "时间" in key:
                metadata["cook_time"] = value.strip()
            elif "难度" in key:
                metadata["difficulty"] = value.strip()
            elif "菜系" in key:
                metadata["cuisine"] = value.strip()

        # 原料清单解析（增强格式兼容性）
        ing_section = re.search(
            r"(📝 原料清单|原料|材料)[：:]?\n((?:[-•] .+\n?)+)", 
            response_text
        )
        if ing_section:
            metadata["ingredient"] = [
                line.strip(" -•") 
                for line in ing_section.group(2).split("\n") 
                if line.strip()
            ]

        # 制作步骤解析（支持多种编号格式）
        steps_section = re.search(
            r"(👩🍳 制作步骤|步骤|做法)[：:]?\n((?:\d+[\.．] .+\n?)+)", 
            response_text
        )
        if steps_section:
            metadata["step"] = [
                re.sub(r"^\d+[\.．]\s*", "", line).strip()
                for line in steps_section.group(2).split("\n")
                if line.strip()
            ]

    except Exception as e:
        st.error(f"解析错误: {str(e)}")
    
    return metadata

# 输入处理核心逻辑（增强数据验证）
def handle_user_input(prompt: str):
    try:
        st.session_state.messages.append({"role": "user", "content": prompt})
        
        with st.spinner("🔍 正在分析您的需求..."):
            response = st.session_state.rag_engine.chat(prompt)
            metadata = parse_response(response.response)

            # 关键字段验证
            required_fields = ["recipe_name", "cook_time", "difficulty", "ingredient", "step"]
            if not all(metadata.get(field) for field in required_fields):
                st.warning("⚠️ 信息解析不完整，请尝试重新提问")
                return

            # 构建完整历史记录
            new_history = {
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "query": prompt,
                "recipe_name": metadata["recipe_name"],
                "full_data": {
                    "recipe_name": metadata["recipe_name"],
                    "cook_time": metadata["cook_time"],
                    "difficulty": metadata["difficulty"],
                    "cuisine": metadata.get("cuisine", "未注明"),
                    "ingredient": metadata["ingredient"],
                    "step": metadata["step"]
                }
            }
            
            # 维护历史记录队列
            if len(st.session_state.history) >= MAX_HISTORY:
                st.session_state.history.pop(0)
            st.session_state.history.append(new_history)

            st.session_state.messages.append({
                "role": "assistant",
                "content": response.response
            })
            
        st.rerun()
        
    except Exception as e:
        st.error(f"处理请求时发生错误：{str(e)}")
        st.session_state.messages.append({
            "role": "assistant",
            "content": "😞 系统暂时无法处理您的请求，请稍后再试"
        })

# 历史侧边栏（增强显示）
def history_sidebar():
    with st.sidebar:
        st.header("📜 查询历史")
        if "history" not in st.session_state:
            st.session_state.history = []
        
        if not st.session_state.history:
            st.info("暂无查询记录")
            return
            
        for idx, item in enumerate(reversed(st.session_state.history)):
            with st.expander(f"{item['timestamp']} - {item['recipe_name']}", expanded=False):
                st.markdown(f"""
                <div class="history-item">
                    <p>🗣️ <strong>查询内容</strong>: {item['query']}</p>
                    <p>🕒 <strong>烹饪时间</strong>: {item['full_data']['cook_time']}</p>
                    <p>🌟 <strong>制作难度</strong>: {item['full_data']['difficulty']}</p>
                    <p>🌍 <strong>菜品菜系</strong>: {item['full_data']['cuisine']}</p>
                </div>
                """, unsafe_allow_html=True)
                if st.button("查看完整菜谱", key=f"detail_{idx}"):
                    st.session_state.current_recipe = item['full_data']
                    st.rerun()

# 主界面
def main_interface():
    apply_custom_style()
    
    # 初始化消息历史
    if "messages" not in st.session_state:
        st.session_state.messages = [{
            "role": "assistant",
            "content": "👩🍳 欢迎使用智能菜谱助手！您可以问我：\n- 如何制作意大利面？\n- 推荐简单的中式菜谱\n- 比较不同菜谱的难度"
        }]
    
    history_sidebar()
    
    with st.container():
        col1, _ = st.columns([4, 1])
        
        with col1:
            st.title("👩🍳 智能菜谱助手")
            st.caption("基于RAG技术的智能烹饪解决方案")
            
            # 显示当前菜谱详情
            if "current_recipe" in st.session_state:
                recipe_card(st.session_state.current_recipe)
                if st.button("← 返回对话界面"):
                    del st.session_state.current_recipe
                    st.rerun()
                return
                
            # 显示对话记录
            for msg in st.session_state.messages:
                with st.chat_message(msg["role"]):
                    st.markdown(msg["content"])
                    
            # 用户输入
            if prompt := st.chat_input("请输入您的烹饪问题..."):
                handle_user_input(prompt)

# RAG系统初始化（增强数据生成）
def initialize_rag_system():
    recipe_data = {
        "宫保鸡丁": {
            "ingredient": ["鸡胸肉500g", "花生50g", "干辣椒3个"],
            "step": ["鸡肉切丁腌制15分钟", "热油爆香辣椒和花椒", "加入鸡丁翻炒至变色", "最后加入花生快炒"],
            "metadata": {
                "cuisine": "川菜",
                "cook_time": "25分钟",
                "difficulty": "中等"
            }
        },
        "番茄意面": {
            "ingredient": ["意大利面200g", "番茄2个", "橄榄油30ml"],
            "step": ["煮面8-10分钟", "番茄切丁炒制酱汁", "混合面条与酱汁"],
            "metadata": {
                "cuisine": "意大利",
                "cook_time": "20分钟",
                "difficulty": "简单"
            }
        }
    }

    def create_documents(data):
        docs = []
        for name, details in data.items():
            text = f"""
            【{name}】
            ⏱ 时间：{details['metadata']['cook_time']}
            🌟 难度：{details['metadata']['difficulty']}
            🌍 菜系：{details['metadata']['cuisine']}
            
            📝 原料清单：
            {chr(10).join(["- " + i for i in details['ingredient']])}
            
            👩🍳 制作步骤：
            {chr(10).join([f"{i+1}. {s}" for i, s in enumerate(details['step'])])}
            """
            docs.append(Document(
                text=text,
                metadata={"recipe_name": name, **details["metadata"]}
            ))
        return docs

    Settings.llm = Ollama(model="qwen:7b", request_timeout=600.0)
    Settings.embed_model = OllamaEmbedding(model_name="nomic-embed-text")
    
    return VectorStoreIndex.from_documents(
        create_documents(recipe_data)
    ).as_chat_engine(
        chat_mode="condense_plus_context",
        memory=ChatMemoryBuffer.from_defaults(token_limit=4096),
        system_prompt=SYSTEM_PROMPT
    )

if __name__ == "__main__":
    if "rag_engine" not in st.session_state:
        st.session_state.rag_engine = initialize_rag_system()
    
    main_interface()

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

# Initialize async environment
nest_asyncio.apply()

# App configuration
st.set_page_config(
    page_title="AI Recipe Assistant",
    page_icon="👩🍳",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Constants
MAX_HISTORY = 10
SYSTEM_PROMPT = """Please respond strictly in the following format:
【Recipe Name】
⏱ Time: xx mins
🌟 Difficulty: Easy/Medium/Hard
🌍 Cuisine: xx Cuisine

📝 Ingredients:
- Ingredient1 (quantity)
- Ingredient2 (quantity)

👩🍳 Steps:
1. Step description
2. Step description

💡 Tips:
- Useful tip1
- Useful tip2

Requirements:
1. Recipe name must be wrapped in Chinese brackets【】
2. Time, difficulty and cuisine must be listed under the name
3. Ingredients and steps must use list format"""

# Style configuration
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

# Recipe card component
def recipe_card(recipe_data: Dict[str, Any]):
    with st.container():
        st.markdown('<div class="recipe-card">', unsafe_allow_html=True)
        
        # Header
        st.subheader(f"🍳 {recipe_data.get('recipe_name', 'Unknown Recipe')}")
        cols = st.columns(3)
        with cols[0]:
            st.metric("⏱ Cooking Time", recipe_data.get("cook_time", "N/A"))
        with cols[1]:
            st.metric("🌟 Difficulty", recipe_data.get("difficulty", "N/A"))
        with cols[2]:
            st.metric("🌍 Cuisine", recipe_data.get("cuisine", "N/A"))

        # Tabs
        tab_ing, tab_step = st.tabs(["📦 Ingredients", "👩🍳 Steps"])
        
        with tab_ing:
            if ingredients := recipe_data.get("ingredient"):
                st.markdown('<div class="ingredient-list">', unsafe_allow_html=True)
                for item in ingredients:
                    st.markdown(f"🍴 {item}")
                st.markdown('</div>', unsafe_allow_html=True)
            else:
                st.warning("No ingredients available")

        with tab_step:
            if steps := recipe_data.get("step"):
                st.markdown('<div class="step-list">', unsafe_allow_html=True)
                for i, step in enumerate(steps, 1):
                    st.markdown(f"{i}. {step}")
                st.markdown('</div>', unsafe_allow_html=True)
            else:
                st.warning("No steps available")

        st.markdown('</div>', unsafe_allow_html=True)

# Enhanced parsing logic
def parse_response(response_text: str) -> Dict[str, Any]:
    metadata = {
        "recipe_name": "Unknown Recipe",
        "cook_time": "N/A",
        "difficulty": "N/A",
        "cuisine": "N/A",
        "ingredient": [],
        "step": []
    }

    try:
        # Name parsing
        name_match = re.search(r"[【《](.+?)[】》]", response_text)
        if name_match:
            metadata["recipe_name"] = name_match.group(1)

        # Metadata parsing
        meta_pattern = r"^(⏱|Time|🌟|Difficulty|🌍|Cuisine)[：:]?\s*(.+)$"
        for match in re.finditer(meta_pattern, response_text, re.MULTILINE):
            key, value = match.groups()
            key = key.strip()
            if "Time" in key:
                metadata["cook_time"] = value.strip()
            elif "Difficulty" in key:
                metadata["difficulty"] = value.strip()
            elif "Cuisine" in key:
                metadata["cuisine"] = value.strip()

        # Ingredients parsing
        ing_section = re.search(
            r"(📝 Ingredients|Ingredients|Materials)[：:]?\n((?:[-•] .+\n?)+)", 
            response_text
        )
        if ing_section:
            metadata["ingredient"] = [
                line.strip(" -•") 
                for line in ing_section.group(2).split("\n") 
                if line.strip()
            ]

        # Steps parsing
        steps_section = re.search(
            r"(👩🍳 Steps|Steps|Instructions)[：:]?\n((?:\d+[\.．] .+\n?)+)", 
            response_text
        )
        if steps_section:
            metadata["step"] = [
                re.sub(r"^\d+[\.．]\s*", "", line).strip()
                for line in steps_section.group(2).split("\n")
                if line.strip()
            ]

    except Exception as e:
        st.error(f"Parsing error: {str(e)}")
    
    return metadata

# Input handling
def handle_user_input(prompt: str):
    try:
        st.session_state.messages.append({"role": "user", "content": prompt})
        
        with st.spinner("🔍 Analyzing your request..."):
            response = st.session_state.rag_engine.chat(prompt)
            metadata = parse_response(response.response)

            # Validation
            required_fields = ["recipe_name", "cook_time", "difficulty", "ingredient", "step"]
            if not all(metadata.get(field) for field in required_fields):
                st.warning("⚠️ Incomplete information, please rephrase your question")
                return

            # Maintain history
            new_history = {
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "query": prompt,
                "recipe_name": metadata["recipe_name"],
                "full_data": {
                    "recipe_name": metadata["recipe_name"],
                    "cook_time": metadata["cook_time"],
                    "difficulty": metadata["difficulty"],
                    "cuisine": metadata.get("cuisine", "N/A"),
                    "ingredient": metadata["ingredient"],
                    "step": metadata["step"]
                }
            }
            
            if len(st.session_state.history) >= MAX_HISTORY:
                st.session_state.history.pop(0)
            st.session_state.history.append(new_history)

            st.session_state.messages.append({
                "role": "assistant",
                "content": response.response
            })
            
        st.rerun()
        
    except Exception as e:
        st.error(f"Error processing request: {str(e)}")
        st.session_state.messages.append({
            "role": "assistant",
            "content": "😞 System temporarily unavailable, please try again later"
        })

# History sidebar
def history_sidebar():
    with st.sidebar:
        st.header("📜 Query History")
        if "history" not in st.session_state:
            st.session_state.history = []
        
        if not st.session_state.history:
            st.info("No query history")
            return
            
        for idx, item in enumerate(reversed(st.session_state.history)):
            with st.expander(f"{item['timestamp']} - {item['recipe_name']}", expanded=False):
                st.markdown(f"""
                <div class="history-item">
                    <p>🗣️ <strong>Query</strong>: {item['query']}</p>
                    <p>🕒 <strong>Time</strong>: {item['full_data']['cook_time']}</p>
                    <p>🌟 <strong>Difficulty</strong>: {item['full_data']['difficulty']}</p>
                    <p>🌍 <strong>Cuisine</strong>: {item['full_data']['cuisine']}</p>
                </div>
                """, unsafe_allow_html=True)
                if st.button("View Full Recipe", key=f"detail_{idx}"):
                    st.session_state.current_recipe = item['full_data']
                    st.rerun()

# Main interface
def main_interface():
    apply_custom_style()
    
    # Initialize message history
    if "messages" not in st.session_state:
        st.session_state.messages = [{
            "role": "assistant",
            "content": "👩🍳 Welcome to AI Recipe Assistant! Ask me:\n- How to make spaghetti?\n- Recommend easy Chinese recipes\n- Compare recipe difficulties"
        }]
    
    history_sidebar()
    
    with st.container():
        col1, _ = st.columns([4, 1])
        
        with col1:
            st.title("👩🍳 AI Recipe Assistant")
            st.caption("Smart cooking solution powered by RAG")
            
            # Current recipe view
            if "current_recipe" in st.session_state:
                recipe_card(st.session_state.current_recipe)
                if st.button("← Back to Chat"):
                    del st.session_state.current_recipe
                    st.rerun()
                return
                
            # Chat history
            for msg in st.session_state.messages:
                with st.chat_message(msg["role"]):
                    st.markdown(msg["content"])
                    
            # User input
            if prompt := st.chat_input("Enter your cooking question..."):
                handle_user_input(prompt)

# RAG system initialization
def initialize_rag_system():
    recipe_data = {
        "Kung Pao Chicken": {
            "ingredient": ["500g chicken", "50g peanuts", "3 dried chilies"],
            "step": ["Marinate chicken", "Stir-fry chilies", "Add peanuts"],
            "metadata": {
                "cuisine": "Chinese",
                "cook_time": "30 mins",
                "difficulty": "Medium"
            }
        },
        "Pasta": {
            "ingredient": ["200g pasta", "2 cloves garlic", "100ml olive oil"],
            "step": ["Boil pasta 8 mins", "Chop garlic", "Fry garlic", "Mix all"],
            "metadata": {
                "cuisine": "Italian",
                "cook_time": "20 mins",
                "difficulty": "Easy"
            }
        }
    }

    def create_documents(data):
        docs = []
        for name, details in data.items():
            text = f"""
            【{name}】
            ⏱ Time: {details['metadata']['cook_time']}
            🌟 Difficulty: {details['metadata']['difficulty']}
            🌍 Cuisine: {details['metadata']['cuisine']}
            
            📝 Ingredients:
            {chr(10).join(["- " + i for i in details['ingredient']])}
            
            👩🍳 Steps:
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

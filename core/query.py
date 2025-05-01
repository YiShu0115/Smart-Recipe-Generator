from llama_index.core import Settings
from llama_index.core.chat_engine import CondenseQuestionChatEngine
from llama_index.core.query_engine import RetrieverQueryEngine
from llama_index.core.memory import ChatMemoryBuffer
from llama_index.core.vector_stores import MetadataFilter, MetadataFilters
from llama_index.core import get_response_synthesizer
from sklearn.metrics.pairwise import cosine_similarity

from typing import List

# 单轮简单查询
def query_answer(query: str, index) -> str:
    query_engine = index.as_query_engine()
    response = query_engine.query(query)
    return str(response)

# 多轮对话（带记忆）
def init_chat_engine(index):
    memory = ChatMemoryBuffer.from_defaults(token_limit=3900)
    chat_engine = index.as_chat_engine(
        chat_mode="condense_plus_context",
        memory=memory,
        system_prompt=(
            "您是一位专业厨师助手，请根据菜谱数据库回答用户问题。\n"
            "回答时请：\n"
            "1. 明确说明菜谱名称\n"
            "2. 分步骤说明制作方法\n"
            "3. 给出烹饪小贴士\n"
            "4. 主动询问是否需要补充信息"
        )
    )
    return chat_engine

def chat_turn(query: str, chat_engine) -> str:
    response = chat_engine.chat(query)
    return str(response)

# 关键词匹配检索（需要自己实现 get_keywords_from_llama）
def keyword_based_answer(query: str, index, get_keywords_from_llama_fn) -> str:
    keywords = get_keywords_from_llama_fn(query)
    
    filters_list = [
        MetadataFilter(key="excerpt_keywords", value=k, operator="contains")
        for k in keywords
    ]
    filters = MetadataFilters(filters=filters_list)
    
    retriever = index.as_retriever(filters=filters)
    synthesizer = get_response_synthesizer(response_mode="compact")
    
    query_engine = RetrieverQueryEngine(
        retriever=retriever, 
        response_synthesizer=synthesizer
    )
    
    response = query_engine.query(query)
    return str(response)


# 从输入食材推荐相关菜谱
def suggest_recipes_by_query(query: str, index, model: str = "tinyllama:1.1b", top_k=3) -> str:
    """
    根据用户自然语言问题提取关键词，并根据食材推荐匹配的菜谱。
    """
    from core.utils import get_keywords_from_llama  # 如果已经导入可删掉

    # 1. 提取关键词作为食材
    ingredients = get_keywords_from_llama(query, model=model)
    if not ingredients:
        return "Failed to extract keywords from the input."

    print(f"[INFO] Extracted ingredients: {ingredients}")

    # 2. 使用原先逻辑匹配菜谱
    docstore = index.storage_context.docstore
    nodes = list(docstore.docs.values())

    matches = []
    for node in nodes:
        recipe_name = node.metadata.get("recipe_name", "Unknown")
        if "Ingredients:" in node.text and "Steps:" in node.text:
            ingredients_section = node.text.split("Ingredients:")[1].split("Steps:")[0]
            score = sum(1 for ing in ingredients if ing.lower() in ingredients_section.lower())
            if score > 0:
                matches.append((recipe_name, score))

    matches.sort(key=lambda x: x[1], reverse=True)

    result_descriptions = [
        f"- Suggested recipe: {name} (matched ingredients: {score})"
        for name, score in matches[:top_k]
    ]
    return "\n".join(result_descriptions) if result_descriptions else "No matching recipes found."




# 找与某道菜相似的其它菜
def find_similar_recipes(target_name, index, embed_model, top_k=3):
    docstore = index.storage_context.docstore
    nodes = list(docstore.docs.values())

    target_node = next((n for n in nodes if n.metadata.get("recipe_name") == target_name), None)
    if not target_node:
        return f"No recipe found with the name '{target_name}'."

    target_vec = embed_model._get_text_embedding(target_node.text)
    all_vecs = [embed_model._get_text_embedding(n.text) for n in nodes]
    scores = cosine_similarity([target_vec], all_vecs)[0]

    sorted_results = sorted(zip(nodes, scores), key=lambda x: x[1], reverse=True)
    similar_list = [
        f"- Similar recipe: {n.metadata['recipe_name']} (similarity score: {s:.2f})"
        for n, s in sorted_results[1:top_k+1]
    ]
    return "\n".join(similar_list) if similar_list else "No similar recipes found."



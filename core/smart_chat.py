from core.utils import get_keywords_from_llama, extract_number_from_text
from core.query import suggest_recipes_by_ingredients, find_similar_recipes
from core.utils import scale_ingredients, get_last_mentioned_recipe
from llama_index.core import Settings
from ollama import Ollama

# 初始化一个轻量问答判断模型（也可以用 Settings.llm）
llm_router = Ollama(model="tinyllama:1.1b", request_timeout=300.0)

def classify_query(query: str) -> str:
    """使用 LLM 判断 query 类型：recommend, similar, scale, chat"""
    prompt = (
        f"You are a smart assistant. Classify the user's question into one of the categories:\n"
        f"- recommend (if user wants recipe suggestions based on ingredients or keywords)\n"
        f"- similar (if user wants similar dishes)\n"
        f"- scale (if user asks about changing servings or quantities)\n"
        f"- chat (default for everything else)\n\n"
        f"User question: {query}\n"
        f"Answer format: label: <category>"
    )
    response = llm_router.complete(prompt).text.strip().lower()
    if "recommend" in response:
        return "recommend"
    if "similar" in response:
        return "similar"
    if "scale" in response:
        return "scale"
    return "chat"

def smart_chat_turn(query: str, chat_engine, index, embed_model) -> str:
    label = classify_query(query)
    
    if label == "recommend":
        keywords = get_keywords_from_llama(query)
        response = suggest_recipes_by_ingredients(keywords, index)
        return f"Based on your input, here are some suggested recipes:\n{response}"
    
    if label == "similar":
        target = query.lower().split("similar to")[-1].strip()
        results = find_similar_recipes(target, index, embed_model)
        if results:
            return "Here are some dishes similar to what you mentioned:\n" + "\n".join(
                f"- {name} (similarity: {score:.2f})" for name, score in results
            )
        else:
            return "Sorry, I couldn't find any similar recipes."
    
    if label == "scale":
        scale_by = extract_number_from_text(query)
        recipe_id = get_last_mentioned_recipe(chat_engine.memory)
        if recipe_id and scale_by:
            doc = index.storage_context.docstore.docs.get(recipe_id)
            ingredients = doc.text.split("Ingredients:")[1].split("Steps:")[0].split("\n")
            scaled = scale_ingredients(ingredients, scale_by)
            return f"Here are the adjusted ingredients for {scale_by}x servings:\n" + "\n".join(scaled)
        return "I couldn't determine which recipe or scale factor you meant."

    return str(chat_engine.chat(query))

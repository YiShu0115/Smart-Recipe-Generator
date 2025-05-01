# core/utils.py

from llama_index.llms.ollama import Ollama
from fractions import Fraction
import re
import re
from llama_index.core.memory import ChatMemoryBuffer

def extract_number_from_text(text):
    match = re.search(r"\d+", text)
    return int(match.group()) if match else None

def get_last_mentioned_recipe(memory: ChatMemoryBuffer) -> str:
    for msg in reversed(memory.get_all()):
        if 'recipe_name' in msg.additional_kwargs:
            return msg.additional_kwargs['recipe_name']
    return None

# 用 Ollama 模型提取关键词（最多3个关键词）
def get_keywords_from_llama(query: str, model="tinyllama:1.1b") -> list:
    import re

    llm = Ollama(model=model, request_timeout=600.0)

    system_prompt = (
        f"Extract at most 3 keywords from this input: \"{query}\"\n"
        f"Return in this format: Keywords: keyword1, keyword2, keyword3"
    )

    response = llm.complete(system_prompt).text.strip()
    print("[DEBUG] Raw response:", response)

    # 提取关键词部分
    match = re.search(r"[Kk]eywords?\s*[:：]?\s*(.*)", response)
    if not match:
        print("[WARN] No keywords found.")
        return []

    keyword_str = match.group(1)
    raw_keywords = [k.strip() for k in keyword_str.split(',') if k.strip()]

    # 强化过滤：最多3个，每个最多3个英文单词
    final_keywords = []
    for kw in raw_keywords:
        if len(kw.split()) <= 3:
            final_keywords.append(kw)
        if len(final_keywords) == 3:
            break

    return final_keywords



# 把字符串每两个中文或英文字符切分一组
def split_into_pairs(text: str) -> list:
    pairs = []
    length = len(text)
    for i in range(0, length, 2):
        pairs.append(text[i:i+2])
    return pairs

# 缩放配料数量（假设配料是纯文本list）
def scale_ingredients(ingredients: list, scale_by: float) -> list:
    scaled_ingredients = []
    for line in ingredients:
        numbers = re.findall(r"\d+\/\d+|\d+\.\d+|\d+", line)  # 找到所有数字或分数
        if numbers:
            for num in numbers:
                try:
                    value = float(Fraction(num))
                    scaled_value = round(value * scale_by, 2)
                    line = line.replace(num, str(scaled_value), 1)
                except Exception:
                    continue
        scaled_ingredients.append(line)
    return scaled_ingredients

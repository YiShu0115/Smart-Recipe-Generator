# main.py
import json
import nest_asyncio
from core.embedding import get_embed_model
from core.prepare import prepare_documents, build_index
from llama_index.core import Settings
from llama_index.llms.ollama import Ollama

def init_index_from_json(json_path: str):
    nest_asyncio.apply()

    with open(json_path, 'r', encoding='utf-8') as f:
        recipe_data = json.load(f)

    Settings.llm = Ollama(model="qwen:7b", request_timeout=600.0)
    Settings.embed_model = get_embed_model("nomic-embed-text")
    Settings.chunk_size = 1024

    documents = prepare_documents(recipe_data)
    index = build_index(documents)
    return index

if __name__ == "__main__":
    index = init_index_from_json("sample.json")
    print("begin!")

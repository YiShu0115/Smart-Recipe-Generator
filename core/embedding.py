# core/embedding.py
from llama_index.embeddings.ollama import OllamaEmbedding

def get_embed_model(model_name: str = "nomic-embed-text"):
    return OllamaEmbedding(model_name=model_name)

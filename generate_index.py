import json
import time
from tqdm import tqdm
from llama_index.core import Settings, VectorStoreIndex, StorageContext
from llama_index.llms.ollama import Ollama
from core.prepare import prepare_documents
from core.embedding import get_embed_model

# 初始化模型
print("Initializing models...")
Settings.llm = Ollama(model="qwen:7b", request_timeout=600.0)
Settings.embed_model = get_embed_model("nomic-embed-text")
Settings.chunk_size = 1024

# 加载数据
print("Loading recipe data...")
with open("data/recipe.json", 'r', encoding='utf-8') as f:
    recipe_data = json.load(f)
print(f"Loaded {len(recipe_data)} recipes")

# 准备文档并构建索引
print("Preparing documents...")
# 使用tqdm显示文档准备的进度
documents = []
with tqdm(total=len(recipe_data), desc="Processing recipes") as pbar:
    for i, (name, details) in enumerate(recipe_data.items()):
        doc = prepare_documents({name: details})[0]  # 一次处理一个食谱
        documents.append(doc)
        pbar.update(1)
        
        # 每处理10个食谱显示一次进度
        if (i+1) % 100 == 0:
            print(f"Processed {i+1}/{len(recipe_data)} recipes")

# 创建并保存索引
print("\nBuilding index (this may take a while)...")
# 标记开始时间
start_time = time.time()

# 使用LlamaIndex构建索引
print("Vectorizing documents and building index structure...")
index = VectorStoreIndex.from_documents(documents)

# 显示完成时间
elapsed = time.time() - start_time
print(f"Index built in {elapsed:.2f} seconds")

# 保存索引到磁盘
print("Saving index to disk...")
index.storage_context.persist("./data/index_storage")

print("Index generated and saved successfully!")

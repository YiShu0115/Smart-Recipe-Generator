# core/prepare.py
from llama_index.core import Document, VectorStoreIndex
from llama_index.core.ingestion import IngestionPipeline
from llama_index.core.node_parser import TokenTextSplitter
from llama_index.core.extractors import TitleExtractor, KeywordExtractor
from typing import List, Dict

def prepare_documents(recipe_data: Dict) -> List[Document]:
    docs = []
    for name, details in recipe_data.items():
        text = f"""Recipe: {name}

Level: {details.get('level', '-')}
Total Time: {details.get('total_time', '-')}
Prep Time: {details.get('prep_time', '-')}
Cook Time: {details.get('cook_time', '-')}
Servings: {details.get('servings', '-')}

Ingredients:
{', '.join(details.get('ingredient', []))}

Steps:
{' '.join(details.get('step', []))}
"""
        docs.append(Document(text=text.strip(), metadata={"recipe_name": name}))
    return docs

def build_index(docs: List[Document]) -> VectorStoreIndex:
    text_splitter = TokenTextSplitter(separator=" ", chunk_size=512, chunk_overlap=20)
    title_extractor = TitleExtractor(nodes=5)
    keyword_extractor = KeywordExtractor(keywords=5)

    pipeline = IngestionPipeline(transformations=[
        text_splitter, title_extractor, keyword_extractor
    ])
    
    nodes = pipeline.run(documents=docs)
    print(f"[INFO] Ingestion 完成，生成 {len(nodes)} 个节点")

    index = VectorStoreIndex(nodes)
    return index

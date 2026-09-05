from imports.AI_models import embeddings
from langchain_chroma import Chroma

vector_store = Chroma(
    collection_name="sample_collection",
    embedding_function=embeddings,
    persist_directory="./vector_DB/docs_v20",
)


from langchain_chroma import Chroma

from imports.AI_models import get_embeddings_model
from imports.config import CHROMA_DIR

# APP_DATA = Path(os.getenv("LOCALAPPDATA", Path.home())) / "MyRAGApp"
# CHROMA_DIR = APP_DATA / "chroma"
# CHROMA_DIR.mkdir(parents=True, exist_ok=True)

def get_vector_Store():
    embeddings = get_embeddings_model()

    vector_store = Chroma(
        collection_name="sample_collection",
        embedding_function=embeddings,
        persist_directory = str(CHROMA_DIR),
    )

    return vector_store

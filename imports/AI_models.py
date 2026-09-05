from langchain.chat_models import init_chat_model
from faster_whisper import WhisperModel
from langchain_ollama import OllamaEmbeddings
from langchain_ollama import ChatOllama

vision_model = ChatOllama(
    model="qwen3-vl:2b",
    model_kwargs={
            "num_predict": 800
        }
)

embeddings = OllamaEmbeddings(
                model='nomic-embed-text:v1.5'
            )

llm = init_chat_model(model="qwen2.5:3b", model_provider='ollama')

whisper_model = WhisperModel(
    "base",
    device="cpu",
    compute_type="int8"
)




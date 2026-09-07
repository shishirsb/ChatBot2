from langchain.chat_models import init_chat_model
from faster_whisper import WhisperModel
from langchain_ollama import OllamaEmbeddings
from langchain_ollama import ChatOllama
from langchain_openai import ChatOpenAI
from langchain_openai import OpenAIEmbeddings


# vision_model = ChatOllama(
#     model="qwen3-vl:2b",
#     model_kwargs={
#             "num_predict": 800
#         }
# )



# embeddings = OllamaEmbeddings(
#                 model='nomic-embed-text:v1.5'
#             )

embeddings = OpenAIEmbeddings(
    model="text-embedding-3-small",
    chunk_size=256
    # With the `text-embedding-3` class
    # of models, you can specify the size
    # of the embeddings you want returned.
    # dimensions=1024
)

# llm = init_chat_model(model="qwen2.5:3b", model_provider='ollama')
llm = ChatOpenAI(
    model='gpt-4o-mini',
    # model="gpt-5-nano",
    # stream_usage=True,
    # temperature=None,
    # max_tokens=None,
    # timeout=None,
    # reasoning_effort="low",
    # max_retries=2,
    # api_key="...",  # If you prefer to pass api key in directly
    # base_url="...",
    # organization="...",
    # other params...
)

whisper_model = WhisperModel(
    "base",
    device="cpu",
    compute_type="int8"
)




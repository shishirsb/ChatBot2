
from langchain_openai import ChatOpenAI
from langchain_openai import OpenAIEmbeddings
import os
import keyring
from imports.config import SERVICE_NAME, USERNAME


def get_embeddings_model():

    # Retrieve
    api_key = keyring.get_password(
        SERVICE_NAME,
        USERNAME
    )

    try:
        embeddings = OpenAIEmbeddings(
            model="text-embedding-3-small",
            chunk_size=256,
            api_key=api_key
            # With the `text-embedding-3` class
            # of models, you can specify the size
            # of the embeddings you want returned.
            # dimensions=1024
        )

        return embeddings
    except Exception as e:
        print(e)



# llm = init_chat_model(model="qwen2.5:3b", model_provider='ollama')
def get_llm():
    # Retrieve
    api_key = keyring.get_password(
        SERVICE_NAME,
        USERNAME
    )

    llm = ChatOpenAI(
        model='gpt-4o-mini',
        api_key=api_key,
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

    return llm



# whisper_model = WhisperModel(
#     "base",
# device="cpu",
# compute_type="int8"
# )
#
#

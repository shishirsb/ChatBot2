

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
import gradio as gr
from langsmith import traceable
from dotenv import load_dotenv
from imports.AI_models import get_llm
from .format_docs import format_docs
from .format_sources import format_sources
from imports.vector_store import get_vector_Store
from pathlib import Path

print('Finished imports')
load_dotenv()


def get_retriever():
    vector_store = get_vector_Store()
    retriever = vector_store.as_retriever(search_type='similarity', search_kwargs={'k': 2})
    return retriever


prompt_template_RAG = ChatPromptTemplate.from_template(
    """You are a question-answering assistant.

Answer the QUESTION using ONLY the information contained in the CONTEXT.

IMPORTANT RULES:

1. Answer only what is asked in the QUESTION.

2. Use only information explicitly supported by the CONTEXT.
   Do not use outside knowledge, assumptions, or speculation.

3. Give priority to information that directly answers the QUESTION.

4. Do NOT include information merely because it is related to the
   same product, topic, or subject.

5. If the QUESTION asks about a specific category, section, attribute,
   or list, answer using information belonging specifically to that
   category or section.

   For example, if the QUESTION asks for "features", do not include
   construction details, applications, specifications, operating
   procedures, or other product information unless the CONTEXT
   explicitly presents them as features.

6. Preserve the terminology and wording of the CONTEXT wherever
   practical, especially for lists, specifications, product features,
   names, and technical terms.

7. If the CONTEXT contains a clearly identified heading or section
   corresponding to the QUESTION, prefer information from that section.

8. Do not combine information from different products, documents,
   or unrelated sections unless the QUESTION explicitly requires
   such a comparison or combination.

9. If the QUESTION asks for a list, provide the items in the list
   rather than converting them into a general product summary.

10. If the CONTEXT does not contain enough information to answer the
    QUESTION, say so. Do not fill the missing information using
    outside knowledge.

CONTEXT:
{context}

QUESTION:
{question}

ANSWER:
""", )



print('defining chain')

def get_rag_chain():
    llm = get_llm()
    rag_chain = (
            prompt_template_RAG | llm | StrOutputParser()
    )
    return rag_chain




@traceable(name='Ask a question', run_type='chain')
def process_query(question, history):
    try:
        source_paths = []
        yield history, '', gr.update(
                            visible=False,
                            value=source_paths
                            )
        if history is None:
            history = []

        history.append({
            "role": "user",
            "content": question
        })


        history.append({
            "role": "assistant",
            "content": "Thinking..."
        })

        yield history, '', gr.update(
                            visible=False,
                            value=source_paths
                            )
        retriever = get_retriever()
        retrieved_docs = retriever.invoke(question)


        seen = set()

        for doc in retrieved_docs:
            source = doc.metadata.get("source")

            if not source:
                continue

            source = str(source)

            # Don't put web URLs into gr.File
            if source.startswith(("http://", "https://")):
                continue

            source = str(Path(source).resolve())

            if source not in seen:
                seen.add(source)
                source_paths.append(source)

        context = format_docs(retrieved_docs)

        answer = ""
        rag_chain = get_rag_chain()

        for chunk in rag_chain.stream({
            "context": context,
            "question": question
        }):
            answer += chunk
            history[-1]["content"] = answer
            yield history, '', gr.update(
                            visible=False,
                            value=source_paths
                            )

        # Now display sources
        sources = format_sources(retrieved_docs)

        source_text = ""

        for source in sources:
            source_text += source + "\n"

            history[-1]["content"] = (
                    answer
                    + "\n\n"
                    + source_text
            )

            yield history, '', gr.update(
            visible=True,
            value=source_paths
            )
    except Exception as e:
        print(f"Error in process_query: {e}")

        if history:
            history[-1]["content"] = "Please set your API key under Settings."

        yield history, '', gr.update(
            visible=False,
            value=source_paths
        )




def send_text(message, history):
    yield from process_query(message, history)


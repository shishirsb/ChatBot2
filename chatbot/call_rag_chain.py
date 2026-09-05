

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
import gradio as gr
from langsmith import traceable
from dotenv import load_dotenv
from imports.AI_models import llm
from .format_docs import format_docs
from .format_sources import format_sources
from speech_recording.transcribe_and_summarize import transcribe
from imports.vector_store import vector_store
from pathlib import Path

print('Finished imports')
load_dotenv()


retriever = vector_store.as_retriever(search_type='similarity', search_kwargs={'k': 10})

prompt_template_RAG = ChatPromptTemplate.from_template(
    """You are a question-answering assistant.

Answer the QUESTION using only information contained in the CONTEXT.

Your goal is to provide a detailed, well-explained answer to the QUESTION,
while staying strictly within the information available in the CONTEXT.

IMPORTANT RULES:

1. Answer only the QUESTION. Do not provide a general summary of the CONTEXT.

2. Use only information supported by the CONTEXT. Do not use outside knowledge,
   assumptions, or speculation.

3. Identify all information in the CONTEXT that is directly relevant to answering
   the QUESTION.

4. Explain the relevant information sufficiently so that the answer is clear and
   easy to understand. Do not merely state isolated facts.

5. Include relevant supporting details, explanations, examples, reasons,
   relationships, causes, consequences, or qualifications from the CONTEXT
   when they help provide a complete answer.

6. Do not omit important details simply to keep the answer short.

7. At the same time, do not include information from the CONTEXT that is unrelated
   to the QUESTION, even if it is interesting or relevant to a broader topic.

8. If the QUESTION asks "why" or "how", explain the reasoning or process described
   in the CONTEXT rather than giving only the final conclusion.

9. If the QUESTION asks for a comparison, explain the relevant differences and
   similarities found in the CONTEXT.

10. If the QUESTION asks about a specific fact, answer that fact directly and then
    provide the relevant supporting explanation from the CONTEXT.

11. If the CONTEXT contains insufficient information to answer the QUESTION,
    clearly state what information is available and what cannot be determined.

12. The desired level of detail is: thorough enough to fully explain the answer,
    but never a summary of unrelated context.

CONTEXT:
{context}

QUESTION:
{question}

ANSWER:
""", )



print('defining chain')

rag_chain = (
        prompt_template_RAG | llm | StrOutputParser()
)




@traceable(name='Ask a question', run_type='chain')
def process_query(question, history):
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






def send_text(message, history):
    yield from process_query(message, history)



# def send_audio(audio_path, history):
#     if audio_path is None:
#         yield "", history or []
#         return
#     question = transcribe(audio_path)
#
#     if not question.strip():
#         yield "", history or []
#         return
#
#     answer_history = history or []
#
#     for updated_history in process_query(question, answer_history):
#         yield question, updated_history


from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from imports.AI_models import whisper_model
from imports.AI_models import llm


summary_prompt = ChatPromptTemplate.from_template(
"""Rewrite the transcript into detailed, structured notes.

Preserve all meaningful information from the transcript. Do not produce a high-level summary.

- Include all topics, explanations, questions, answers, arguments, examples, opinions, and conclusions.
- Do not omit meaningful details.
- Do not combine distinct points merely to make the output shorter.
- Remove only filler words, false starts, and exact repetitions.
- Do not add information that is not present in the transcript.
- Organize the content using Markdown headings and bullet points.
- Use nested bullets where appropriate.
- Keep the wording clear and readable while preserving the substance.

IMPORTANT:
- If the transcript is empty or blank, output exactly:
  No transcript available.
- Do not invent, assume, or create any content that is not present in the transcript.

Formatting requirements:
- Output Markdown directly.
- Do NOT wrap the response in a Markdown code block.
- Do NOT use ```markdown or ``` anywhere in the response.
- Markdown headings must use #, ##, or ### directly.
- Use **bold** only for important terms or phrases.
- Do not escape Markdown characters such as *, _, or # with backslashes.

Transcript:
{transcript}"""
)


summary_chain = (
    summary_prompt
    | llm
    | StrOutputParser()
)


def transcribe(audio_path, language):
    if audio_path is None:
        return ""
    segments, info = whisper_model.transcribe(
        audio_path,
        language=language,
        task="translate",
        vad_filter=True,
        )
    return " ".join(
        segment.text.strip()
        for segment in segments
    )

def summarize(transcript):
    print("=== SUMMARIZE ===")
    print("Length:", len(transcript))
    print("Content:", repr(transcript))

    if not transcript or not transcript.strip():
        print("!!! EMPTY TRANSCRIPT SENT TO LLM !!!")
        return

    for chunk in summary_chain.stream({
        "transcript": transcript
    }):
        yield chunk




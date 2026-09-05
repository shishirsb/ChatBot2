import gradio as gr
from ui import speech_recording
from ui.knowledge_base import knowledge_base_accordion
from ui.speech_recording import speech_recording
from ui.chatbot import chat_ui


def create_ui():
    print('Defining gradio blocks')
    with gr.Blocks() as demo:
        chat_ui()
        speech_recording()
        knowledge_base_accordion()

    return demo
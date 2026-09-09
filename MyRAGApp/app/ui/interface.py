import gradio as gr
from ui.knowledge_base import knowledge_base_accordion
from ui.chatbot import chat_ui
from ui.settings import settings_accordion



def create_ui():
    print('Defining gradio blocks')
    with gr.Blocks() as demo:
        chat_ui()
        # speech_recording()
        knowledge_base_accordion()
        settings_accordion()

    return demo
import gradio as gr
from knowledge_base.load_docs import Loader

def knowledge_base_accordion():
    loader = Loader()
    with gr.Accordion("Knowledge Base", open=False) as kb_accordion:
        files = gr.File(
            file_count="multiple",
            file_types=[".pdf", '.txt', '.pptx', '.docx', '.jpg']
        )
        url = gr.Textbox(
            label="Website URL"
        )
        load_btn = gr.Button("Load Documents")
        kb_status = gr.Textbox(label="Status")

        load_btn.click(
            fn=loader.load_documents,
            inputs=[files, url],
            outputs=kb_status
        )
    return kb_accordion, files, url, load_btn, kb_status
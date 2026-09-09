
import gradio as gr
from imports.set_api_key import set_api_key


def settings_accordion():
    with gr.Accordion("Settings", open=False) as settings_accordion:

        # Text box
        api_key_input_box = gr.Textbox(
            label="API Key",
            placeholder="Enter your API Key",
        )

        set_api_key_btn = gr.Button("Set API Key")

        set_api_key_status = gr.Textbox(label="Status")

        set_api_key_btn.click(
            fn=set_api_key,
            inputs=[api_key_input_box],
            outputs=[set_api_key_status, api_key_input_box]
        )




    return settings_accordion
from chatbot.call_rag_chain import send_text
import gradio as gr

def chat_ui():
    with gr.Group(visible=True):
        gr.Markdown('# AI Chatbot')
        chatbot = gr.Chatbot(
                    height=500
                )

        source_files = gr.File(
            label="Source Files",
            file_count="multiple",
            visible=False,
            height=120
        )

        chat_input_box = gr.Textbox(
            show_label=False,
            placeholder="Ask a question..."
        )


        chat_input_box.submit(
            fn=send_text,
            inputs=[chat_input_box, chatbot],
            outputs=[chatbot, chat_input_box, source_files]
        )

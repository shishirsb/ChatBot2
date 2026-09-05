import gradio as gr
from speech_recording.record_and_parse_audio import recorder, stop_recording, generate_summary
from knowledge_base.load_docs import Loader
from speech_recording.load_summary import load_summary


def speech_recording():
    with gr.Accordion("Speech Recording", open=False) as sr_accordion:
        audio_mode = gr.Radio(
            ["System Sound", "Mic"],
            value="System Sound",
            interactive=True,
            label='Select Source'
        )

        language_selected = gr.Radio(
            ["English", "Kannada", 'Telugu'],
            value="English",
            interactive=True,
            label='Select Language'
        )

        with gr.Group(visible=True) as system_group:
            start_btn = gr.Button("🎙 Start Recording")
            stop_btn = gr.Button("⏹ Stop Recording")
            audio_status = gr.Textbox(label='Status')

        transcript_box = gr.Textbox(label="Transcript", interactive=True)

        summarize_btn = gr.Button("Generate Summary")

        summary_box = gr.Markdown(label="Summary")

        upload_btn = gr.Button("Upload as document")
        upload_status = gr.Textbox(label='Status')


        start_btn.click(
            fn=recorder.start,
            inputs=[audio_mode, language_selected],
            outputs=[audio_status, transcript_box, summary_box]
        )

        stop_btn.click(
            fn=stop_recording,
            outputs=[
                audio_status,
                summary_box
            ]
        )

        summarize_btn.click(
            fn=generate_summary,
            inputs=[transcript_box],
            outputs=[
                audio_status,
                summary_box
            ]
        )


        upload_btn.click(
            fn=load_summary,
            inputs=[summary_box],
            outputs=[
                upload_status
            ]
        )



    return sr_accordion, audio_mode, system_group, start_btn, stop_btn, audio_status, transcript_box, summary_box
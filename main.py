
from ui.interface import create_ui

print("Script started")



demo = create_ui()
demo.queue()

print('launching')
demo.launch(
    inbrowser=True,
    allowed_paths=["knowledge_base/uploads"]
)

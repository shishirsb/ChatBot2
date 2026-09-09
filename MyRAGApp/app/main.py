
from dotenv import load_dotenv
from imports.config import UPLOAD_DIR

load_dotenv()

from ui.interface import create_ui

def main():
    print("Script started")

    demo = create_ui()
    demo.queue()

    print('launching')
    demo.launch(
        inbrowser=True,
        allowed_paths=[
            # "knowledge_base/uploads",
            UPLOAD_DIR,
        ],
    )

if __name__ == "__main__":
    main()

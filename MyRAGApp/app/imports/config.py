from pathlib import Path
import os

APP_DATA = Path(os.getenv("LOCALAPPDATA", Path.home())) / "MyRAGApp"

UPLOAD_DIR = APP_DATA / "uploads"

CHROMA_DIR = APP_DATA / "chroma" / "docs_v24"

UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
CHROMA_DIR.mkdir(parents=True, exist_ok=True)

SERVICE_NAME = "MyRAGApp"
USERNAME = "openai_api_key"
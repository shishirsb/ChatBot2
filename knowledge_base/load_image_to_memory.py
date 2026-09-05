from io import BytesIO
from PIL import Image
import requests


def load_image_to_memory(image_url):

    response = requests.get(
        image_url,
        timeout=30,
        headers={
            "User-Agent": "Mozilla/5.0"
        }
    )

    response.raise_for_status()

    with BytesIO(response.content) as buffer:
        image = Image.open(buffer)
        image.load()

    return image.convert("RGB")
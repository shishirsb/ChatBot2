from PIL import Image

def resize_image(image, max_size=768):
    image = image.copy()
    image.thumbnail((max_size, max_size), Image.Resampling.LANCZOS)
    return image
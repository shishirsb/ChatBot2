from langchain_core.messages import HumanMessage
import base64
from io import BytesIO
from imports.AI_models import vision_model
from langchain_core.documents import Document
from docling.document_converter import DocumentConverter
from docling.datamodel.document import PictureItem
import time


def describe_image(image):
    start = time.time()
    buffer = BytesIO()
    image.save(buffer, format="PNG")
    image_bytes = buffer.getvalue()
    image_base64 = base64.b64encode(
        image_bytes
    ).decode("utf-8")
    message = HumanMessage(
        content=[
            {
                "type": "text",
                "text": """
                    Describe this image accurately for use in a document search system.
                    
                    Include:
                    - important visible text
                    - the main subject or topic
                    - diagrams and their relationships
                    - charts and important trends
                    - tables and key values
                    - labels and annotations
                    
                    Be concise but informative.
                    Do not invent information.
                    Return only the description.
                    """
            },
            {
                "type": "image",
                "base64": image_base64,
                "mime_type": "image/png"
            }
        ]
    )
    response = vision_model.invoke([message])
    end = time.time()
    print(f'Took {end-start} seconds')

    print("Response object:", response)
    print("Response content:", repr(response.content))
    print("Content type:", type(response.content))

    return response.content


# -------------------------

def test_load_img_docs():
    converter = DocumentConverter()
    result = converter.convert('docs/PPTs/FOUNDRY TRAINING 28.01.2026 (1).pptx')
    docling_doc = result.document

    image_docs = []
    path = "../removed/docs/PPTs/FOUNDRY TRAINING 28.01.2026 (1).pptx"
    for item, level in docling_doc.iterate_items():
        if not isinstance(item, PictureItem):
            continue
        page_no = item.prov[0].page_no if item.prov else None
        print("\n--- IMAGE FOUND ---")
        print(f"Page: {page_no}")
        image = item.get_image(docling_doc)
        print(f"Image object: {image}")
        print(f"Image size: {image.size if image else None}")
        if image is None:
            print("Could not extract image")
            continue
        description = describe_image(image)
        print(
            f"Description: "
            f"{description[:300] if description else None}"
        )
        if not description:
            print("No description generated")
            continue
        image_doc = Document(
            page_content=description,
            metadata={
                "pages": [page_no],
                "source": str(path)
            }
        )
        image_docs.append(image_doc)
        print(f"Image document added. Total: {len(image_docs)}")
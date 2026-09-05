from docling.document_converter import DocumentConverter
from langchain_core.documents import Document

stored_path = 'removed/docs/pdf/DBS booklet New_final_whatsapp_spread.pdf'
converter = DocumentConverter()
conversion_result = converter.convert(str(stored_path),
                                      page_range=(1, 30))
docling_doc = conversion_result.document
# ------------------------------------------
# Group Docling elements by PDF page
# ------------------------------------------
page_content = {}
for item, level in docling_doc.iterate_items():
    if not item.prov:
        continue
    page_no = item.prov[0].page_no
    # Get text representation of the item
    try:
        text = item.export_to_markdown(docling_doc)
    except Exception:
        try:
            text = item.text
        except AttributeError:
            text = ""
    if not text:
        continue
    page_content.setdefault(page_no, []).append(text)
# ------------------------------------------
# Create one LangChain Document per page
# ------------------------------------------
docs = []
for page_no in sorted(page_content):
    content = "\n\n".join(page_content[page_no])
    doc = Document(
        page_content=content,
        metadata={
            "source": str(stored_path),
            "page": page_no,
        }
    )
    docs.append(doc)
    print(
        f"Page {page_no}: "
        f"{len(content)} characters"
    )

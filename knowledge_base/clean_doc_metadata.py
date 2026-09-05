from pathlib import Path


def clean_doc_metadata(doc):

    metadata = doc.metadata
    dl_meta = metadata.get("dl_meta", {})

    # -------------------------
    # Source
    # -------------------------
    source = metadata.get("source", "")

    # -------------------------
    # Heading
    # -------------------------
    headings = dl_meta.get("headings", [])

    heading = " → ".join(headings) if headings else None

    # -------------------------
    # Pages
    # -------------------------
    pages = set()

    for item in dl_meta.get("doc_items", []):
        for prov in item.get("prov", []):
            page_no = prov.get("page_no")

            if page_no is not None:
                pages.add(page_no)

    pages = sorted(pages)

    # Empty page list → None
    if not pages:
        pages = None

    # -------------------------
    # Replace metadata
    # -------------------------
    # doc.metadata = {
    #     "source": source,
    #     "heading": heading,
    #     "pages": pages
    # }

    metadata = {
        "source": source,
        "heading": heading
    }

    if pages:
        metadata["pages"] = pages

    doc.metadata = metadata

    return doc
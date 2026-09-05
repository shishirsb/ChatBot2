from pathlib import Path


def format_sources(retrieved_docs):
    unique_sources = []
    seen = set()

    for doc in retrieved_docs:

        metadata = doc.metadata

        source = metadata.get("source", "")
        heading = metadata.get("heading")
        pages = metadata.get("pages") or []

        # Normalize pages so they can be used in a set
        pages = tuple(sorted(pages))

        # Deduplicate based on ALL THREE:
        # source + heading + pages
        source_key = (
            source,
            heading,
            pages
        )

        if source_key in seen:
            continue

        seen.add(source_key)

        # -------------------------
        # URL source
        # -------------------------
        if source.startswith(("http://", "https://")):

            source_text = f"- **URL:** {source}\n"

            if heading:
                source_text += f"- **Section:** {heading}\n"

        # -------------------------
        # PDF / file source
        # -------------------------
        else:
            filename = Path(source).name if source else "Unknown"

            source_text = f"- **File:** {filename}\n"

            if heading:
                source_text += f"- **Section:** {heading}\n"

            if len(pages) == 1:
                page_text = str(pages[0])
            elif pages:
                page_text = f"{pages[0]}-{pages[-1]}"
            else:
                page_text = None

            if page_text:
                source_text += f"- **Pages:** {page_text}\n"

        unique_sources.append(source_text)

    # Number sources AFTER deduplication
    sources = []

    for i, source_text in enumerate(unique_sources, start=1):
        sources.append(
            f"### Source {i}\n{source_text}"
        )

    return sources
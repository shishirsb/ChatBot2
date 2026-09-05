def split_transcript(transcript, chunk_size=16000):
    chunks = []

    while len(transcript) > chunk_size:
        split_at = transcript.rfind(".", 0, chunk_size)

        if split_at == -1:
            split_at = chunk_size

        chunks.append(transcript[:split_at + 1].strip())
        transcript = transcript[split_at + 1:].strip()

    if transcript:
        chunks.append(transcript)

    return chunks
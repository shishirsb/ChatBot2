from knowledge_base.load_docs import Loader

def load_summary(summary):
    if not summary:
        return "No summary available."
    loader = Loader()
    return loader.load_documents([summary])
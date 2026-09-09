from langsmith import traceable

@traceable(name='Ask a question', run_type='chain')
def format_docs(retrieved_docs):
    context = '\n----\n'.join([doc.page_content for doc in retrieved_docs])
    return context
from pathlib import Path
from langchain_docling.loader import DoclingLoader, ExportType
from knowledge_base.clean_doc_metadata import clean_doc_metadata
from knowledge_base.extract_image_candidates import extract_image_candidates
from knowledge_base.interpret_image import describe_image
from knowledge_base.load_image_to_memory import load_image_to_memory
from imports.vector_store import vector_store
import gradio as gr
from langchain_core.documents import Document
from docling.document_converter import DocumentConverter
from docling.datamodel.document import PictureItem
import os
from knowledge_base.resize_image import resize_image
import shutil
from PIL import Image
import traceback
from langsmith import traceable
from datetime import datetime


class Loader:
    @traceable(name='Load document', run_type='function call')
    def load_document(self, file, progress_state = {}):
        try:
            progress = progress_state['progress']

            PROJECT_ROOT = Path(__file__).resolve().parent
            UPLOAD_DIR = PROJECT_ROOT / "uploads"
            print(f'PROJECT_ROOT: {PROJECT_ROOT}')
            print(f'UPLOAD_DIR: {UPLOAD_DIR}')
            UPLOAD_DIR.mkdir(exist_ok=True)

            if type(file) == str:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                stored_path = UPLOAD_DIR / f"transcript_{timestamp}.txt"

                stored_path.write_text(
                    file,
                    encoding="utf-8"
                )

                path = stored_path
                filename = stored_path.name

            else:
                path = Path(file.name)
                filename = path.name

                stored_path = UPLOAD_DIR / filename
                shutil.copy2(path, stored_path)

                path = stored_path

            loader = DoclingLoader(file_path=str(stored_path), export_type=ExportType.DOC_CHUNKS)
            progress_state['progress_value'] += 0.05

            converter = DocumentConverter()
            result = converter.convert(path)
            docling_doc = result.document

            num_images = sum(
                1
                for item, level in docling_doc.iterate_items()
                if isinstance(item, PictureItem)
            )

            estimated_time_for_images = num_images * 65
            total_estimated_time = estimated_time_for_images

            progress(
                progress_state['progress_value'],
                desc=f"Loading: {filename}"
                     f"\n Total time Estimate: {total_estimated_time / 60:.1f} minutes")


            docs = []
            for i, doc in enumerate(loader.lazy_load(), start=1):
                try:
                    doc = clean_doc_metadata(doc)
                    docs.append(doc)
                    progress_state['progress_value'] += 0.01
                    progress(
                        progress_state['progress_value'],
                        desc=f"Loading: {filename}"
                             f"\n Total time Estimate: {total_estimated_time / 60:.1f} minutes")
                except Exception as e:
                    print(f'Exception occurred while processing {i}th chunk: {e}')

            image_docs = []
            i=0

            for item, level in docling_doc.iterate_items():
                if not isinstance(item, PictureItem):
                    continue
                page_no = item.prov[0].page_no if item.prov else None
                print("\n--- IMAGE FOUND ---")
                print(f"Page: {page_no}")

                image = item.get_image(docling_doc)

                print(f"Original image size: {image.size if image else None}")

                if image is None:
                    print("Could not extract image")
                    continue

                i += 1

                # Resize before sending to vision model
                image = resize_image(image, max_size=512)

                print(f"Resized image size: {image.size}")

                MAX_RETRIES = 2

                description = None

                for attempt in range(1, MAX_RETRIES + 1):

                    print(
                        f"Describing image {i}/{num_images} "
                        f"(attempt {attempt})..."
                    )

                    description = describe_image(image)

                    print(type(description))
                    print(description[:100])

                    if description:
                        print(type(description))
                        print(description[:100])
                        print("No description returned.")
                        break



                if not description:
                    print(
                        f"Failed to describe image {i} "
                        f"after {MAX_RETRIES} attempts"
                    )
                    continue

                metadata = {
                    "source": str(stored_path)
                }

                if page_no is not None:
                    metadata["pages"] = [page_no]

                image_doc = Document(
                    page_content=description,
                    metadata=metadata
                )

                image_docs.append(image_doc)
                progress_state['progress_value'] += 0.02
                progress(
                    progress_state['progress_value'],
                    desc=f"Loading: {filename} \n"
                         f"\n Total time Estimate: {total_estimated_time / 60:.1f} minutes")
                print(f"Image document added. Total: {len(image_docs)}")

            progress(
                progress_state['progress_value'],
                desc=f"Loaded document: {filename}")

            return docs + image_docs
        except Exception as e:
            print(e)
            traceback.print_exc()
            raise

    @traceable(name='Load URL', run_type='function call')
    def load_url(self, url, progress_state = {}):
        try:
            progress = progress_state['progress']

            loader = DoclingLoader(file_path=url, export_type=ExportType.DOC_CHUNKS)

            docs = []
            for i, doc in enumerate(loader.lazy_load(), start=1):
                try:
                    doc = clean_doc_metadata(doc)
                    docs.append(doc)
                    print(f"Processed URL: {url}... ({i}th chunks)")

                    progress_state['progress_value'] += 0.01
                    progress(
                        progress_state['progress_value'],
                        desc=f"Processed URL: {url}... ({i} chunks)"
                    )
                except Exception as e:
                    print(e)
            image_urls = extract_image_candidates(url)

            total_estimated_time = len(image_urls) * 60

            print(f"Found {len(image_urls)} images")

            progress_state['progress_value'] = 0.4
            progress(
                progress_state['progress_value'],
                desc=f"Loading URL: {url}"
                     f"\n (Total time Estimate: {total_estimated_time / 60:.1f} minutes)")

            image_docs = []

            for i, image_url in enumerate(image_urls, start=1):
                try:
                    image = load_image_to_memory(image_url)

                    image = resize_image(image, max_size=512)

                    description = describe_image(image)

                    if not description:
                        continue

                    image_doc = Document(
                        page_content=description,
                        metadata={
                            "source": url,
                            "image_url": image_url
                        }
                    )


                    progress_state['progress_value'] += 0.01
                    progress(
                        progress_state['progress_value'],
                        desc=f"Loading URL: {url}"
                     f"\n (Total time Estimate: {total_estimated_time / 60:.1f} minutes)")

                    image_docs.append(image_doc)

                except Exception as e:
                    print(f"Failed to process image {i}: {e}")
            return docs + image_docs
        except Exception as e:
            print(e)
            traceback.print_exc()
            raise

    @traceable(name='Load image', run_type='function call')
    def load_image(self, file, progress_state = {}):
        try:
            image_docs = []
            progress = progress_state['progress']
            path = str(file)
            filename = Path(file.name).name

            progress(
                progress_state['progress_value'],
                desc=f"Loading Image: {filename}.")

            UPLOAD_DIR = Path("../uploads")
            UPLOAD_DIR.mkdir(exist_ok=True)

            path = Path(file.name)

            stored_path = UPLOAD_DIR / path.name

            shutil.copy2(path, stored_path)

            print("Stored file:", stored_path)

            # Open image
            image = Image.open(stored_path)

            # Resize before sending to vision model
            image = resize_image(image, max_size=512)

            print(f"Resized image size: {image.size}")

            MAX_RETRIES = 2

            description = None

            for attempt in range(1, MAX_RETRIES + 1):
                print(
                    f"Describing image {1}/{1} "
                    f"(attempt {attempt})..."
                )

                description = describe_image(image)

                print(type(description))
                print(description[:100])

                if description:
                    break

                print(type(description))
                print(description[:100])
                print("No description returned.")

            if not description:
                print(
                    f"Failed to describe image"
                    f"after {MAX_RETRIES} attempts"
                )
                raise Exception('Failed to describe image')

            image_doc = Document(
                page_content = description,
                metadata={
                    "source": str(stored_path)
                }
            )
            image_docs.append(image_doc)
            progress_state['progress_value'] += 0.02
            progress(
                progress_state['progress_value'],
                desc=f"Image document loaded. Total: {len(image_docs)}")
            print(f"Image document loaded. Total: {len(image_docs)}")

            return image_docs
        except Exception as e:
            print(f'An exception occurred: {e}')
            traceback.print_exc()
            raise

    @traceable(name='Load files', run_type='function call')
    def load_files(self, files, url_string = '', progress_state = {}):
        try:
            progress = progress_state['progress']
            all_docs = []
            exceptions = ''

            if url_string:
                urls = [url.strip() for url in url_string.split(";") if url.strip()]
                for url in urls:
                    try:
                        all_docs.extend(self.load_url(url, progress_state=progress_state))
                        progress_state['progress_value'] += 0.1
                        progress(progress_state['progress_value'], desc=f"Loaded {url}")
                        print(f"Loaded {url}")
                    except Exception as e:
                        exceptions += f'URL:{url} ({e})'

            if files:
                for file in files:
                    print(f'Detected file type: {type(file)}')
                    try:
                        if type(file) == str:
                            all_docs.extend(self.load_document(file, progress_state=progress_state))
                            progress_state['progress_value'] += 0.1
                            progress(
                                progress_state['progress_value'],
                                desc=f"Processed chunk..."
                            )
                            print(f"Processed chunk...")
                        else:
                            filename = Path(file.name).name
                            # check file type
                            extension = Path(file.name).suffix.lower()
                            print(f'Extension: {extension}')

                            if extension in [".pdf", '.txt', '.pptx', '.docx']:
                                all_docs.extend(self.load_document(file, progress_state=progress_state))
                                progress_state['progress_value'] += 0.1
                                progress(
                                    progress_state['progress_value'],
                                    desc=f"Processed {filename}..."
                                )
                                print(f"Processed {filename}...")
                            elif extension in [".jpg", '.png']:
                                all_docs.extend(self.load_image(file, progress_state=progress_state))
                                progress_state['progress_value'] += 0.1
                                progress(
                                    progress_state['progress_value'],
                                    desc=f"Processed {filename}..."
                                )
                                print(f"Processed {filename}...")
                            else:
                                raise Exception(f"Unsupported file type: {extension}")
                    except Exception as e:
                        exceptions += f'File name:{filename if filename else "unknown... likey a transcript"} ({e})'
            return all_docs, exceptions
        except Exception as e:
            print(e)
            traceback.print_exc()
            raise

    # @traceable(name='Load documents', run_type='function call')
    def load_documents(self, files, url='', progress_state = {'progress': gr.Progress(), 'progress_value': 0}):
        try:
            progress_state['progress_value'] = 0

            progress = progress_state['progress']
            progress_state['progress_value'] += 0.05

            progress(progress_state['progress_value'], desc="Loading documents...")
            print("Loading documents...")

            all_doc_chunks, exceptions = self.load_files(files, url, progress_state)

            progress_state['progress_value'] = 0.6
            progress(progress_state['progress_value'], desc="Load documents completed...")

            batch_size = 20

            for batch_num, i in enumerate(range(0, len(all_doc_chunks), batch_size), start=1):
                batch = all_doc_chunks[i:i + batch_size]

                vector_store.add_documents(batch)
                progress_state['progress_value'] += 0.05
                progress(progress_state['progress_value'], desc=f"Indexed {i + len(batch)} / {len(all_doc_chunks)}")

                print(f"Indexed {i + len(batch)} / {len(all_doc_chunks)}")

            progress(1.0, desc="Complete")
            print("Load documents completed")

            return f"""Success. Added {len(all_doc_chunks)} chunks.
            Exceptions:
            {exceptions}
            """
        except Exception as e:
            print(e)
            return f"Exception occurred while loading documents: {e}"


from pathlib import Path
from langchain_docling.loader import DoclingLoader, ExportType
from knowledge_base.clean_doc_metadata import clean_doc_metadata
from knowledge_base.extract_image_candidates import extract_image_candidates
from knowledge_base.interpret_image import describe_image
from knowledge_base.load_image_to_memory import load_image_to_memory
from imports.vector_store import get_vector_Store
import gradio as gr
from knowledge_base.resize_image import resize_image
import shutil
from PIL import Image
import traceback
from langsmith import traceable
from datetime import datetime
from docling.document_converter import DocumentConverter
from langchain_core.documents import Document
import fitz
from imports.config import UPLOAD_DIR


class Loader:
    @traceable(name='Load document', run_type='function call')
    def load_document(self, file, progress_state = {}):
        try:
            progress = progress_state['progress']

            print(f'UPLOAD_DIR: {UPLOAD_DIR}')
            # UPLOAD_DIR.mkdir(exist_ok=True)

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

                if stored_path.exists():
                    raise FileExistsError(
                        f"File already exists in knowledge base: {filename}"
                    )
                shutil.copy2(path, stored_path)

                path = stored_path


            with fitz.open(str(path)) as pdf:
                pages = len(pdf)
                print(f'Pages: {pages}')

            time_estimate = 12.2 * pages
            progress(
                progress_state['progress_value'],
                desc=f"Loading: {filename}"
                     f"\n ( {time_estimate / 60:.1f} minutes) ")

            converter = DocumentConverter()
            conversion_result = converter.convert(str(path))
            docling_doc = conversion_result.document
            progress_state['progress_value'] += 0.15

            estimated_time_for_images = 0
            total_estimated_time = estimated_time_for_images

            page_content = {}
            for item, level in docling_doc.iterate_items():
                if not item.prov:
                    continue
                page_no = item.prov[0].page_no
                bbox = item.prov[0].bbox
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

                # page_content.setdefault(page_no, []).append(text)
                page_content.setdefault(page_no, []).append({
                    "text": text,
                    "bbox": bbox,
                })

            docs = []

            for page_no in sorted(page_content):


                X_RANGE = 20

                items = sorted(
                    page_content[page_no],
                    key=lambda item: (
                        # round(item["bbox"].l / X_RANGE),
                        int(item["bbox"].l / X_RANGE),
                        -item["bbox"].t
                    )
                )

                content = "\n\n".join(
                    item["text"]
                    for item in items
                )

                doc = Document(
                    page_content=content,
                    metadata={
                        "source": str(stored_path),
                        "page": page_no,
                    }
                )

                docs.append(doc)

            # image_docs = []
            # i=0
            #
            # for item, level in docling_doc.iterate_items():
            #     if not isinstance(item, PictureItem):
            #         continue
            #     page_no = item.prov[0].page_no if item.prov else None
            #     print("\n--- IMAGE FOUND ---")
            #     print(f"Page: {page_no}")
            #
            #     image = item.get_image(docling_doc)
            #
            #     print(f"Original image size: {image.size if image else None}")
            #
            #     if image is None:
            #         print("Could not extract image")
            #         continue
            #
            #     i += 1
            #
            #     # Resize before sending to vision model
            #     image = resize_image(image, max_size=512)
            #
            #     print(f"Resized image size: {image.size}")
            #
            #     MAX_RETRIES = 2
            #
            #     description = None
            #
            #     for attempt in range(1, MAX_RETRIES + 1):
            #
            #         print(
            #             f"Describing image {i}/{num_images} "
            #             f"(attempt {attempt})..."
            #         )
            #
            #         description = describe_image(image)
            #
            #         print(type(description))
            #         print(description[:100])
            #
            #         if description:
            #             print(type(description))
            #             print(description[:100])
            #             print("No description returned.")
            #             break
            #
            #
            #
            #     if not description:
            #         print(
            #             f"Failed to describe image {i} "
            #             f"after {MAX_RETRIES} attempts"
            #         )
            #         continue
            #
            #     metadata = {
            #         "source": str(stored_path)
            #     }
            #
            #     if page_no is not None:
            #         metadata["pages"] = [page_no]
            #
            #     image_doc = Document(
            #         page_content=description,
            #         metadata=metadata
            #     )
            #
            #     image_docs.append(image_doc)
            #     progress_state['progress_value'] += 0.02
            #     progress(
            #         progress_state['progress_value'],
            #         desc=f"Loading: {filename} \n"
            #              f"\n Total time Estimate: {total_estimated_time / 60:.1f} minutes")
            #     print(f"Image document added. Total: {len(image_docs)}")

            progress(
                progress_state['progress_value'],
                desc=f"Loaded document: {filename}")

            return docs
        except Exception as e:
            print(e)
            # Remove file from uploads directory
            try:
                if path.exists():
                    path.unlink()
                    print(f"Removed file: {path}")
            except Exception as cleanup_error:
                print(f"Failed to remove file: {cleanup_error}")

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

                            if extension in [".pdf"]:
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

            batch_size = 256
            vector_store = get_vector_Store()

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
            # Delete ALL files from uploads directory
            try:
                for file_path in UPLOAD_DIR.iterdir():
                    if file_path.is_file():
                        file_path.unlink()
                        print(f"Removed file: {file_path}")

            except Exception as cleanup_error:
                print(f"Failed to clean uploads directory: {cleanup_error}")
            return f"Exception occurred while loading documents: {e}"


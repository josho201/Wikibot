import torch
from docling.datamodel.settings import settings
import faiss
settings.perf.code_formula_batch_size = 2

import os
from PyPDF2 import PdfReader, PdfWriter
import tempfile
from langchain_text_splitters import MarkdownHeaderTextSplitter
import hashlib
from docling.backend.docling_parse_v4_backend import DoclingParseV4DocumentBackend
from docling.document_converter import DocumentConverter, PdfFormatOption
from docling.datamodel.pipeline_options import PdfPipelineOptions, AcceleratorOptions, AcceleratorDevice
from docling.datamodel.base_models import InputFormat
import numpy as np
from sentence_transformers import SentenceTransformer
import json



class WikiFile:

    METADATA_FILE = 'processed_wikifiles.json'
    
    def __init__(self, pdf_path, do_formula_enrichment:bool = True):

        self.metadata = self.load_metadata()

        self.pdf_path = pdf_path
        self.paths = []
        self.markdown_content = ""
        self.splited_markdown = []

        self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')  # Small, efficient model
        self.embeddings = []
        self.texts = []
        self.index = None

        self.pipeline_options = PdfPipelineOptions()
        self.pipeline_options.accelerator_options = AcceleratorOptions(
            num_threads=8, 
            device=AcceleratorDevice.CUDA
        )
        self.pipeline_options.do_formula_enrichment = do_formula_enrichment
        self.pipeline_options.code_formula_batch_size = 2
        
        self.converter = DocumentConverter(format_options={
            InputFormat.PDF: PdfFormatOption(
                pipeline_options=self.pipeline_options
                )
        })  


    def load_metadata(self):
        if os.path.exists(self.METADATA_FILE):
            with open(self.METADATA_FILE, 'r') as file:
                return json.load(file) or {}
        return {}
    
    def compute_checksum(self):
        hasher = hashlib.sha256()
        with open(self.pdf_path, 'rb') as file:
            for chunk in iter(lambda: file.read(4096), b""):
                hasher.update(chunk)
        return hasher.hexdigest()

    def is_processed(self):
        checksum = self.compute_checksum()
        file_info = self.metadata.get(self.pdf_path, {})

        if file_info and file_info.get('checksum') == checksum:
            faiss_index_path = file_info.get('faiss_index_path')
            embeddings_path = file_info.get('embeddings_path')
            texts_path = file_info.get('texts_path')

            if faiss_index_path and embeddings_path:
                self.load_embeddings(embeddings_path)
                self.load_faiss_index(faiss_index_path)
                self.load_texts(texts_path)
            return True
        return False
    
    def load_embeddings(self, embeddings_path):
        self.embeddings = np.load(embeddings_path)
    
    def load_faiss_index(self, faiss_index_path):
        self.index = faiss.read_index(faiss_index_path)

    def load_texts(self, texts_path):
        with open(texts_path, 'r') as f:
            self.texts = json.load(f)
        

    def mark_as_processed(self, embeddings_path, faiss_index_path, texts_path):
        checksum = self.compute_checksum()
        self.metadata[self.pdf_path] = {
            'checksum': checksum,
            'processed_at': os.path.getmtime(self.pdf_path),
            'faiss_index_path': faiss_index_path,
            'embeddings_path': embeddings_path,
            "texts_path": texts_path
        }
        temp_metadata = self.METADATA_FILE + '.tmp'
        with open(temp_metadata, 'w') as f:
            json.dump(self.metadata, f, indent=4)
        os.replace(temp_metadata, self.METADATA_FILE)
        print(f"Metadata updated and saved to {self.METADATA_FILE}")


    def split_pdf_to_temp_files(self):
        # Create a temporary directory
        temp_dir = tempfile.mkdtemp()
        print(f"Temporary directory created: {temp_dir}")
        paths = []

        # Open the PDF file
        with open(self.pdf_path, 'rb') as file:
            reader = PdfReader(file)
            num_pages = len(reader.pages)

            # Split PDF into sections of 10 pages
            for start_page in range(0, num_pages, 10):
                writer = PdfWriter()

                # Add up to 10 pages to the current section
                for page_number in range(start_page, min(start_page + 10, num_pages)):
                    writer.add_page(reader.pages[page_number])

                # Create output path
                output_filename = f"section_{(start_page // 10) + 1}.pdf"
                output_path = os.path.join(temp_dir, output_filename)

                # Write the section to a new PDF file
                with open(output_path, 'wb') as output_file:
                    writer.write(output_file)

                print(f"Section {(start_page // 10) + 1} saved as {output_path}")
                paths.append(output_path)

        self.paths = paths

    def create_markwdon(self):
        self.markdown_content = ""
        for file_path in self.paths:
            print("processing file: ", file_path, "/", len(self.paths))

            with torch.amp.autocast("cuda") and torch.inference_mode():
                tmp_result = self.converter.convert(file_path)
                print(f"-- file converted")

                self.markdown_content += tmp_result.document.export_to_markdown()
                print(f"-- markdown content added")
    
    def split_markdown(self):
        splitter = MarkdownHeaderTextSplitter(
            headers_to_split_on=[
                ("#", "Header"),
                ("##", "Header"),
                ("###", "Header"),
            ],
        )

        self.splited_markdown = splitter.split_text(self.markdown_content)

    def create_embeddings(self):
        # Create a list to store embeddings and text pairs
        
        for i, section in zip(range(len(self.splited_markdown)), self.splited_markdown):

            print(f"Embedding section {i + 1} / {len(self.splited_markdown)}")
            # Create embedding for the content
            embedding = self.embedding_model.encode(
                f"header: {section.metadata.get('Header', '')} \n {section.page_content}", 
                show_progress_bar=False
                )
            
            # Store embedding and associated text
            self.embeddings.append(embedding)
            self.texts.append(section.page_content)

        self.embeddings = np.array(self.embeddings).astype('float32')

    def create_faiss_index(self):
        self.index = faiss.IndexFlatL2(self.embeddings.shape[1])
        self.index.add(self.embeddings)

    def search(self, query, k=5):

        query_embedding = self.embedding_model\
            .encode(query)\
            .reshape(1, -1)\
            .astype('float32')
        _, indices = self.index.search(query_embedding, k=k)

        results = []
        for idx in indices[0]:
            results.append(self.texts[idx])
        return results
    
    def init(self, path = None): 

        if self.is_processed():
            print(f"PDF {self.pdf_path} has already been processed. Skipping.")
            return
        # self.paths = [self.pdf_path]
        self.split_pdf_to_temp_files()
        self.create_markwdon()
        self.split_markdown()


        self.create_embeddings()
        self.create_faiss_index()

        self.save_WikiFile(filepath=path)

    def save_WikiFile(self, filepath):
        # Save the index

        faiss_path = f"{filepath}_faiss_index.bin" or f"{self.pdf_path.replace('.pdf', '')}_faiss_index.bin" 
        embeddings_path =   f"{filepath}_embeddings.npy" or f"{self.pdf_path.replace('.pdf', '')}_embeddings.npy"
        texts_path = f"{filepath}_texts.json" or f"{self.pdf_path.replace('.pdf', '')}_texts.json"

        with open(texts_path, 'w') as f:
            json.dump(self.texts, f, indent=4, ensure_ascii=False)
        print("Texts saved to", texts_path)
        faiss.write_index(self.index, faiss_path)
        print(f"FAISS index saved to {faiss_path}")

        # Save the embeddings separately
        np.save(embeddings_path, self.embeddings)

        self.mark_as_processed(embeddings_path, faiss_path, texts_path)
        print("Embeddings saved to", embeddings_path)


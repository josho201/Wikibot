import torch
from docling.datamodel.settings import settings

"""
    doc_batch_size: int = 2
    doc_batch_concurrency: int = 2
    page_batch_size: int = 4
    page_batch_concurrency: int = 2
    elements_batch_size: int = 16
"""

settings.perf.code_formula_batch_size = 2

import os
from PyPDF2 import PdfReader, PdfWriter
import tempfile

from docling.backend.docling_parse_v4_backend import DoclingParseV4DocumentBackend
from docling.document_converter import DocumentConverter, PdfFormatOption
from docling.datamodel.pipeline_options import PdfPipelineOptions, AcceleratorOptions, AcceleratorDevice
from docling.datamodel.base_models import InputFormat
import json


accelerator_options = AcceleratorOptions(
        num_threads=8, device=AcceleratorDevice.CUDA
    )

pipeline_options = PdfPipelineOptions()

pipeline_options.accelerator_options = accelerator_options
pipeline_options.do_formula_enrichment = True
pipeline_options.code_formula_batch_size = 2
converter = DocumentConverter(format_options={
    InputFormat.PDF: PdfFormatOption(
        pipeline_options=pipeline_options,
        backend=DoclingParseV4DocumentBackend,
        )
})



def split_pdf_to_temp_files(pdf_path):
    # Create a temporary directory
    temp_dir = tempfile.mkdtemp()
    print(f"Temporary directory created: {temp_dir}")
    paths = []	
    # Open the PDF file
    with open(pdf_path, 'rb') as file:
        # Read the PDF file
        reader = PdfReader(file)
        num_pages = len(reader.pages)

        # Iterate through each page and save it as a separate PDF
        for page_number in range(num_pages):
            writer = PdfWriter()
            writer.add_page(reader.pages[page_number])

            # Create output path
            output_filename = f"page_{page_number + 1}.pdf"
            output_path = os.path.join(temp_dir, output_filename)

            # Write the page to a new PDF file
            with open(output_path, 'wb') as output_file:
                writer.write(output_file)

            print(f"Page {page_number + 1} saved as {output_path}")
            paths.append(output_path)
    return paths



# Example usage
pdf_path = "testpdf/transformers.pdf"
temp_directory = split_pdf_to_temp_files(pdf_path)
print(f"All pages have been saved to {temp_directory}")


markdown_content = ""
for file_path in temp_directory:
    print("processing file: ", file_path, "/", len(temp_directory))

    
    with torch.amp.autocast("cuda") and torch.inference_mode():
        tmp_result = converter.convert(file_path)
        print(f"-- file converted")

        markdown_content += tmp_result.document.export_to_markdown()
        print(f"-- markdown content added")
    


markdown_content = markdown_content.replace("\n \n", "\n").replace("\n\n", "\n")
with open("testpdf/transformers.txt", "w") as f:
    f.write(markdown_content)
import os
from pathlib import Path
from PyPDF2 import PdfReader, PdfWriter

def split_pdf(input_pdf, output_prefix):
    reader = PdfReader(input_pdf)
    for i, page in enumerate(reader.pages):
        writer = PdfWriter()
        writer.add_page(page)
        with open(f"./outputs/{output_prefix}_{i}.pdf", "wb") as out_pdf:
            writer.write(out_pdf)

if not os.path.exists("outputs"):
    os.makedirs("outputs")

filename = input("Enter PDF filename (full file path valid):")
split_pdf(filename, "page")

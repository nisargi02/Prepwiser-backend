import os
import pytesseract
from pdf2image import convert_from_path
from PyPDF2 import PdfReader
from PIL import Image

# Set the path for the input and output folders

output_folder = "prepwiser/texts/"

# Define a function to convert PDF to text using OCR
def pdf_to_text(file_path):
    with open(file_path, 'rb') as f:
        pdf_reader = PdfReader(f)
        # Extract text from each page of the PDF file
        text = ""
        for i in range(len(pdf_reader.pages)):
            # Convert each page of the PDF to an image and apply OCR to extract text
            pil_image = convert_from_path(file_path, first_page=i+1, last_page=i+1)[0]
            text += pytesseract.image_to_string(pil_image)
        return text



import pytesseract
from pdf2image import convert_from_path
import cv2
import re
import PIL.Image
import numpy as np

PIL.Image.MAX_IMAGE_PIXELS = 933120000

def preprocess_image(image):
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)[1]
    return thresh

def ocr_columns(image):
    height, width = image.shape[:2]
    left_roi = image[0:height, 0:width//2]  # Left half
    right_roi = image[0:height, width//2:]  # Right half
    return (
        pytesseract.image_to_string(preprocess_image(left_roi), config='--psm 6'),
        pytesseract.image_to_string(preprocess_image(right_roi), config='--psm 6')
    )

def extract_dictionary(pdf_path):
    pages = convert_from_path(pdf_path, 500)
    entries = []

    for page in pages:
        image = np.array(page)
        left_text, right_text = ocr_columns(image)

        replacements = {
            '|': 'I', 
            '‘': "'",
            '’': "'",
            '“': '"',
            '”': '"',
            '\n\n': '\n'
        }
        
        for old, new in replacements.items():
            left_text = left_text.replace(old, new)
            right_text = right_text.replace(old, new)
        
        lines = []
        for line in left_text.splitlines():
            if len(line.strip()) > 2:
                lines.append(line.strip())

        for line in right_text.splitlines():
            if len(line.strip()) > 2:
                lines.append(line.strip())
        
    return "\n".join(lines)

pdf_path = input("Enter PDF filename (full file path valid):")
my_entries = extract_dictionary(pdf_path)

print(my_entries)



    
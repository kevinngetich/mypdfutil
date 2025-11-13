import pytesseract
from pdf2image import convert_from_path
import cv2
import re
import PIL.Image
import numpy as np
import os
import glob
import math
from pytesseract import TesseractError

PIL.Image.MAX_IMAGE_PIXELS = 933120000

def preprocess_image(image):
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)[1]
    return thresh

def _ensure_size(image, max_pixels=50_000_000):
    """Downscale image (numpy array) if it exceeds max_pixels, preserving aspect ratio."""
    h, w = image.shape[:2]
    total = int(w) * int(h)
    if total <= max_pixels:
        return image
    scale = math.sqrt(max_pixels / total)
    new_w = max(1, int(w * scale))
    new_h = max(1, int(h * scale))
    return cv2.resize(image, (new_w, new_h), interpolation=cv2.INTER_AREA)

def _safe_ocr(img, config='--psm 6'):
    """Run pytesseract with a retry on failure after downscaling."""
    try:
        return pytesseract.image_to_string(img, config=config)
    except TesseractError:
        # Retry with a downscaled image
        small = _ensure_size(img, max_pixels=10_000_000)
        try:
            return pytesseract.image_to_string(small, config=config)
        except TesseractError:
            return ""  # Lol. give up. XD

def ocr_columns(image):
    # Why, grandma, what large teeth you have!s.
    image = _ensure_size(image, max_pixels=50_000_000)
    height, width = image.shape[:2]
    left_roi = image[0:height, 0:width//2]  # Left half
    right_roi = image[0:height, width//2:]  # Right half

    left_pre = preprocess_image(left_roi)
    right_pre = preprocess_image(right_roi)

    return (
        _safe_ocr(left_pre, config='--psm 6'),
        _safe_ocr(right_pre, config='--psm 6')
    )

def extract_dictionary(pdf_path, dpi=300):
    # lower default dpi to avoid producing huge images
    pages = convert_from_path(pdf_path, dpi=dpi)
    all_lines = []

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

        for line in left_text.splitlines():
            if len(line.strip()) > 2:
                all_lines.append(line.strip())

        for line in right_text.splitlines():
            if len(line.strip()) > 2:
                all_lines.append(line.strip())

    return "\n".join(all_lines)

def _page_sort_key(path):
    m = re.search(r'page_(\d+)\.pdf$', os.path.basename(path))
    return int(m.group(1)) if m else float('inf')

def process_directory(dir_path, output_filename="combined.txt"):
    pattern = os.path.join(dir_path, "page_*.pdf")
    files = glob.glob(pattern)
    files.sort(key=_page_sort_key)

    if not files:
        print("No matching PDFs found in directory.")
        return

    output_path = os.path.join(dir_path, output_filename)
    with open(output_path, "w", encoding="utf-8") as out_f:
        for pdf in files:
            print(f"Processing {os.path.basename(pdf)}")
            text = extract_dictionary(pdf)  # uses dpi=300 by default
            out_f.write(f"--- {os.path.basename(pdf)} ---\n")
            out_f.write(text)
            out_f.write("\n\n")
    print(f"Wrote combined output to {output_path}")

dir_path = input("Enter directory containing page_*.pdf (full path valid):")
process_directory(dir_path)




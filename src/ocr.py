import pytesseract
from pdf2image import convert_from_path
from pathlib import Path

POPPLER_PATH = Path(r"C:\TEMP\poppler-26.02.0\Library\bin")
TESSERACT_PATH = Path(r"C:\TEMP\Tesseract-OCR\tesseract.exe")
pytesseract.pytesseract.tesseract_cmd = TESSERACT_PATH

def extraire_texte_ocr(pdf_path: Path) -> str:
    pages = convert_from_path(pdf_path, dpi=300, poppler_path=POPPLER_PATH)  # conversion du PDF en images à haute résolution pour une meilleure reconnaissance OCR
    
    texte = ""
    for page in pages:
        texte += pytesseract.image_to_string(page, lang="fra+eng", config="--oem 1 --psm 6") # configuration pour une meilleure reconnaissance de texte dans les documents structurés

    return texte
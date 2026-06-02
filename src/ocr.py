import pytesseract
from pdf2image import convert_from_path
from pathlib import Path
import pymupdf
import io
from PIL import Image

from .config_path import POPPLER_PATH, TESSERACT_PATH

if TESSERACT_PATH.exists():
    pytesseract.pytesseract.tesseract_cmd = str(TESSERACT_PATH)

def extraire_texte_ocr_pdf2image(pdf_path: Path) -> str:

    poppler = POPPLER_PATH if POPPLER_PATH.exists() else None # None = utiliser le PATH système

    # conversion du PDF en images à haute résolution pour une meilleure reconnaissance OCR
    pages = convert_from_path(
        pdf_path, 
        dpi=300, 
        first_page=1,
        last_page=2,  # on se limite aux premières pages pour l'OCR (gain de temps)
        poppler_path=poppler  # type: ignore
        )  
    
    texte = ""
    for page in pages:
        texte += pytesseract.image_to_string(page, lang="fra+eng", config="--oem 1 --psm 6") # configuration pour une meilleure reconnaissance de texte dans les documents structurés

    return texte

def extrire_texte_ocr_pymupdf(pdf_path: Path) -> str:
    pass
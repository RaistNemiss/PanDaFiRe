import pytesseract
import pymupdf
from pathlib import Path
from PIL import Image


from .config_path import TESSERACT_PATH

if TESSERACT_PATH.exists():
    pytesseract.pytesseract.tesseract_cmd = str(TESSERACT_PATH)

def extraire_texte_ocr(pdf_path: Path, nb_pages_max: int = 3, dpi: int = 200) -> str:
    """Stratégie OCR via rendu image PyMuPDF + Tesseract, avec limitation du nombre de pages à traiter pour l'OCR."""
    # dpi = 200  # Résolution pour le rendu de la page
    texte = ""

    with pymupdf.open(pdf_path) as pdf_to_ocr:

        derniere_page = min(nb_pages_max, pdf_to_ocr.page_count)

        for page in pdf_to_ocr.pages(stop=derniere_page):

            # étape 1: PDF -> Pixmap (rendu de la page en pixels)
            pixmap_page_image = page.get_pixmap(dpi=dpi, colorspace=pymupdf.csGRAY)  # Rendu en niveaux de gris pour accélérer l'OCR, souvent suffisant pour les documents textuels. 

            # étape 2: Pixmap -> PIL.Image (format compatible avec Tesseract)
            pil_page_image = Image.frombytes("L", (pixmap_page_image.width, pixmap_page_image.height), pixmap_page_image.samples) # L pour mode de couleur en niveaux de gris.
            
            # étape 3: OCR avec Tesseract
            texte += pytesseract.image_to_string(pil_page_image, lang="fra+eng", config="--oem 1 --psm 6")
    
    return texte


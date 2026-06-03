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

def extraire_texte_ocr_pymupdf(pdf_path: Path, nb_pages_max: int = 3) -> str:
    """Stratégie OCR via rendu image PyMuPDF + Tesseract, avec limitation du nombre de pages à traiter pour l'OCR."""
    dpi = 200  # Résolution pour le rendu de la page
    texte = ""

    with pymupdf.open(pdf_path) as pdf_to_ocr:

        derniere_page = min(nb_pages_max, pdf_to_ocr.page_count)

        for page in pdf_to_ocr.pages(stop=derniere_page):

            # étape 1: PDF -> Pixmap (rendu de la page en pixels)
            pixmap_page_image = page.get_pixmap(dpi=dpi)

            # étape 2: Pixmap -> PIL.Image (format compatible avec Tesseract)
            pil_page_image = Image.open(io.BytesIO(pixmap_page_image.tobytes("png")))

            # étape 3: OCR avec Tesseract
            texte += pytesseract.image_to_string(pil_page_image, lang="fra+eng", config="--oem 1 --psm 6")
    
    return texte

if __name__ == "__main__":
    # Exemple d'utilisation
    pdf_test = Path(r"C:\Users\afarina\Downloads\attestation efaje.pdf")
    print("Texte extrait avec pdf2image + Tesseract :")
    print(extraire_texte_ocr_pdf2image(pdf_test))
    print("\nTexte extrait avec PyMuPDF + Tesseract :")
    print(extraire_texte_ocr_pymupdf(pdf_test))
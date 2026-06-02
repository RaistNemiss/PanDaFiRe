import time
import pytesseract
from pdf2image import convert_from_path
import pymupdf
from PIL import Image
from pathlib import Path
import io

from config_path import POPPLER_PATH, TESSERACT_PATH

# Config Tesseract
if TESSERACT_PATH.exists():
    pytesseract.pytesseract.tesseract_cmd = str(TESSERACT_PATH)

# Paramètres communs
DPI = 300
FIRST_PAGE = 1
LAST_PAGE = 2
LANG = "fra+eng"
CONFIG = "--oem 1 --psm 6"
PDF_DIR = Path(r"C:\Users\Raist Nemiss\Downloads\pdf test")

# 🅰️ Pipeline ACTUEL : pdf2image + Tesseract
def ocr_avec_pdf2image(pdf_path: Path) -> str:
    poppler = POPPLER_PATH if POPPLER_PATH.exists() else None
    pages = convert_from_path(
        pdf_path,
        dpi=DPI,
        first_page=FIRST_PAGE,
        last_page=LAST_PAGE,
        poppler_path=poppler,  # type: ignore
    )
    texte = ""
    for page in pages:
        texte += pytesseract.image_to_string(page, lang=LANG, config=CONFIG)
    return texte


# 🅱️ Pipeline NOUVEAU : PyMuPDF + Tesseract
def ocr_avec_pymupdf(pdf_path: Path) -> str:
    doc = pymupdf.open(pdf_path)
    texte = ""

    # Limiter aux pages voulues
    last = min(LAST_PAGE, doc.page_count)

    for num_page in range(FIRST_PAGE - 1, last):  # PyMuPDF indexe à 0
        page = doc[num_page]
        # Rendu en image haute résolution
        # matrix = zoom : 300 DPI / 72 DPI natif = ~4.17
        zoom = DPI / 72
        matrix = pymupdf.Matrix(zoom, zoom)
        pix = page.get_pixmap(matrix=matrix)

        # Conversion en PIL.Image pour Tesseract
        img = Image.open(io.BytesIO(pix.tobytes("png")))
        texte += pytesseract.image_to_string(img, lang=LANG, config=CONFIG)

    doc.close()
    return texte


# 🏁 Benchmark
def benchmark(pdf_path: Path):
    print(f"\n{'='*60}")
    print(f"📄 {pdf_path.name}")
    print(f"{'='*60}")

    # Pipeline A
    t0 = time.perf_counter()
    texte_a = ocr_avec_pdf2image(pdf_path)
    temps_a = time.perf_counter() - t0
    print(f"🅰️  pdf2image + Tesseract : {temps_a:.2f}s | {len(texte_a)} chars")

    # Pipeline B
    t0 = time.perf_counter()
    texte_b = ocr_avec_pymupdf(pdf_path)
    temps_b = time.perf_counter() - t0
    print(f"🅱️  PyMuPDF    + Tesseract : {temps_b:.2f}s | {len(texte_b)} chars")

    # Comparaison
    diff = ((temps_a - temps_b) / temps_a) * 100
    print(f"⚡ Gain PyMuPDF : {diff:+.1f}%")


if __name__ == "__main__":
    dossier = PDF_DIR  # 👈 à adapter
    for pdf in dossier.glob("*.pdf"):
        benchmark(pdf)

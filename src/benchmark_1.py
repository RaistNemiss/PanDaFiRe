"""
Script de benchmark : compare extraction texte natif vs OCR
sur un dossier de PDF de test.
"""
import time
from pathlib import Path

import pymupdf
from PIL import Image
import pytesseract

from config_path import TESSERACT_PATH

# ⚙️ À adapter
PDF_DIR = Path(r"C:\Users\Raist Nemiss\Downloads\pdf test")
SEUIL_TEXTE = 50  # caractères mini pour considérer qu'il y a du texte natif

pytesseract.pytesseract.tesseract_cmd = TESSERACT_PATH


def extraire_texte_natif(pdf_path: Path) -> str:
    """Tente d'extraire le texte directement depuis le PDF."""
    doc = pymupdf.open(pdf_path)
    texte = doc[0].get_text()  # On teste sur la 1ère page
    doc.close()
    return texte.strip()


def extraire_texte_ocr(pdf_path: Path, dpi: int = 200) -> str:
    """Fallback OCR via rendu image PyMuPDF + Tesseract."""
    doc = pymupdf.open(pdf_path)
    page = doc[0]
    zoom = dpi / 72
    mat = pymupdf.Matrix(zoom, zoom)
    pix = page.get_pixmap(matrix=mat)
    img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
    doc.close()
    return pytesseract.image_to_string(img, lang="fra").strip()


def traiter_pdf(pdf_path: Path) -> dict:
    """Stratégie hybride avec mesure de temps."""
    start = time.perf_counter()
    
    texte = extraire_texte_natif(pdf_path)
    methode = "natif"
    
    if len(texte) < SEUIL_TEXTE:
        texte = extraire_texte_ocr(pdf_path)
        methode = "ocr"
    
    duree = time.perf_counter() - start
    
    return {
        "fichier": pdf_path.name,
        "methode": methode,
        "duree": duree,
        "nb_chars": len(texte),
    }


def main():
    pdfs = list(PDF_DIR.glob("*.pdf"))
    print(f"📂 {len(pdfs)} PDF trouvés\n")
    
    resultats = []
    for pdf in pdfs:
        try:
            r = traiter_pdf(pdf)
            resultats.append(r)
            icone = "⚡" if r["methode"] == "natif" else "🐢"
            print(f"{icone} {r['fichier']:<40} {r['methode']:<6} "
                  f"{r['duree']:>6.2f}s  ({r['nb_chars']} chars)")
        except Exception as e:
            print(f"❌ {pdf.name} : {e}")
    
    # 📊 Récap
    print("\n" + "="*60)
    total = sum(r["duree"] for r in resultats)
    natifs = [r for r in resultats if r["methode"] == "natif"]
    ocrs = [r for r in resultats if r["methode"] == "ocr"]
    
    print(f"⏱️  Temps total : {total:.2f}s")
    print(f"⚡ PDF natifs  : {len(natifs)} (moy. {sum(r['duree'] for r in natifs)/max(len(natifs),1):.2f}s)")
    print(f"🐢 PDF OCR     : {len(ocrs)} (moy. {sum(r['duree'] for r in ocrs)/max(len(ocrs),1):.2f}s)")


if __name__ == "__main__":
    main()

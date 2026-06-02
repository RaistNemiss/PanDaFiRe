import pdfplumber
import pymupdf

document_path = r"C:\Users\Raist Nemiss\Downloads\pdf test\Scan2026-05-30_214451.pdf"
doc = pymupdf.open(document_path) #ouvre un document PDF avec PyMuPDF
with open (r"C:\Users\Raist Nemiss\Downloads\pdf test\output_pymupdf.txt", "w", encoding="utf-8") as f: #crée un fichier texte pour écrire le contenu extrait
    for page in doc: #itère à travers chaque page du document
        text = page.get_text() #extrait le texte de la page et l'encode en UTF-8
        if text == "":
            print("Aucun texte trouvé sur la page.")
            continue
        f.write(text)
        f.write(50 * "-" + "\n") #écrit le texte extrait dans le fichier de sortie
print (doc)

with pdfplumber.open(document_path) as pdf:   
    # extract_text() peut retourner None si la page est vide ou si le texte ne peut pas être extrait (ex: PDF scanné)
    texte = "\n".join(page.extract_text() or "" for page in pdf.pages)

with open (r"C:\Users\Raist Nemiss\Downloads\pdf test\output_pdfplumber.txt", "w", encoding="utf-8") as f: #crée un fichier texte pour écrire le contenu extrait
    f.write(texte)
print (pdf)
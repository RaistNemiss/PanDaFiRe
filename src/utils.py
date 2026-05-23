import re
import unicodedata
from pathlib import Path
import json

ARTICLES_PREPOSITIONS = r"\b(de|du|la|des|le|les|et|à|au|aux)\b"


def normaliser_text(text: str, stopwords: bool = True) -> str:
    
    text_normalise = text.lower().strip()

    # enlever les accents
    text_normalise = enlever_accents(text_normalise)
    
    # enlever les articles et prépositions courants
    if stopwords:
        text_normalise = re.sub(ARTICLES_PREPOSITIONS, "", text_normalise)
    
    # enlever les caractères spéciaux
    text_normalise = re.sub(r"[^\w\s]", " ", text_normalise)

    # nettoyer les espaces
    text_normalise = re.sub(r"\s+", " ", text_normalise).strip()
    return text_normalise

def enlever_accents(text: str) -> str:
    return "".join(
        c for c in unicodedata.normalize("NFD", text)
        if unicodedata.category(c) != "Mn"
    )

def ajouter_nouvelle_entree_json(description: str, keywords: dict[str, int], json_path: Path, nom_categorie: str = "", overwrite: bool = False) -> bool:

    description_clean = description.strip()
    nouvelle_clef = re.sub(r"\s+", "_", normaliser_text(description)).strip("_")
    nouvelle_entree = {
        "description": description_clean,
        "category" : nom_categorie,
        "keywords": keywords
    }

    # supprime la clé category s'il n'y a aucune catégorie de spécifiée
    if not nom_categorie:
        del nouvelle_entree["category"]

    # essaie de lire à l'intérieur du fichier json et gère l'erreur en cas de json vide.
    try:
        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except (json.JSONDecodeError, FileNotFoundError):
        data = {}

    if nouvelle_clef in data and not overwrite:
        return False
    
    data[nouvelle_clef] = nouvelle_entree
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)
    return True


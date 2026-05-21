import re
import unicodedata
from pathlib import Path
import json

ARTICLES_PREPOSITIONS = r"\b(de|du|la|des|le|les|et|à|au|aux)\b"


def normaliser_text(text: str, stopwords: bool = True) -> str:
    text_nomalise = text.lower().strip()
    

    # enlever les articles et prépositions courants
    if stopwords:
        text_nomalise = re.sub(ARTICLES_PREPOSITIONS, "", text_nomalise)
    
    # enlever les caractères spéciaux
    text_nomalise = re.sub(r"[^\w\s]", " ", text_nomalise)

    # enlever les accents
    text_nomalise = enlever_accents(text)

    # nettoyer les espaces
    text_nomalise = re.sub(r"\s+", " ", text_nomalise).strip()
    return text_nomalise

def enlever_accents(text: str) -> str:
    return "".join(
        c for c in unicodedata.normalize("NFD", text)
        if unicodedata.category(c) != "Mn"
    )

def ajouter_nouvelle_entree_json(description: str, keywords: dict[str, int], json_path: Path, nom_categorie: str = "") -> bool:

    description_clean = description.strip()
    nouvelle_clef = normaliser_text(description).replace(" ", "_")
    nouvelle_entree = {
        "description": description_clean,
        "keywords": keywords
    }

    # ajoute la clé category s'il y a une catégorie de spécifié
    if nom_categorie:
        nouvelle_entree["category"] = nom_categorie

    # essaie de lire à l'intérieur du fichier json et gère l'erreur en cas de json vide.
    try:
        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except (json.JSONDecodeError, FileNotFoundError):
        data = {}

    if nouvelle_clef in data:
        return False
    
    else:
        data[nouvelle_clef] = nouvelle_entree
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
        return True


"""utils.py"""

import re
import unicodedata
import json
from typing import Optional

from .entry_service import JsonNewEntryDraft, EntryExistsError, PanDaFiReError

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
        c for c in unicodedata.normalize("NFD", text) if unicodedata.category(c) != "Mn"
    )


def ajouter_nouvelle_entree_json(brouillon: JsonNewEntryDraft):

    description_clean = brouillon.description.strip()
    nouvelle_clef = generer_clef_json(brouillon.description)
    nouvelle_entree = {
        "description": description_clean,
        "category": brouillon.category,
        "keywords": brouillon.keywords,
    }

    # supprime la clé category s'il n'y a aucune catégorie de spécifiée
    if not brouillon.category:
        del nouvelle_entree["category"]

    # essaie de lire à l'intérieur du fichier json et gère l'erreur en cas de json vide.
    try:
        with open(brouillon.json_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except FileNotFoundError:
        data = {}
    except json.JSONDecodeError as e:
        raise PanDaFiReError(
            f"Le fichier {brouillon.json_path.name} est corrompu : {e}"
        ) from e

    # vérifie si la nouvelle clé existe déjà et que l'option d'écrasement est désactivée.
    if nouvelle_clef in data and not brouillon.overwrite:
        raise EntryExistsError(nouvelle_clef)

    # écriture de la nouvelle entrée dans le JSON
    data[nouvelle_clef] = nouvelle_entree
    try:
        with open(brouillon.json_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
    except OSError as e:
        raise PanDaFiReError(f"Erreur lors de l'écriture dans {brouillon.json_path.name} : {e}") from e


def entree_json_existe(mot_cle: str, config_json: dict) -> bool:
    
    mot_cle_clean = generer_clef_json(mot_cle)
    # print(f"🔍 Vérification de l'existence de la clé '{mot_cle_clean}' dans la configuration...")  # DEBUG
    return mot_cle_clean in config_json


def generer_clef_json(mot_cle: str) -> str:
    return re.sub(r"\s+", "_", normaliser_text(mot_cle)).strip(
        "_"
    )


def ajuster_score_keywords_ambigus(
    keywords: dict[str, int], config_json: dict[str, dict], exclure: str = ""
) -> tuple[dict[str, int], list[str]]:

    config_keywords = []
    keywords_ajustes = []

    # 1. exclure la nouvelle entrée en cours pour éviter l'auto-ajustement en cas d'écrasement
    keyword_exclu = normaliser_text(exclure, stopwords=False)

    # 2. ajouter dans une liste toutes les clés du config_json sauf celle à exclure
    for nom, data in config_json.items():
        if nom == keyword_exclu:
            continue
        config_keywords.extend(data.get("keywords", {}).keys())

    # 3. pour chaque mot clé du keywords, si il existe dans config_keywords et que son score est > 1, le réduire à 1 pour éviter les faux positifs
    for mot_cle, score in keywords.items():
        if mot_cle in config_keywords and score > 1:
            keywords[mot_cle] = 1
            keywords_ajustes.append(mot_cle)

    return keywords, keywords_ajustes

def valider_choix_liste(choix: int, nombre_choix: int) -> Optional[int]:
    """Convertit un choix utilisateur en index de liste."""

    if choix == 0:
        return None
    if 1 <= choix <= nombre_choix:
        return choix - 1
    return None
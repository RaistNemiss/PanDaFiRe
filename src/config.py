"""Chargement centralisé des configurations PanDaFire."""

import json
from pathlib import Path
from typing import Callable

from .config_path import DESTINATAIRE_PATH, TYPEDOC_PATH, EMETTEURS_PATH
from .utils import ajouter_nouvelle_entree_json, entree_json_existe
from .entry_service import JsonNewEntryDraft, ValidationError, EntryExistsError, TypeDeConfig



def charger_config() -> tuple[dict, dict, dict]:
    """Charge et retourne TYPES, EMETTEURS, DESTINATAIRES."""

    types = charger_config_typedoc()
    emetteurs = charger_config_emetteurs()
    destinataires = charger_config_destinataires()

    return types, emetteurs, destinataires


def _charger_json(path: Path, nom: str) -> dict:
    """Charge un fichier JSON avec gestion d'erreur uniforme."""
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError as e:
        raise SystemExit(f"❌ Fichier {nom} dans config/ introuvable : {e}") from e
    except json.JSONDecodeError as e:
        raise SystemExit(f"❌ Fichier {nom} dans config/ invalide : {e}") from e


def charger_config_emetteurs() -> dict:
    return _charger_json(EMETTEURS_PATH, "emetteurs.json")


def charger_config_typedoc() -> dict:
    return _charger_json(TYPEDOC_PATH, "types.json")


def charger_config_destinataires() -> dict:
    # s'assure que le fichier destinataire.json existe et contient au moins une entrée exemple
    init_destinataire_config()
    return _charger_json(DESTINATAIRE_PATH, "destinataire.json")


def init_destinataire_config() -> None:

    # créer le dossier si nécessaire
    DESTINATAIRE_PATH.parent.mkdir(parents=True, exist_ok=True)

    if DESTINATAIRE_PATH.exists():
        return

    
    print("⚠️ destinataire.json introuvable → création du fichier")

    keywords_homer = {
        "homer simpson": 5,
        "+41 77 777 77 77": 6,
        "simpson": 1,
        "homer": 1,
        "homer.simpson@email.com": 6,
    }

    brouillon_homer = JsonNewEntryDraft("destinataires", "Homer Simpson", keywords=keywords_homer, json_path=DESTINATAIRE_PATH)

    ajouter_nouvelle_entree_json(brouillon_homer)

    print("✅ destinataire.json créé avec un utilisateur exemple")


def trouver_categorie_config(nom_emetteur: str, emetteurs: dict) -> str:
    """Trouve la catégorie d'un émetteur à partir de la configuration emetteurs.json. Retourne "inconnu" si l'émetteur n'est pas trouvé ou si la configuration est absente/mal formée."""
    return emetteurs.get(nom_emetteur, {}).get("category", "inconnu")


def categories_disponibles(type_de_config : TypeDeConfig) -> list[str] :
    config_json = charger_config_par_type(type_de_config)
    return list(dict.fromkeys(entree["category"] for entree in config_json.values()))


# Mapping des types de config à leurs fonctions de chargement
_LOADERS : dict[TypeDeConfig, Callable[[], dict]] = {
    "emetteurs": charger_config_emetteurs,
    "typedoc": charger_config_typedoc,
    "destinataires": charger_config_destinataires,
}

def charger_config_par_type(type_config: TypeDeConfig) -> dict:
    """Charge une configuration spécifique (emetteurs, types ou destinataires)."""
    return _LOADERS[type_config]()


def prepare_nouvelle_entree(nouvelle_entree: JsonNewEntryDraft) -> JsonNewEntryDraft: 
    if not nouvelle_entree.description.strip():
        raise ValidationError("Au moins un prénom ou un nom doit être fourni.")
    if entree_json_existe(nouvelle_entree.description, charger_config_par_type(nouvelle_entree.config_type)):
        raise EntryExistsError(nouvelle_entree.description)
    return nouvelle_entree


if __name__ == "__main__":
    pass

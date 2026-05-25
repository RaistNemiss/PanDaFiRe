"""Chargement centralisé des configurations PanDaFire."""

import json
from pathlib import Path

from .config_path import DESTINATAIRE_PATH, TYPES_PATH, EMETTEURS_PATH
from .destinataire import charger_config_destinataires
from .utils import ajouter_nouvelle_entree_json


def charger_config() -> tuple[dict, dict, dict]:
    """Charge et retourne TYPES, EMETTEURS, DESTINATAIRES."""
    types = charger_config_types()
    emetteurs = charger_config_emetteurs()
    destinataires = charger_config_destinataires()


    return types, emetteurs, destinataires

def _charger_json(path: Path, nom: str) -> dict:
    """Charge un fichier JSON avec gestion d'erreur uniforme."""
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError as e:
        raise SystemExit(f"❌ Fichier {nom} dans config/ introuvable : {e}")
    except json.JSONDecodeError as e:
        raise SystemExit(f"❌ Fichier {nom} dans config/ invalide : {e}")


def charger_config_emetteurs() -> dict:
    return _charger_json(EMETTEURS_PATH, "emetteurs.json")


def charger_config_types() -> dict:
    return _charger_json(TYPES_PATH, "types.json")


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
                "homer.simpson@email.com": 6
                }
    
    ajouter_nouvelle_entree_json(
        description="Homer Simpson",
        keywords=keywords_homer,
        json_path=DESTINATAIRE_PATH,
    )

    print("✅ destinataire.json créé avec un utilisateur exemple")
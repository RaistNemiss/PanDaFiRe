"""Chargement centralisé des configurations PanDaFire."""

import json
from .config_path import DESTINATAIRE_PATH, TYPES_PATH, EMETTEURS_PATH
from .destinataire import chargement_destinataires


def charger_config() -> tuple[dict, dict, dict]:
    """Charge et retourne TYPES, EMETTEURS, DESTINATAIRES."""
    try:
        with open(TYPES_PATH, encoding="utf-8") as f:
            types = json.load(f)

        with open(EMETTEURS_PATH, encoding="utf-8") as f:
            emetteurs = json.load(f)

        destinataires = chargement_destinataires(DESTINATAIRE_PATH)

    except FileNotFoundError as e:
        raise SystemExit(f"❌ Fichier de config introuvable : {e}")
    except json.JSONDecodeError as e:
        raise SystemExit(f"❌ Fichier de config invalide : {e}")

    return types, emetteurs, destinataires

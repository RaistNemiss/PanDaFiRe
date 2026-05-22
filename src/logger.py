import json
from datetime import datetime
from pathlib import Path

from .config_path import LOG_PATH

def init_log_file():
    # Si le dossier de logs n'existe pas, on le crée automatiquement pour éviter les erreurs d'écriture du log
    if not LOG_PATH.parent.exists():
        LOG_PATH.parent.mkdir(parents=True, exist_ok=True)

    # si le fichier de log n'existe pas, on le crée pour éviter les erreurs d'écriture du log
    if not LOG_PATH.exists():
        LOG_PATH.touch()

def log_decision(
    pdf_path: Path,
    type_doc: str,
    type_doc_scores: dict[str, int],
    emetteur: str,
    emetteur_scores: dict[str, int],
    emetteur_candidats: list,
    destinataire: str,
    date_doc: str,
    ocr_used: bool,
    fichier_log=LOG_PATH,
    entete_brut_preview: str = "",
    entete_normalise_preview: str = "",
):
    
    log_entry = {
        "timestamp": datetime.now().isoformat(),
        "file": pdf_path.name,
        "type_document": type_doc,
        "type_document_scores": type_doc_scores,
        "emetteur": emetteur,
        "emetteur_scores": emetteur_scores,
        "emetteur_candidats": emetteur_candidats,
        "destinataire": destinataire,
        "date_document": date_doc,
        "ocr_utilisé": ocr_used,
        "entete_brut_preview": entete_brut_preview,
        "entete_normalise_preview": entete_normalise_preview,
    }

    # On initialise le fichier de log s'il n'existe pas déjà (création du dossier et du fichier si nécessaire)
    init_log_file()

    with open(fichier_log, "a", encoding="utf-8") as f:
        f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")

def lire_log(fichier_log=LOG_PATH) -> list[dict]:
    with open(fichier_log, "r", encoding="utf-8") as f:
        return [json.loads(line) for line in f]

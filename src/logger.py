import json
from datetime import datetime
from pathlib import Path

LOG_PATH = Path(__file__).parent.parent / "logs" / "extraction_log.jsonl"

def log_decision(pdf_path: Path, 
                 type_doc: str, 
                 type_doc_scores: dict,
                 emetteur: str, 
                 emetteur_scores: dict,
                 emetteur_candidats: list,
                 date_doc: str,
                 ocr_used: bool,
                 fichier_log=LOG_PATH,
                 ):
    
    log_entry = {
        "timestamp": datetime.now().isoformat(),
        "file": pdf_path.name,
        "type_document": type_doc,
        "type_document_scores": type_doc_scores,
        "emetteur": emetteur,
        "emetteur_scores": emetteur_scores,
        "emetteur_candidats": emetteur_candidats,
        "date_document": date_doc,
        "ocr_utilisé": ocr_used
    }

    with open(fichier_log, "a", encoding="utf-8") as f:
        f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")

def lire_log(fichier_log=LOG_PATH) -> list[dict]:
    with open(fichier_log, "r", encoding="utf-8") as f:
        return [json.loads(line) for line in f]

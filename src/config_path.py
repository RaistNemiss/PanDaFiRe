from pathlib import Path

BASE_PATH = Path(__file__).resolve().parent.parent
CONFIG_PATH = BASE_PATH / "config"
DESTINATAIRE_PATH = CONFIG_PATH / "destinataire.json"
TYPES_PATH = CONFIG_PATH / "types_documents.json"
EMETTEURS_PATH = CONFIG_PATH / "emetteurs.json"
LOG_PATH = BASE_PATH / "logs" / "extraction_log.jsonl"

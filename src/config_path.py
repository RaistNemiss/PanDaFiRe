from pathlib import Path
import os

# Structure attendue :
# projet/
# ├── config/
# │   ├── destinataire.json
# │   ├── types_documents.json
# │   └── emetteurs.json
# ├── logs/
# │   └── extraction_log.jsonl
# └── pandafire/
#     └── config_path.py   ← ce fichier

BASE_PATH = Path(__file__).resolve().parent.parent
CONFIG_PATH = BASE_PATH / "config"
DESTINATAIRE_PATH = CONFIG_PATH / "destinataire.json"
TYPES_PATH = CONFIG_PATH / "types_documents.json"
EMETTEURS_PATH = CONFIG_PATH / "emetteurs.json"
LOG_PATH = BASE_PATH / "logs" / "extraction_log.jsonl"
POPPLER_PATH = Path(os.getenv("POPPLER_PATH", r"C:\TEMP\poppler-26.02.0\Library\bin"))
TESSERACT_PATH = Path(os.getenv("TESSERACT_PATH", r"C:\TEMP\tesseract-5.3.1\tesseract.exe"))

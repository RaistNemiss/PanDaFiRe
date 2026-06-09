from pathlib import Path
import json
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
TYPEDOC_PATH = CONFIG_PATH / "types_documents.json"
EMETTEURS_PATH = CONFIG_PATH / "emetteurs.json"
LOG_PATH = BASE_PATH / "logs" / "extraction_log.jsonl"
SETTINGS_PATH = CONFIG_PATH / "settings.json"
TESSERACT_PATH = Path(os.getenv("TESSERACT_PATH", r"C:\TEMP\Tesseract-OCR\tesseract.exe"))
DEFAULT_OUTPUT_PATH = Path.home() / "Documents"


def _charger_settings() -> dict:
    """Charger les chemins depuis un fichier settings.json si nécessaire."""
    if not SETTINGS_PATH.exists():
        return {}
    try:
        return json.loads(SETTINGS_PATH.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}


def _sauvegarder_settings(settings: dict) -> None:
    SETTINGS_PATH.parent.mkdir(parents=True, exist_ok=True)
    SETTINGS_PATH.write_text(
        json.dumps(settings, indent=4, ensure_ascii=False), encoding="utf-8"
    )


def get_output_path() -> Path:
    settings = _charger_settings()
    return Path(settings.get("output_path", DEFAULT_OUTPUT_PATH))


def set_output_path(path: Path) -> None:
    settings = _charger_settings()
    settings["output_path"] = str(path.resolve())
    _sauvegarder_settings(settings)

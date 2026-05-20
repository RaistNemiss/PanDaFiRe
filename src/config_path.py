from pathlib import Path

BASE_PATH = Path(__file__).resolve().parent.parent
CONFIG_PATH = BASE_PATH / "config"
LOG_PATH = BASE_PATH / "logs" / "extraction_log.jsonl"
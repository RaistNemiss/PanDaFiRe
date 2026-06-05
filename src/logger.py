import json
from datetime import datetime
from pathlib import Path
from typing import Literal
from functools import wraps

from .config_path import LOG_PATH

RunType = Literal["START", "END", "ABORT", "ERROR"]


def init_extraction_log_file():
    # Si le dossier de logs n'existe pas, on le crée automatiquement pour éviter les erreurs d'écriture du log
    if not LOG_PATH.parent.exists():
        LOG_PATH.parent.mkdir(parents=True, exist_ok=True)

    # si le fichier de log n'existe pas, on le crée pour éviter les erreurs d'écriture du log
    if not LOG_PATH.exists():
        LOG_PATH.touch()


def extraction_logger(
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
        "ocr_utilise": ocr_used,
        "entete_brut_preview": entete_brut_preview,
        "entete_normalise_preview": entete_normalise_preview,
    }

    # On initialise le fichier de log s'il n'existe pas déjà (création du dossier et du fichier si nécessaire)
    init_extraction_log_file()

    with open(fichier_log, "a", encoding="utf-8") as f:
        f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")


def lire_extraction_log(fichier_log=LOG_PATH) -> list[dict]:
    if not Path(fichier_log).exists():
        return []
    with open(fichier_log, "r", encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def log_run(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        name = func.__name__
        run_log(name, "START")
        try:
            result = func(*args, **kwargs)
            run_log(name, "END")
            return result
        except KeyboardInterrupt:
            run_log(name, "ABORT", "Ctrl+C")
            raise
        except SystemExit as e:
            # type.Exit / typer.Abort passent par ici
            code = getattr(e, "code", None)
            run_log(name, "ABORT", f"exit code {code}")
            raise
        except Exception as e:
            run_log(name, "ERROR", f"{type(e).__name__}: {e}")
            raise

    return wrapper


def run_log(function_name: str, run_type: RunType, detail: str = "") -> None:
    runlog_path = LOG_PATH.parent / "run.log"
    runlog_path.parent.mkdir(
        parents=True, exist_ok=True
    )  # Assure que le dossier existe

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{timestamp}] {function_name:<12} | {run_type:<6}"
    if detail:
        line += f" | {detail}"

    with open(runlog_path, "a", encoding="utf-8") as f:
        f.write(line + "\n")

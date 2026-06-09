from pathlib import Path
from typing import Literal

from .utils import entree_json_existe
from .config import charger_config_par_type

TypeDeConfig = Literal["emetteurs", "typedoc", "destinataires"]

class ValidationError(Exception):
    """Données invalides fournies."""


class UserExistsError(Exception):
    """L'utilisateur existe déjà."""
    def __init__(self, username: str):
        self.username = username # attribut accessible via e.username
        super().__init__(f"L'utilisateur '{username}' existe déjà.")

class JsonNewEntryDraft():
    config_type: TypeDeConfig
    description: str # nom complet
    keywords: dict[str, int] # mot-clé + score d'importance
    json_path: Path
    category : str = ""
    keywords_ajustes: list[str] = [] # pour éviter de réajouter les mêmes keywords
    overwrite: bool = False

def prepare_nouvelle_entree(nouvelle_entree: JsonNewEntryDraft):
    if not nouvelle_entree.description.strip():
        raise ValidationError("Au moins un prénom ou un nom doit être fourni.")
    if entree_json_existe(nouvelle_entree.description, charger_config_par_type(nouvelle_entree.config_type)):
        raise UserExistsError(nouvelle_entree.description)

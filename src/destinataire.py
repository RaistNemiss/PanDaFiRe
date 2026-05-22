import json
from pathlib import Path
from .utils import ajouter_nouvelle_entree_json


def chargement_destinataires(path: Path) -> dict:
    
    # Initialisation de la configuration des destinataires (création du fichier destinataire.json s'il n'existe pas déjà)
    init_destinataire_config(path)

    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def init_destinataire_config(destinataire_json_path: Path) -> None:
    
    # créer le dossier si nécessaire
    destinataire_json_path.parent.mkdir(parents=True, exist_ok=True)

    if destinataire_json_path.exists():
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
        json_path=destinataire_json_path,
    )

    print("✅ destinataire.json créé avec un utilisateur exemple")

def determiner_initiales_destinataire(nom: str) -> str:

    if not nom or nom == "inconnu":
        return ""

    mots = nom.split()

    if len(mots) == 2:
        # 1 lettre du prénom + 2 lettres du nom (ex: Homer Simpson → HSI)
        return (mots[0][:1] + mots[1][:2]).upper()

    if len(mots) == 1:
        # 2 premières lettres (ex: Homer → HO)
        return nom[:2].upper()

    # 1 lettre par mot (ex: Jean Claude Van Damme → JCVD)
    return "".join(mot[0] for mot in mots).upper()

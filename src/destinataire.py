import json
from pathlib import Path
from .utils import ajouter_nouvelle_entree_json


def chargement_destinataires(path: Path, debug: bool = False) -> dict:
    
    # Initialisation de la configuration des destinataires (création du fichier destinataire.json s'il n'existe pas déjà)
    init_destinataire_config(path, debug=debug)

    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def init_destinataire_config(destinataire_json_path: Path, debug: bool = False) -> None:
    
    # créer le dossier si nécessaire
    destinataire_json_path.parent.mkdir(parents=True, exist_ok=True)

    if destinataire_json_path.exists():
        return

    print("⚠️ destinataire.json introuvable → création du fichier")

    coordonees = {
                "homer simpson": 5,
                "+41 77 777 77 77": 6,
                "simpson": 1,
                "homer": 1,
                "homer.simpson@email.com": 6
                }
    
    ajouter_nouvelle_entree_json(
        description="Homer Simpson",
        keywords=coordonees,
        json_path=destinataire_json_path,
    )

    print("✅ destinataire.json créé avec un utilisateur exemple")
    return

def determiner_initiales_destinataire(nom: str) -> str:
    
    if nom == "inconnu" or nom == "":
        return ""
    
    # extraire les initiales du nom du destinataire (ex: "Homer Simpson" → "HS") pour maximiser les chances de correspondance même si le nom complet n'est pas mentionné dans le document
    mots = nom.split()
    
    if len(mots) == 2:
        return (mots[0][:1] + mots[1][:2]).upper()  # Prend la première lettre du premier mot et les deux premières lettres du second mot (ex: Homer Simpson → HSI)
    if len(mots) == 1:
        return nom[:2].upper()  # si le nom ne comporte qu'un mot, prendre les 2 premières lettres comme initiales
    else:
        return "".join(mot[0] for mot in mots).upper()  # sinon, prendre la première lettre de chaque mot (ex: Jean Claude Van Damme → JCVD)
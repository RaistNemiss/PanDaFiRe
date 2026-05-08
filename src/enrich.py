import json
from pathlib import Path
from collections import Counter


def candidats_frequents(logs: list[dict]) -> list[tuple[str, int]]:

    emetteurs = []
    seuil_occurrence = (
        5  # seuil de fréquence pour considérer un candidat comme pertinent
    )

    for log in logs:
        emetteurs.extend(log.get("emetteur_candidats", []))

    counter = Counter(emetteurs)

    return [
        (emetteur, occurrence)
        for emetteur, occurrence in counter.most_common()
        if occurrence >= seuil_occurrence
    ]


def ajouter_emetteur_json(emetteur_select: str, categorie_emetteur: str, emetteur_json_path: Path) -> None:
    
    nouveau_emetteur = emetteur_select.strip()
    nouvelle_clé_emetteur = (nouveau_emetteur.lower().replace(" ", "_"))


    nouvelle_entree = {
        "description": nouveau_emetteur,
        "category": categorie_emetteur,
        "mot_clef": {
            nouveau_emetteur.lower(): 5,
            },
        }

    with open(emetteur_json_path, "r", encoding="utf-8") as f:
        data_emetteurs = json.load(f)

    data_emetteurs[nouvelle_clé_emetteur] = nouvelle_entree

    with open(emetteur_json_path, "w", encoding="utf-8") as f:
        json.dump(data_emetteurs, f, indent=4, ensure_ascii=False)
    
    print(f"✅ Émetteur ajouté : {nouvelle_clé_emetteur}")
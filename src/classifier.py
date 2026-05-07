import re

def identifier_par_score(texte: str, config: dict, seuil: int = 4, retour_score: bool = False):
    # normalisation du texte pour faciliter la recherche
    texte = texte.lower()
    texte = re.sub(r"\s+", " ", texte)

    # création d'une compréhension de dictionnaire pour compter les occurrences de mots-clés pour chaque type de document
    scores = {cle: 0 for cle in config}

    for cle, data in config.items():
        mots_cle = data["mot_clef"]
        for mot, valeur_mot in mots_cle.items():
            if len(mot) < 3:  # éviter que les mots trop génère des faux positifs (ex: UBS dans sUBScription)
                nombre_occurrences = len(re.findall(rf"(!<?w){re.escape(mot)}(!?\w)", texte))
            else:
                nombre_occurrences = len(re.findall(rf"\b{re.escape(mot)}\b", texte))

            scores[cle] += nombre_occurrences * int(valeur_mot)
    gagnant = max(scores, key=scores.get)
    # seuil de confiance pour éviter les faux positifs
    resultat = gagnant if scores[gagnant] >= seuil else "inconnu"

    if retour_score:
        return resultat, scores
    
    return gagnant
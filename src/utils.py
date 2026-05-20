import re
import unicodedata

ARTICLES_PREPOSITIONS = r"\b(de|du|la|des|le|les|et|à|au|aux)\b"


def normaliser_text(text: str, stopwords: bool = True) -> str:
    text_nomalise = text.lower().strip()
    

    # enlever les articles et prépositions courants
    if stopwords:
        text_nomalise = re.sub(ARTICLES_PREPOSITIONS, "", text_nomalise)
    
    # enlever les caractères spéciaux
    text_nomalise = re.sub(r"[^\w\s]", " ", text_nomalise)

    # enlever les accents
    text_nomalise = enlever_accents(text)

    # nettoyer les espaces
    text_nomalise = re.sub(r"\s+", " ", text_nomalise).strip()
    return text_nomalise

def enlever_accents(text: str) -> str:
    return "".join(
        c for c in unicodedata.normalize("NFD", text)
        if unicodedata.category(c) != "Mn"
    )
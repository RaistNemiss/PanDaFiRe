# PanDaFiRe

Outil Python pour analyser et renommer automatiquement des fichiers PDF :
- analyser des PDF
- déterminer le type de document
- identifier l'émetteur
- extraire la date
- renommer automatiquement les fichiers

## Fonctionnalités

- Extraction PDF (pdfplumber)
- OCR (Tesseract)
- Classification par scoring
- Identification de l'émetteur
- Extraction de date
- CLI avec Typer

## Installation

```bash
pip install -r requirements.txt
```

## Usage

```bash
python -m src.main run fichier.pdf
```

Traitement d'un dossier entier :

```bash
python -m src.main run dossier_pdf
```

Traitement d'un dossier et de ses sous-dossiers :

```bash
python -m src.main run dossier_pdf --recursive
```

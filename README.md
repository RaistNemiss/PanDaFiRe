```markdown
# PanDaFiRe 🐼🔥

Outil Python pour analyser et renommer automatiquement des fichiers PDF :
- 📄 analyser des PDF (texte + OCR)
- 🏷️ déterminer le type de document
- 👤 identifier l'émetteur / destinataire
- 📅 extraire la date du document
- ✏️ renommer automatiquement les fichiers

## Fonctionnalités

- 📑 Extraction PDF (pdfplumber)
- 🔍 OCR pour les PDF scannés (Tesseract + Poppler)
- 🎯 Classification par scoring de mots-clés
- 👥 Identification de l'émetteur et du destinataire
- 📆 Extraction et normalisation de la date
- 🖥️ CLI avec Typer
- 🧪 Mode `--dry-run` pour prévisualiser sans renommer
- 📁 Traitement récursif des dossiers

## Prérequis

### Dépendances système

PanDaFiRe nécessite **Tesseract** (OCR).

#### 🪟 Windows

1. **Tesseract-OCR**
   - Télécharger : https://github.com/UB-Mannheim/tesseract/wiki
   - Installer (par défaut : `C:\Program Files\Tesseract-OCR\`)
   - ⚠️ Pense à installer le pack de langue **français** lors de l'installation

2. **Configurer les chemins** via variables d'environnement (recommandé) :
   ```powershell
   setx TESSERACT_PATH "C:\Program Files\Tesseract-OCR\tesseract.exe"
   ```
   *(ou éditer directement `src/config_path.py`)*

#### 🐧 Linux (Debian/Ubuntu)

```bash
sudo apt update
sudo apt install tesseract-ocr tesseract-ocr-fra
```

#### 🍎 macOS (Homebrew)

```bash
brew install tesseract tesseract-lang
```

### Python

Python **3.10+** recommandé.

## Installation

```bash
git clone https://github.com/RaistNemiss/PanDaFiRe.git
cd PanDaFiRe
pip install -r requirements.txt
```

## Usage

### Renommer un PDF

```bash
python -m src.main run fichier.pdf
```

### Traitement d'un dossier

```bash
python -m src.main run dossier_pdf
```

### Traitement récursif (sous-dossiers inclus)

```bash
python -m src.main run dossier_pdf --recursive
```

### Mode dry-run (simulation sans renommage)

```bash
python -m src.main run dossier_pdf --dry-run
```

### Enregistrer un nouveau destinataire

```bash
python -m src.main register
```

### Déplacer les fichiers dans des dossiers de sortie

```bash
python -m src.main run fichier.pdf -output
```

### Définir le dossier de sortie des fichiers.

```bash
python -m src.main set-output
```

Une saisie interactive te demandera nom, prénom, email, téléphone, etc.

## Structure du projet

```
PanDaFiRe/
├── src/
│   ├── main.py              # CLI (Typer)
│   ├── ocr.py               # OCR Tesseract + Poppler
│   ├── extraction.py        # Extraction texte/date
│   ├── classification.py    # Scoring & type de document
│   ├── destinataire.py      # Gestion des destinataires
│   ├── config_path.py       # Chemins (Tesseract, Poppler, JSON)
│   └── ...
├── data/
│   └── destinataires.json   # Base des destinataires
├── requirements.txt
└── README.md
```

## Licence


MIT — voir [LICENSE](LICENSE)

## Auteur

**Raist Nemiss**
```


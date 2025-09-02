#!/bin/bash
# Script d'installation de Python 3.13 et PyInstaller dans un préfixe Wine
# Usage : bash install_python_wine.sh

set -e

# Variables
PYTHON_VERSION=3.13.0
PYTHON_MSI=python-${PYTHON_VERSION}-amd64.exe
PYTHON_URL="https://www.python.org/ftp/python/${PYTHON_VERSION}/${PYTHON_MSI}"
WINEPREFIX=${WINEPREFIX:-$HOME/.wine}

# 1. Télécharger l'installeur Python
if [ ! -f "$PYTHON_MSI" ]; then
    echo "Téléchargement de $PYTHON_MSI ..."
    wget "$PYTHON_URL"
fi

# 2. Installer Python dans Wine
wine "$PYTHON_MSI" /quiet InstallAllUsers=1 PrependPath=1 Include_pip=1

# 3. Vérifier l'installation
wine python --version

# 4. Installer pip si besoin (souvent déjà inclus)
wine python -m ensurepip || true

# 5. Mettre à jour pip
wine python -m pip install --upgrade pip

# 6. Installer PyInstaller
wine python -m pip install pyinstaller

echo "Installation terminée. Utilisez 'wine python' et 'wine pyinstaller' pour builder vos scripts."

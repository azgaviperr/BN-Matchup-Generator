# Makefile pour Matchup Generator

PYTHON=python3
PYINSTALLER=$(PYTHON) -m PyInstaller
SRC_DIR=${PWD}
DIST_DIR=dist
BUILD_DIR=build

LINUX_DIST=$(DIST_DIR)/linux
WINDOWS_DIST=$(DIST_DIR)/windows
MACOS_DIST=$(DIST_DIR)/macos

LINUX_EXPORT=$(DIST_DIR)/linux
WINDOWS_EXPORT=$(DIST_DIR)/windows
MACOS_EXPORT=$(DIST_DIR)/macos

.PHONY: all build build_all clean distclean linux windows macos help install_python_wine

all: build

build:
	$(PYTHON) build.py

install_python_wine:
	bash install_python_wine.sh
	find $(SRC_DIR) -type f -name 'python*.exe' -delete

build_all:
	$(MAKE) linux
	$(MAKE) macos
	$(MAKE) windows

linux:
	$(PYINSTALLER) --distpath $(LINUX_DIST) --workpath $(BUILD_DIR) --specpath $(BUILD_DIR) --clean --onefile $(SRC_DIR)/matchup_generator.py
	$(PYINSTALLER) --distpath $(LINUX_EXPORT) --workpath $(BUILD_DIR) --specpath $(BUILD_DIR) --clean --onefile $(SRC_DIR)/export_tourplay.py

windows:
	wine python -m PyInstaller --distpath $(WINDOWS_DIST) --workpath $(BUILD_DIR) --specpath $(BUILD_DIR) --clean --onefile $(SRC_DIR)/matchup_generator.py
	wine python -m PyInstaller --distpath $(WINDOWS_EXPORT) --workpath $(BUILD_DIR) --specpath $(BUILD_DIR) --clean --onefile $(SRC_DIR)/export_tourplay.py

macos:
	$(PYINSTALLER) --distpath $(MACOS_DIST) --workpath $(BUILD_DIR) --specpath $(BUILD_DIR) --clean --onefile $(SRC_DIR)/matchup_generator.py
	$(PYINSTALLER) --distpath $(MACOS_EXPORT) --workpath $(BUILD_DIR) --specpath $(BUILD_DIR) --clean --onefile $(SRC_DIR)/export_tourplay.py

clean:
	@echo "Nettoyage des fichiers générés..."
	@if [ -d "$(BUILD_DIR)" ]; then rm -rf $(BUILD_DIR); fi
	@if [ -d "$(DIST_DIR)" ]; then rm -rf $(DIST_DIR); fi
	@if [ -d "__pycache__" ]; then rm -rf __pycache__; fi
	@if [ -d ".pytest_cache" ]; then rm -rf .pytest_cache; fi
	@find $(SRC_DIR) -name '*.spec' -delete
	@find $(SRC_DIR) -name '__pycache__' -type d -exec rm -rf {} +
	@find . -maxdepth 1 -name '*.spec' -delete
	@find . -name 'NUL' -delete
	@find . -type f -name '*.exe' -delete
	@find $(SRC_DIR) -type f -name 'python*.exe' -delete
	@echo "Nettoyage terminé."

help:
	@echo "Cibles disponibles :"
	@echo "  build         : Génère les éxécutables pour la plateforme courante via build.py"
	@echo "  build_all     : Build pour Linux, MacOS, Windows (auto-install python_wine.sh sous Linux)"
	@echo "  linux         : Build Linux uniquement (PyInstaller requis)"
	@echo "  windows       : Build Windows (nécessite wine + PyInstaller)"
	@echo "  macos         : Build MacOS uniquement (PyInstaller requis)"
	@echo "  clean         : Supprime tous les fichiers générés et dossiers de build"
	@echo "  help          : Affiche cette aide"

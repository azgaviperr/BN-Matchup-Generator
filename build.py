# build.py
"""
Script de build pour packager les scripts Python en exécutables pour Linux, Mac et 
Windows. Utilise PyInstaller pour générer des exécutables standalone.

Usage :
    python build.py

Prérequis :
    pip install pyinstaller
"""
import os
import sys
import subprocess
import platform

# Définition des chemins et des scripts
SCRIPTS_DIR = os.path.dirname(
    os.path.abspath(__file__)
)  # Chemin vers le répertoire du script
SCRIPTS = [
    "matchup_generator.py",
    "export_tourplay.py"
]

DIST_DIR = "dist"

# Définition des cibles (plateforme, commande python, arguments PyInstaller)
TARGETS = [
    ("linux",   "python3",  []),
    ("windows", "python",   ["--windowed"]),
    ("macos",   "python3",  [])
]

def build_script(script_path, platform_name, python_cmd, extra_args=None):
    """
    Construit la commande PyInstaller pour un script et une plateforme donnés.
    Retourne la liste des arguments de la commande.
    """
    base_name = os.path.splitext(os.path.basename(script_path))[0]
    
    # Crée un chemin de distribution spécifique à la plateforme
    dist_path = os.path.join(DIST_DIR, platform_name)
    
    # Construction de la commande PyInstaller
    cmd = [python_cmd, "-m", "PyInstaller"]
    
    # Ajout des options de construction
    cmd.extend([
        "--distpath", dist_path,
        "--workpath", "build",
        "--specpath", "build",
        "--clean",
        "--onefile"
    ])
    
    # Ajout d'arguments supplémentaires si présents
    if extra_args:
        cmd.extend(extra_args)
    
    # Ajout du script à la fin de la commande
    cmd.append(script_path)
    
    return cmd

if __name__ == "__main__":
    print("== Build des scripts pour Linux, Windows et MacOS ==")
    
    # Détecte le système d'exploitation actuel pour exécuter le build natif
    current_os = platform.system().lower()
    
    # Crée le répertoire 'dist' si il n'existe pas
    os.makedirs(DIST_DIR, exist_ok=True)
    
    for script in SCRIPTS:
        script_path = os.path.join(SCRIPTS_DIR, script)
        print(f"\n--- Préparation du build pour '{script}' ---")
        
        for plat, pycmd, extra in TARGETS:
            # Construit la commande pour chaque plateforme cible
            cmd = build_script(script_path, plat, pycmd, extra_args=extra)
            
            # Vérifie si la plateforme cible correspond au système actuel
            if (plat == "linux" and current_os.startswith("linux")) or \
               (plat == "windows" and current_os.startswith("win")) or \
               (plat == "macos" and current_os.startswith("darwin")):
                
                print(f"Exécution du build pour {plat}...")
                try:
                    # Exécute la commande PyInstaller
                    subprocess.run(cmd, check=True)
                    print(f"Build pour {plat} terminé avec succès.")
                except subprocess.CalledProcessError as e:
                    print(f"Erreur lors du build pour {plat}. Vérifiez l'erreur PyInstaller ci-dessus : {e}")
                except FileNotFoundError:
                    print(f"Erreur : La commande Python '{pycmd}' est introuvable. Assurez-vous que Python est dans votre PATH.")
            else:
                # Affiche la commande à exécuter sur les autres plateformes
                print(
                    f"(Info) Pour {plat}, exécutez cette commande sur la plateforme cible :\n"
                    f"{' '.join(str(c) for c in cmd)}"
                )
    
    print(
        "\n== Build terminé (ou commandes à exécuter sur chaque OS). Les exécutables "
        "sont dans le dossier 'dist/'."
    )

import sys
import json
import csv
import requests
from bs4 import BeautifulSoup
import tkinter as tk
from tkinter import filedialog, simpledialog, messagebox, scrolledtext
try:
    from requests_html import HTMLSession
    REQUESTS_HTML_AVAILABLE = True
except ImportError:
    REQUESTS_HTML_AVAILABLE = False

def load_html(source):
    """Charge le HTML depuis un fichier local ou une URL (avec JS si possible)."""
    if source.startswith('http://') or source.startswith('https://'):
        headers = {
            'User-Agent': (
                'Mozilla/5.0 (Linux; Android 10; SM-G996U Build/QP1A.190711.020; wv) '
                'AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Mobile Safari/537.36'
            )
        }
        if REQUESTS_HTML_AVAILABLE:
            session = HTMLSession()
            resp = session.get(source, headers=headers, timeout=15)
            try:
                resp.html.render(timeout=20)
            except Exception as e:
                raise RuntimeError(f"Erreur lors du rendu JavaScript : {e}")
            return resp.html.html
        else:
            resp = requests.get(source, headers=headers, timeout=15)
            resp.raise_for_status()
            return resp.text
    else:
        with open(source, encoding="utf-8") as file:
            return file.read()

def extract_tourplay_data(html_content):
    """
    Extrait tous les coachs, équipes et rosters à partir du HTML.
    Retourne une liste de dictionnaires.
    """
    soup = BeautifulSoup(html_content, 'html.parser')
    results = []
    
    # Recherche tous les blocs mat-list-item qui contiennent les informations
    import re
    for item in soup.find_all('mat-list-item'):
        # Extraction du nom du coach
        coach_div = item.find('div', class_='ellipsis', style='line-height: 16px;')
        coach_name_full = coach_div.find('span').text.strip() if coach_div and coach_div.find('span') else "Non trouvé"
        # Séparation du groupe/ligue uniquement si ' · ' (point milieu) ou ' - ' (tiret entouré d'espaces)
        m = re.match(r"^(.*?)(?:\s*[·]\s*(\w+))?$", coach_name_full)
        if not m or not m.group(2):
            # Essai avec ' - ' entouré d'espaces (mais pas un simple tiret)
            m2 = re.match(r"^(.*?)(?:\s-\s(\w+))$", coach_name_full)
            if m2:
                coach_name = m2.group(1).strip()
                groupe = m2.group(2)
            else:
                coach_name = coach_name_full
                groupe = ""
        else:
            coach_name = m.group(1).strip()
            groupe = m.group(2)

        # Extraction du nom de l'équipe
        team_div = item.find('div', class_='ellipsis title-roster-list')
        team_name = team_div.text.strip() if team_div else "Non trouvé"

        # Extraction du roster (race)
        roster_span = item.find('span', class_='mat-caption--small ng-star-inserted')
        roster = roster_span.text.strip() if roster_span else "Non trouvé"

        results.append({
            "coach": coach_name,
            "groupe": groupe,
            "team": team_name,
            "roster": roster
        })
    
    # Trie les résultats par nom de coach
    results = sorted(results, key=lambda x: x["coach"].lower())
    
    # Ajoute un numéro de position à chaque entrée
    for idx, row in enumerate(results, 1):
        row["num"] = idx
        
    return results

def show_results(results):
    """Affiche les résultats dans une fenêtre Tkinter."""
    result_text = f"Nombre de coachs extraits : {len(results)}\n\n"
    for row in results:
        result_text += (
            f"{row['num']} - Coach : {row['coach']} | Équipe : {row['team']} | "
            f"Roster : {row['roster']}\n"
        )
    
    result_window = tk.Toplevel()
    result_window.title("Résultats de l'extraction")
    text_area = scrolledtext.ScrolledText(result_window, width=100, height=30)
    text_area.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
    text_area.insert(tk.END, result_text)
    text_area.config(state=tk.DISABLED)

def save_results(results):
    """Sauvegarde les résultats dans des fichiers JSON et CSV."""
    import os
    export_dir = "tourplay_data_exported"
    os.makedirs(export_dir, exist_ok=True)

    json_filename = os.path.join(export_dir, "coachs_extract.json")
    with open(json_filename, "w", encoding="utf-8") as fjson:
        json.dump(results, fjson, ensure_ascii=False, indent=2)

    csv_filename = os.path.join(export_dir, "coachs_extract.csv")
    fieldnames = ["num", "coach", "groupe", "team", "roster"]
    with open(csv_filename, "w", encoding="utf-8", newline='') as fcsv:
        writer = csv.DictWriter(fcsv, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(results)

    messagebox.showinfo(
        "Sauvegarde réussie",
        f"Les données ont été exportées dans le dossier '{export_dir}' :\n\n"
        f"'{json_filename}'\n"
        f"'{csv_filename}'"
    )

def handle_extraction(source):
    """Gère le flux d'extraction, d'affichage et de sauvegarde."""
    try:
        html_content = load_html(source)
        results = extract_tourplay_data(html_content)
        show_results(results)
        save_results(results)
    except Exception as e:
        messagebox.showerror("Erreur", f"Une erreur est survenue lors de l'extraction : {e}")

def select_file():
    """Ouvre une boîte de dialogue pour sélectionner un fichier."""
    file_path = filedialog.askopenfilename(
        title="Sélectionner un fichier HTML",
        filetypes=[("Fichiers HTML", "*.htm;*.html"), ("Tous les fichiers", "*.*")]
    )
    if file_path:
        handle_extraction(file_path)

def enter_url():
    """Demande à l'utilisateur d'entrer une URL."""
    url = simpledialog.askstring("Entrer une URL", "Veuillez entrer l'URL de la page HTML :")
    if url:
        handle_extraction(url)

def load_coachs_from_json(json_path):
    """Charge les coachs depuis un fichier JSON."""
    with open(json_path, encoding="utf-8") as f:
        return json.load(f)

def load_coachs_from_csv(csv_path):
    """Charge les coachs depuis un fichier CSV."""
    with open(csv_path, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        return [row for row in reader]

def main_ui():
    """Initialise l'interface graphique principale."""
    root = tk.Tk()
    root.title("Extracteur Coachs Tourplay")
    root.geometry("500x200")
    
    label = tk.Label(root, text="Sélectionnez la source des données à extraire :", font=("Arial", 14))
    label.pack(pady=20)
    
    btn_file = tk.Button(root, text="Charger depuis un fichier local", command=select_file, width=30)
    btn_file.pack(pady=10)
    
    btn_url = tk.Button(root, text="Charger depuis une URL", command=enter_url, width=30)
    btn_url.pack(pady=10)
    
    root.mainloop()

if __name__ == "__main__":
    main_ui()
import sys
import json
import csv
import os
import re
import requests
from bs4 import BeautifulSoup
import tkinter as tk
from tkinter import filedialog, simpledialog, messagebox, scrolledtext
try:
    from requests_html import HTMLSession
    REQUESTS_HTML_AVAILABLE = True
except ImportError:
    REQUESTS_HTML_AVAILABLE = False


TOURPLAY_API_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/128.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "fr,en;q=0.9",
    "X-Requested-With": "XMLHttpRequest",
}


def resolve_local_source(source):
    """Resolve a local HTML source, including browser-saved *_files folders."""
    if os.path.isdir(source):
        normalized_source = os.path.normpath(source)
        if normalized_source.endswith('_files'):
            html_source = normalized_source[:-6] + '.htm'
            if os.path.isfile(html_source):
                return html_source
            html_source = normalized_source[:-6] + '.html'
            if os.path.isfile(html_source):
                return html_source
        raise FileNotFoundError(
            "Le chemin fourni est un dossier. Fournissez un fichier .htm/.html, "
            "ou un dossier '_files' accompagné de sa page HTML sauvegardée."
        )
    return source

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
        source = resolve_local_source(source)
        with open(source, encoding="utf-8") as file:
            return file.read()


def extract_expected_participant_count(html_content):
    """Extract the participant count displayed by Tourplay when available."""
    soup = BeautifulSoup(html_content, 'html.parser')
    count_badge = soup.select_one('span.mat-caption.bb-title')
    if not count_badge:
        return None

    match = re.search(r'\d+', count_badge.get_text(" ", strip=True))
    return int(match.group()) if match else None


def extract_tourplay_url(source, html_content):
    """Resolve the Tourplay page URL from the source argument or saved HTML."""
    if source.startswith('http://') or source.startswith('https://'):
        return source

    soup = BeautifulSoup(html_content, 'html.parser')
    og_url = soup.find('meta', attrs={'property': 'og:url'})
    if og_url and og_url.get('content'):
        return og_url['content']
    return None


def fetch_tourplay_api_results(source, html_content):
    """Fetch the complete participant list from Tourplay's API."""
    page_url = extract_tourplay_url(source, html_content)
    if not page_url or '/blood-bowl/' not in page_url:
        return None

    path_parts = page_url.rstrip('/').split('/')
    if len(path_parts) < 2:
        return None

    tournament_name = path_parts[-2] if path_parts[-1] == 'players' else path_parts[-1]
    referer = page_url
    headers = dict(TOURPLAY_API_HEADERS)
    headers['Referer'] = referer

    tournament_response = requests.get(
        f'https://tourplay.net/api/tournament/{tournament_name}',
        headers=headers,
        timeout=30,
    )
    tournament_response.raise_for_status()
    tournament = tournament_response.json()

    categories = tournament.get('categories', [])
    if not categories:
        return None

    category = max(categories, key=lambda item: item.get('inscriptionsCoachCount', 0))
    category_id = category.get('id')
    if not category_id:
        return None

    page_size = max(category.get('inscriptionsCoachCount', 0), 100)
    inscriptions_response = requests.get(
        f'https://tourplay.net/api/inscriptions/{tournament_name}/category/{category_id}/inscriptions',
        headers=headers,
        params={'page': 0, 'pageSize': page_size},
        timeout=30,
    )
    inscriptions_response.raise_for_status()
    inscriptions_payload = inscriptions_response.json()
    inscriptions = inscriptions_payload.get(str(category_id), [])
    if not inscriptions:
        return None

    results = []
    for inscription in inscriptions:
        player = inscription.get('player', {})
        roster = inscription.get('roster', {})
        results.append({
            'coach': player.get('userNameToShow', 'Non trouve'),
            'groupe': '',
            'team': roster.get('shortTeamName') or 'Non trouvé',
            'roster': roster.get('teamRace') or 'Non trouvé',
        })

    return results


def normalize_results(results):
    """Sort extracted rows and assign their display index."""
    normalized_results = sorted(results, key=lambda row: row['coach'].lower())
    for idx, row in enumerate(normalized_results, 1):
        row['num'] = idx
    return normalized_results

def extract_tourplay_data(html_content):
    """
    Extrait tous les coachs, équipes et rosters à partir du HTML.
    Retourne une liste de dictionnaires.
    """
    soup = BeautifulSoup(html_content, 'html.parser')
    results = []

    participant_items = soup.select('a.mat-list-item[href*="/roster/"]')
    if not participant_items:
        participant_items = soup.find_all('mat-list-item')

    for item in participant_items:
        if item.name == 'a':
            coach_row = item.find('div', class_='row-flex', style=lambda s: s and 'justify-content: flex-start' in s)
            team_row = item.find('div', class_='row-flex', style=lambda s: s and 'justify-content: flex-end' in s)
            coach_span = coach_row.find('span', class_=lambda c: c and 'ellipsis' in c) if coach_row else None
            coach_name_full = coach_span.get_text(strip=True) if coach_span else "Non trouvé"
            team_div = team_row.find('div', class_=lambda c: c and 'title-roster-list' in c) if team_row else None
            team_name = team_div.get_text(strip=True) if team_div and team_div.get_text(strip=True) else "Non trouvé"
            roster_span = team_row.find('span', class_=lambda c: c and 'mat-caption' in c) if team_row else None
            roster = roster_span.get_text(strip=True) if roster_span and roster_span.get_text(strip=True) else "Non trouvé"
        else:
            coach_div = item.find('div', class_='ellipsis', style='line-height: 16px;')
            coach_name_full = coach_div.find('span').text.strip() if coach_div and coach_div.find('span') else "Non trouvé"
            team_div = item.find('div', class_='ellipsis title-roster-list')
            team_name = team_div.text.strip() if team_div else "Non trouvé"
            roster_span = item.find('span', class_='mat-caption--small ng-star-inserted')
            roster = roster_span.text.strip() if roster_span else "Non trouvé"

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

        results.append({
            "coach": coach_name,
            "groupe": groupe,
            "team": team_name,
            "roster": roster
        })
    
    return normalize_results(results)

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

def save_results(results, show_message=True):
    """Sauvegarde les résultats dans des fichiers JSON et CSV."""
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

    if show_message:
        messagebox.showinfo(
            "Sauvegarde réussie",
            f"Les données ont été exportées dans le dossier '{export_dir}' :\n\n"
            f"'{json_filename}'\n"
            f"'{csv_filename}'"
        )

    return json_filename, csv_filename

def handle_extraction(source, cli_mode=False):
    """Gère le flux d'extraction, d'affichage et de sauvegarde."""
    try:
        html_content = load_html(source)
        results = extract_tourplay_data(html_content)
        expected_participants = extract_expected_participant_count(html_content)

        if expected_participants and len(results) < expected_participants:
            api_results = fetch_tourplay_api_results(source, html_content)
            if api_results and len(api_results) >= len(results):
                results = normalize_results(api_results)

        if cli_mode:
            json_filename, csv_filename = save_results(results, show_message=False)
            print(f"Extraction réussie : {len(results)} coachs exportés.")
            print(json_filename)
            print(csv_filename)
        else:
            show_results(results)
            save_results(results)
    except Exception as e:
        if cli_mode:
            print(f"Erreur lors de l'extraction : {e}", file=sys.stderr)
            raise SystemExit(1) from e
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
    if len(sys.argv) > 1:
        handle_extraction(sys.argv[1], cli_mode=True)
    else:
        main_ui()
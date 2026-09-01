# coding: utf-8
# V3 - Générateur de plannings de matchs

import random
from typing import List, Tuple, Dict, Any, Set
import csv
import os
import json
from datetime import datetime
import shutil
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import re
import unicodedata

# Installation des dépendances pour PDF/PNG si nécessaire
try:
    import pandas as pd
    from reportlab.lib.pagesizes import A4
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle
    from reportlab.lib import colors
    import matplotlib.pyplot as plt
    PANDAS_INSTALLED = True
except ImportError:
    PANDAS_INSTALLED = False
    print("Les bibliothèques 'pandas', 'reportlab' et 'matplotlib' ne sont pas installées. Les exports PDF et PNG seront désactivés.")


def remove_accents(input_str: str) -> str:
    """Removes accents from a string and converts it to lowercase and removes combining characters."""
    nfkd_form = unicodedata.normalize('NFKD', input_str)
    return "".join([c for c in nfkd_form if not unicodedata.combining(c)])


class MatchupGenerator:
    """
    Générateur de plannings de matchs.
    Garantit que chaque paire de coachs ne se rencontre qu'une seule fois.
    """

    def __init__(self, n_teams: int, n_days: int):
        if n_teams % 2 != 0:
            raise ValueError(
                "Le nombre d'équipes doit être pair.")
        self.n_teams = n_teams
        self.n_days = n_days
        self.teams = list(range(1, n_teams + 1))
        self.schedule: Dict[str, List[Tuple[int, int]]] = {}
        self.all_possible_matches: List[Tuple[int, int]] = []
        for i in range(1, n_teams + 1):
            for j in range(i + 1, n_teams + 1):
                self.all_possible_matches.append(tuple(sorted((i, j))))

    def _find_day_matching(self, available: Set[Tuple[int, int]]) -> List[Tuple[int, int]]:
        """
        Cherche aléatoirement un appariement complet de la journée : chaque coach
        joue exactement une fois, uniquement contre un adversaire non encore rencontré.
        Retourne la liste des rencontres, ou une liste vide si aucune n'existe.
        """
        neighbours: Dict[int, Set[int]] = {team: set() for team in self.teams}
        for a, b in available:
            neighbours[a].add(b)
            neighbours[b].add(a)

        day_matches: List[Tuple[int, int]] = []
        unmatched = set(self.teams)

        def backtrack() -> bool:
            if not unmatched:
                return True
            # Heuristique : traiter d'abord le coach ayant le moins d'adversaires possibles
            team = min(unmatched, key=lambda t: len(neighbours[t] & unmatched))
            candidates = list(neighbours[team] & unmatched)
            random.shuffle(candidates)
            unmatched.discard(team)
            for opponent in candidates:
                unmatched.discard(opponent)
                day_matches.append(tuple(sorted((team, opponent))))
                if backtrack():
                    return True
                day_matches.pop()
                unmatched.add(opponent)
            unmatched.add(team)
            return False

        if backtrack():
            return day_matches
        return []

    def generate(self, max_attempts: int = 100) -> bool:
        """
        Génère un planning de matchs en s'assurant qu'aucune rencontre n'est répétée.
        Chaque journée est tirée au sort indépendamment (pas de round-robin fixe),
        parmi les rencontres encore disponibles.

        `max_attempts` limite le nombre de tirages complets relancés lorsqu'une
        journée aboutit à une impasse : une valeur plus élevée augmente les
        chances de succès au prix d'un temps de calcul plus long.
        """
        if self.n_days > self.n_teams - 1:
            print(
                f"Échec : {self.n_days} journées demandées alors que chaque coach ne peut "
                f"affronter que {self.n_teams - 1} adversaires différents.")
            self.schedule = {}
            return False

        for _ in range(max_attempts):
            available = set(self.all_possible_matches)
            schedule: Dict[str, List[Tuple[int, int]]] = {}
            complete = True

            for i in range(1, self.n_days + 1):
                day_matches = self._find_day_matching(available)
                if not day_matches:
                    # Un choix précédent mène à une impasse : on recommence le tirage
                    complete = False
                    break
                random.shuffle(day_matches)
                schedule[f"Journée {i}"] = [
                    match if random.random() < 0.5 else (match[1], match[0])
                    for match in day_matches
                ]
                available.difference_update(day_matches)

            if complete:
                self.schedule = schedule
                return True

        self.schedule = {}
        print(
            f"Échec : impossible de planifier {self.n_days} journées pour "
            f"{self.n_teams} équipes sans rencontre en double.")
        return False

    def save_csv(self, filename: str):
        with open(filename, mode="w", newline="", encoding="utf-8") as fp:
            writer = csv.writer(fp, delimiter=';')
            writer.writerow(["Journée", "Coach Local", "Coach Visiteur"])
            for day, matches in self.schedule.items():
                for match in matches:
                    writer.writerow([day, match[0], match[1]])


def load_coachs_from_csv(csv_path: str) -> List[Dict[str, str]]:
    """Charge les données des coachs depuis un fichier CSV avec auto-détection du délimiteur."""
    import io
    try:
        with open(csv_path, encoding="utf-8") as f:
            sample = f.read(2048)
            f.seek(0)
            sniffer = csv.Sniffer()
            delimiter = sniffer.sniff(sample, delimiters=[',', ';']).delimiter
    except Exception:
        delimiter = ';'  # fallback

    with open(csv_path, encoding="utf-8") as f:
        reader = csv.DictReader(f, delimiter=delimiter)
        return [row for row in reader]


def save_enriched_matchups_csv(filename: str, schedule: Dict, coachs_map: Dict[str, Dict[str, Any]]):
    with open(filename, mode="w", newline="", encoding="utf-8") as fp:
        writer = csv.writer(fp, delimiter=';')
        writer.writerow([
            "Journée", "Coach Local", "Équipe Local", "Roster Local",
            "Coach Visiteur", "Équipe Visiteur", "Roster Visiteur"
        ])
        for day, matches in schedule.items():
            for match in matches:
                # Assign a consistent home and away team based on their number (e.g., lower number is always home)
                team1_id, team2_id = sorted(match)
                
                local_data = coachs_map.get(str(team1_id), {})
                visiteur_data = coachs_map.get(str(team2_id), {})
                
                writer.writerow([
                    day,
                    local_data.get("coach", team1_id),
                    local_data.get("team", ""),
                    local_data.get("roster", ""),
                    visiteur_data.get("coach", team2_id),
                    visiteur_data.get("team", ""),
                    visiteur_data.get("roster", "")
                ])


def ensure_dir(path: str):
    if not os.path.exists(path):
        os.makedirs(path)


def save_markdown_table(filename, headers, rows):
    """Saves a list of rows to a markdown table, with improved formatting."""
    with open(filename, 'w', encoding='utf-8') as f:
        header_line = '| ' + ' | '.join(headers) + ' |'
        f.write(header_line + '\n')
        alignment_line = '|'
        for _ in headers:
            alignment_line += ' :---: |'
        f.write(alignment_line + '\n')
        for row in rows:
            row_content = '| ' + ' | '.join(str(cell) for cell in row) + ' |'
            f.write(row_content + '\n')


def csv_to_pdf(csv_path, pdf_path):
    if not PANDAS_INSTALLED:
        return
    try:
        df = pd.read_csv(csv_path, delimiter=';')
        doc = SimpleDocTemplate(pdf_path, pagesize=A4)
        table_data = [list(df.columns)] + df.values.tolist()
        table = Table(table_data, repeatRows=1)
        style = TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
        ])
        table.setStyle(style)
        elements = [table]
        doc.build(elements)
    except Exception as e:
        print(f"Erreur PDF : {e}")


def csv_to_image(csv_path, img_path):
    if not PANDAS_INSTALLED:
        return
    try:
        df = pd.read_csv(csv_path, delimiter=';')
        n_rows, n_cols = df.shape
        cell_width = 2.5
        cell_height = 0.7
        width = max(8, min(40, n_cols * cell_width))
        height = max(2, min(40, (n_rows+1) * cell_height))
        fig, ax = plt.subplots(figsize=(width, height))
        ax.axis('off')
        tbl = ax.table(cellText=df.values, colLabels=df.columns,
                       loc='center', cellLoc='center')
        tbl.auto_set_font_size(False)
        tbl.set_fontsize(14)
        tbl.scale(1.3, 1.3)
        for (i, key), cell in tbl.get_celld().items():
            cell.set_fontsize(14)
            cell.set_text_props(wrap=True)
            cell.set_height(cell_height/height)
        plt.tight_layout()
        plt.savefig(img_path, bbox_inches='tight', dpi=200)
        plt.close(fig)
    except Exception as e:
        print(f"Erreur image : {e}")


def generate_per_day_and_per_coach_tables(enriched_csv: str, outdir: str):
    """Génère les exports détaillés par journée et par coach."""
    per_day_dir = os.path.join(outdir, 'par_journee')
    per_coach_dir = os.path.join(outdir, 'par_coach')
    ensure_dir(per_day_dir)
    ensure_dir(per_coach_dir)

    with open(enriched_csv, encoding="utf-8") as f:
        reader = list(csv.DictReader(f, delimiter=';'))

    if not reader:
        print("Fichier enrichi vide, impossible de générer les tables.")
        return

    headers_map = {h.lower(): h for h in reader[0].keys()}
    journee_key = headers_map.get('journée')
    local_coach_key = headers_map.get('coach local')
    visiteur_coach_key = headers_map.get('coach visiteur')

    if not all([journee_key, local_coach_key, visiteur_coach_key]):
        print("Colonnes requises (Journée, Coach Local, Coach Visiteur) introuvables.")
        return

    days = sorted(set(row[journee_key] for row in reader), key=lambda x: int(re.search(r'\d+', x).group()) if re.search(r'\d+', x) else 0)

    for day in days:
        rows = [row for row in reader if row[journee_key] == day]
        headers = list(reader[0].keys())
        sanitized_day = remove_accents(day).replace(' ', '_')
        md_path = os.path.join(
            per_day_dir, f"matchups_{sanitized_day}.md")
        save_markdown_table(md_path, headers, [
                            [r[h] for h in headers] for r in rows])

        csv_path = os.path.splitext(md_path)[0] + ".csv"
        with open(csv_path, 'w', encoding='utf-8', newline='') as fcsv:
            writer = csv.writer(fcsv, delimiter=';')
            writer.writerow(headers)
            for r in rows:
                writer.writerow([r[h] for h in headers])

        pdf_path = os.path.splitext(md_path)[0] + ".pdf"
        csv_to_pdf(csv_path, pdf_path)
        
        img_path = os.path.splitext(md_path)[0] + ".png"
        csv_to_image(csv_path, img_path)

    coachs = sorted(set(row[local_coach_key] for row in reader) | set(
        row[visiteur_coach_key] for row in reader))
    for coach in coachs:
        rows = [r for r in reader if r[local_coach_key]
                == coach or r[visiteur_coach_key] == coach]
        headers = list(reader[0].keys())
        sanitized_coach = remove_accents(coach).replace(' ', '_')
        md_path = os.path.join(
            per_coach_dir, f"matchups_{sanitized_coach}.md")
        save_markdown_table(md_path, headers, [
                            [r[h] for h in headers] for r in rows])

        csv_path = os.path.splitext(md_path)[0] + ".csv"
        with open(csv_path, 'w', encoding='utf-8', newline='') as fcsv:
            writer = csv.writer(fcsv, delimiter=';')
            writer.writerow(headers)
            for r in rows:
                writer.writerow([r[h] for h in headers])

        img_path = os.path.splitext(md_path)[0] + ".png"
        csv_to_image(csv_path, img_path)


def generate_coachs_template(csv_path: str):
    """Génère un template CSV pour les coachs."""
    headers = ["num", "coach", "team", "roster"]
    example_rows = [
        [1, "Coach1", "Equipe1", "Roster1"],
        [2, "Coach2", "Equipe2", "Roster2"],
        [3, "Coach3", "Equipe3", "Roster3"],
        [4, "Coach4", "Equipe4", "Roster4"]
    ]
    with open(csv_path, 'w', encoding='utf-8', newline='') as f:
        writer = csv.writer(f, delimiter=';')
        writer.writerow(headers)
        writer.writerows(example_rows)


def main_ui():
    root = tk.Tk()
    root.title("Générateur de Matchups V3")
    root.geometry("1100x700")

    # --- Fonctions de l'interface ---
    def open_presentation_window():
        pres_win = tk.Toplevel(root)
        pres_win.title("Présentation Journée")
        pres_win.geometry("1180x720")
        pres_win.minsize(980, 620)
        pres_win.configure(bg="#0f172a")

        palette = {
            "window": "#0f172a",
            "panel": "#111c34",
            "panel_alt": "#16233f",
            "card": "#1a2747",
            "card_active": "#173626",
            "border": "#31456f",
            "text": "#eff6ff",
            "muted": "#9fb0cf",
            "gold": "#fde047",
            "accent": "#22c55e",
            "success": "#34d399",
            "danger": "#fb7185",
        }

        pres_style = ttk.Style(pres_win)
        try:
            pres_style.theme_use("clam")
        except tk.TclError:
            pass
        pres_style.configure(
            "Presentation.TButton",
            padding=(14, 10),
            font=("Segoe UI", 10, "bold")
        )
        pres_style.configure(
            "Presentation.TCombobox",
            padding=6,
            arrowsize=16
        )

        try:
            from glob import glob
            gen_dirs = sorted(
                glob("generated_*/matchups_enriched.csv"), reverse=True)
            if not gen_dirs:
                messagebox.showerror("Erreur", "Aucun planning généré trouvé.")
                pres_win.destroy()
                return

            enriched_csv = gen_dirs[0]
            coachs_data = load_coachs_from_csv(enriched_csv)

            if not coachs_data:
                messagebox.showerror(
                    "Erreur", "Le fichier de résultats est vide.")
                pres_win.destroy()
                return

            headers_map = {h.lower(): h for h in coachs_data[0].keys()}
            journee_key = headers_map.get('journée')
            coach_local_key = headers_map.get('coach local')
            coach_visiteur_key = headers_map.get('coach visiteur')
            team_local_key = headers_map.get('équipe local')
            team_visiteur_key = headers_map.get('équipe visiteur')
            roster_local_key = headers_map.get('roster local')
            roster_visiteur_key = headers_map.get('roster visiteur')

            if not all([journee_key, coach_local_key, coach_visiteur_key]):
                messagebox.showerror(
                    "Erreur", "Colonnes requises absentes du fichier enrichi.")
                pres_win.destroy()
                return

            def extract_num(j):
                m = re.search(r'(\d+)', j)
                return int(m.group(1)) if m else 0

            journees = sorted(list(set(r[journee_key]
                              for r in coachs_data)), key=extract_num)
            journee_dict = {
                j: [r for r in coachs_data if r[journee_key] == j] for j in journees}
            current_day_index = 0
            current_match_index = -1
            playing = False
            after_id = None

        except Exception as e:
            messagebox.showerror(
                "Erreur", f"Impossible de charger les journées : {e}")
            pres_win.destroy()
            return

        # Cadre principal de présentation
        main_frame = tk.Frame(pres_win, bg=palette["window"], padx=24, pady=24)
        main_frame.pack(fill=tk.BOTH, expand=True)

        header_frame = tk.Frame(main_frame, bg=palette["panel"], highlightthickness=1,
                                highlightbackground=palette["border"])
        header_frame.pack(fill=tk.X, pady=(0, 18))

        heading_block = tk.Frame(header_frame, bg=palette["panel"])
        heading_block.pack(fill=tk.X, padx=22, pady=(18, 10))

        heading_label = tk.Label(
            heading_block,
            text="Présentation des rencontres",
            bg=palette["panel"],
            fg=palette["text"],
            font=("Segoe UI Semibold", 24)
        )
        heading_label.pack(anchor="w")

        subtitle_label = tk.Label(
            heading_block,
            text="Affichage progressif des matchs de la journée sélectionnée",
            bg=palette["panel"],
            fg=palette["muted"],
            font=("Segoe UI", 11)
        )
        subtitle_label.pack(anchor="w", pady=(4, 0))

        stats_frame = tk.Frame(header_frame, bg=palette["panel"])
        stats_frame.pack(fill=tk.X, padx=22, pady=(0, 18))

        day_badge = tk.Label(
            stats_frame,
            text="Journée 0",
            bg=palette["gold"],
            fg="#1f2937",
            padx=12,
            pady=6,
            font=("Segoe UI", 10, "bold")
        )
        day_badge.pack(side=tk.LEFT)

        summary_label = tk.Label(
            stats_frame,
            text="0 rencontre",
            bg=palette["panel_alt"],
            fg=palette["text"],
            padx=12,
            pady=6,
            font=("Segoe UI", 10, "bold")
        )
        summary_label.pack(side=tk.LEFT, padx=(10, 0))

        status_label = tk.Label(
            stats_frame,
            text="Mode pause",
            bg=palette["panel"],
            fg=palette["muted"],
            font=("Segoe UI", 10)
        )
        status_label.pack(side=tk.RIGHT)

        # Cadre de contrôle pour les boutons de navigation et le menu
        control_frame = tk.Frame(main_frame, bg=palette["window"])
        control_frame.pack(fill=tk.X, pady=(0, 20))

        # Bouton "Précédent"
        btn_prev = ttk.Button(
            control_frame, text="< Précédent", style="Presentation.TButton",
            command=lambda: change_day(-1))
        btn_prev.pack(side=tk.LEFT, padx=10)

        # Menu déroulant des journées
        journee_var = tk.StringVar(value=journees[0] if journees else "")
        journee_menu = ttk.Combobox(
            control_frame, textvariable=journee_var, values=journees,
            state="readonly", width=25, style="Presentation.TCombobox")
        journee_menu.pack(side=tk.LEFT, expand=True, padx=10)

        # Bouton "Suivant"
        btn_next = ttk.Button(control_frame, text="Suivant >",
                              style="Presentation.TButton",
                              command=lambda: change_day(1))
        btn_next.pack(side=tk.LEFT, padx=10)

        # Bouton pour passer à la prochaine rencontre
        btn_next_match = ttk.Button(
            control_frame, text="Prochaine rencontre", style="Presentation.TButton",
            command=lambda: show_next_match())
        btn_next_match.pack(side=tk.RIGHT, padx=10)

        # Bouton pour afficher tous les matchs de la journée
        btn_show_all = ttk.Button(
            control_frame, text="Afficher la journée", style="Presentation.TButton",
            command=lambda: show_all_matches())
        btn_show_all.pack(side=tk.RIGHT, padx=10)

        # Bouton Pause/Lecture
        btn_pause = ttk.Button(control_frame, text="Lecture",
                               style="Presentation.TButton",
                               command=lambda: toggle_play())
        btn_pause.pack(side=tk.RIGHT, padx=10)

        # Espace pour le titre de la journée
        title_label = tk.Label(
            main_frame, text="", bg=palette["window"], fg=palette["text"], font=("Segoe UI Semibold", 22))
        title_label.pack(anchor="w", pady=(0, 8))

        # Canvas d'affichage des matchs
        canvas_frame = tk.Frame(main_frame, bg=palette["window"])
        canvas_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        canvas = tk.Canvas(canvas_frame, bg=palette["panel_alt"], highlightthickness=1,
                   highlightbackground=palette["border"])
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        canvas_scrollbar = ttk.Scrollbar(canvas_frame, orient=tk.VERTICAL, command=canvas.yview)
        canvas_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        canvas.configure(yscrollcommand=canvas_scrollbar.set)

        def format_side_details(team_name, roster_name):
            parts = []
            if team_name and team_name != "Non trouvé":
                parts.append(team_name)
            if roster_name and roster_name != "Non trouvé":
                parts.append(roster_name)
            return " • ".join(parts) if parts else "Informations d'équipe indisponibles"

        def update_navigation_state():
            btn_prev.config(state=tk.NORMAL if current_day_index > 0 else tk.DISABLED)
            btn_next.config(state=tk.NORMAL if current_day_index < len(journees) - 1 else tk.DISABLED)

        def refresh_status():
            journee = journee_var.get()
            rencontres = journee_dict.get(journee, [])
            shown_count = 0 if current_match_index < 0 else min(current_match_index + 1, len(rencontres))
            day_badge.config(text=journee or "Journée")
            summary_label.config(text=f"{len(rencontres)} rencontre{'s' if len(rencontres) > 1 else ''}")
            state_text = "Lecture automatique" if playing else "Mode pause"
            status_label.config(text=f"{state_text} • {shown_count}/{len(rencontres)} affichée{'s' if shown_count > 1 else ''}")
            update_navigation_state()

        def draw_empty_state(message):
            canvas.delete("all")
            width = max(canvas.winfo_width(), 600)
            height = max(canvas.winfo_height(), 360)
            card_w = min(620, width - 80)
            card_h = 150
            x1 = (width - card_w) / 2
            y1 = (height - card_h) / 2
            x2 = x1 + card_w
            y2 = y1 + card_h
            canvas.create_rectangle(x1, y1, x2, y2, fill=palette["card"], outline=palette["border"], width=2)
            canvas.create_text((x1 + x2) / 2, y1 + 48, text="Aucune rencontre à afficher",
                               fill=palette["text"], font=("Segoe UI Semibold", 22))
            canvas.create_text((x1 + x2) / 2, y1 + 92, text=message,
                               fill=palette["muted"], font=("Segoe UI", 12))
            canvas.configure(scrollregion=(0, 0, width, height))

        def draw_match_card(match_data, y_pos, coach_local_key, visiteur_coach_key,
                            team_local_key, visiteur_team_key, roster_local_key,
                            roster_visiteur_key, progress=1.0, highlight=False):
            local_coach = match_data.get(coach_local_key, "N/A")
            visiteur_coach = match_data.get(visiteur_coach_key, "N/A")
            local_team = match_data.get(team_local_key, "")
            visiteur_team = match_data.get(visiteur_team_key, "")
            local_roster = match_data.get(roster_local_key, "")
            visiteur_roster = match_data.get(roster_visiteur_key, "")

            width = max(canvas.winfo_width(), 900)
            card_margin = 36
            card_width = width - (card_margin * 2)
            card_height = 76
            slide_offset = (1 - progress) * 140
            x1 = card_margin
            x2 = x1 + card_width
            y1 = y_pos
            y2 = y1 + card_height

            fill = palette["card_active"] if highlight else palette["card"]
            border = palette["accent"] if highlight else palette["border"]
            badge_fill = palette["gold"] if highlight else palette["panel_alt"]
            badge_text = "#1f2937" if highlight else palette["text"]

            item_ids = []
            item_ids.append(canvas.create_rectangle(x1, y1, x2, y2, fill=fill, outline=border, width=2))
            item_ids.append(canvas.create_rectangle(x1 + 14, y1 + 14, x1 + 60, y1 + 36,
                                    fill=badge_fill, outline=""))
            item_ids.append(canvas.create_text(x1 + 37, y1 + 25, text="LOCAL", fill=badge_text,
                               font=("Segoe UI", 9, "bold")))
            item_ids.append(canvas.create_rectangle(x2 - 60, y1 + 14, x2 - 14, y1 + 36,
                                    fill=badge_fill, outline=""))
            item_ids.append(canvas.create_text(x2 - 37, y1 + 25, text="VISITEUR", fill=badge_text,
                               font=("Segoe UI", 9, "bold")))

            left_x = x1 + 82 - slide_offset
            right_x = x2 - 82 + slide_offset
            middle_x = (x1 + x2) / 2

            item_ids.append(canvas.create_text(left_x, y1 + 31, text=local_coach, anchor="w",
                               fill=palette["text"], font=("Segoe UI Semibold", 18)))
            item_ids.append(canvas.create_text(left_x, y1 + 58,
                               text=format_side_details(local_team, local_roster),
                               anchor="w", fill=palette["muted"], font=("Segoe UI", 10)))

            item_ids.append(canvas.create_text(right_x, y1 + 31, text=visiteur_coach, anchor="e",
                               fill=palette["text"], font=("Segoe UI Semibold", 18)))
            item_ids.append(canvas.create_text(right_x, y1 + 58,
                               text=format_side_details(visiteur_team, visiteur_roster),
                               anchor="e", fill=palette["muted"], font=("Segoe UI", 10)))

            item_ids.append(canvas.create_oval(middle_x - 28, y1 + 16, middle_x + 28, y1 + 58,
                               fill=palette["panel"], outline=border, width=2))
            item_ids.append(canvas.create_text(middle_x, y1 + 37, text="VS", fill=palette["gold"],
                               font=("Segoe UI", 16, "bold")))

            return item_ids

        def set_scroll_region(match_count, spacing, y_offset):
            content_height = y_offset + max(match_count, 1) * spacing + 24
            content_width = max(canvas.winfo_width(), 900)
            canvas.configure(scrollregion=(0, 0, content_width, content_height))

        def ensure_match_visible(match_index, spacing, y_offset):
            if match_index < 0:
                canvas.yview_moveto(0)
                return

            content_height = y_offset + max(len(journee_dict.get(journee_var.get(), [])), 1) * spacing + 24
            viewport_height = max(canvas.winfo_height(), 1)
            if content_height <= viewport_height:
                return

            card_top = y_offset + match_index * spacing
            card_bottom = card_top + 76
            top_fraction = canvas.yview()[0]
            visible_top = top_fraction * content_height
            visible_bottom = visible_top + viewport_height

            if card_bottom > visible_bottom - 16:
                new_top = min(card_bottom - viewport_height + 24, content_height - viewport_height)
                canvas.yview_moveto(max(0, new_top / content_height))
            elif card_top < visible_top + 16:
                new_top = max(0, card_top - 24)
                canvas.yview_moveto(new_top / content_height)

        def on_canvas_mousewheel(event):
            if canvas_scrollbar.winfo_ismapped():
                canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

        def toggle_play():
            nonlocal playing, after_id
            playing = not playing
            if playing:
                btn_pause.config(text="Pause")
                if after_id:
                    pres_win.after_cancel(after_id)
                update_display()  # Start the loop
            else:
                btn_pause.config(text="Lecture")
                if after_id:
                    pres_win.after_cancel(after_id)
                    after_id = None
                refresh_status()

        def show_all_matches():
            nonlocal current_match_index, playing
            playing = False
            btn_pause.config(text="Lecture")
            if after_id:
                pres_win.after_cancel(after_id)

            current_match_index = len(journee_dict[journee_var.get()]) - 1
            update_display()
            btn_next_match.config(state=tk.DISABLED)
            canvas.yview_moveto(1.0)

        def change_day(direction):
            nonlocal current_day_index, current_match_index, playing
            new_index = current_day_index + direction
            if 0 <= new_index < len(journees):
                current_day_index = new_index
                current_match_index = -1
                journee_var.set(journees[current_day_index])
                playing = False
                btn_pause.config(text="Lecture")
                update_display()

        # NOTE: Les clés sont maintenant des arguments de la fonction
        def animate_match(match_data, y_pos, coach_local_key, visiteur_coach_key, team_local_key, visiteur_team_key, roster_local_key, roster_visiteur_key, step=0, item_ids=None):
            if item_ids is None:
                item_ids = []

            for item_id in item_ids:
                canvas.delete(item_id)
            item_ids.clear()

            if step < 20:
                progress = step / 20
                new_item_ids = draw_match_card(
                    match_data, y_pos, coach_local_key, visiteur_coach_key,
                    team_local_key, visiteur_team_key, roster_local_key,
                    roster_visiteur_key, progress=progress, highlight=True
                )
                item_ids.extend(new_item_ids)
                pres_win.after(20, lambda: animate_match(
                    match_data, y_pos, coach_local_key, visiteur_coach_key,
                    team_local_key, visiteur_team_key, roster_local_key,
                    roster_visiteur_key, step + 1, item_ids))
            else:
                draw_match_card(
                    match_data, y_pos, coach_local_key, visiteur_coach_key,
                    team_local_key, visiteur_team_key, roster_local_key,
                    roster_visiteur_key, progress=1.0, highlight=True
                )
                item_ids.clear()

        def show_next_match():
            nonlocal current_match_index
            rencontres = journee_dict.get(journee_var.get(), [])
            if current_match_index < len(rencontres) - 1:
                current_match_index += 1
                update_display()

            if current_match_index >= len(rencontres) - 1:
                btn_next_match.config(state=tk.DISABLED)

        def update_display(event=None):
            nonlocal after_id, playing, current_match_index
            journee = journee_var.get()
            if not journee:
                return

            if after_id:
                pres_win.after_cancel(after_id)

            try:
                nonlocal current_day_index
                current_day_index = journees.index(journee)
            except ValueError:
                current_day_index = 0

            title_label.config(text=journee)
            refresh_status()

            rencontres = journee_dict.get(journee, [])
            canvas.delete("all")

            btn_next_match.config(state=tk.NORMAL)

            if not rencontres:
                draw_empty_state("Aucun match pour cette journée.")
                btn_next_match.config(state=tk.DISABLED)
                return

            y_offset = 24
            available_height = max(canvas.winfo_height() - 60, 420)
            spacing = max(86, min(102, available_height // max(len(rencontres), 1)))
            set_scroll_region(len(rencontres), spacing, y_offset)

            matches_to_show = rencontres[:current_match_index + 1]

            for i, r in enumerate(matches_to_show):
                if i == current_match_index:
                    animate_match(r, y_offset + i * spacing, coach_local_key, coach_visiteur_key,
                                  team_local_key, team_visiteur_key, roster_local_key, roster_visiteur_key)
                else:
                    draw_match_card(r, y_offset + i * spacing, coach_local_key,
                                    coach_visiteur_key, team_local_key,
                                    team_visiteur_key, roster_local_key,
                                    roster_visiteur_key, progress=1.0,
                                    highlight=False)

            if current_match_index < 0:
                canvas.create_text(canvas.winfo_width() / 2, min(80, canvas.winfo_height() / 3),
                                   text="Choisissez Lecture ou Prochaine rencontre pour démarrer",
                                   fill=palette["muted"], font=("Segoe UI", 12))
                canvas.yview_moveto(0)
            else:
                ensure_match_visible(current_match_index, spacing, y_offset)

            if playing and current_match_index < len(rencontres) - 1:
                after_id = pres_win.after(3000, show_next_match)

        journee_menu.bind('<<ComboboxSelected>>', update_display)
        canvas.bind("<Configure>", update_display)
        canvas.bind_all("<MouseWheel>", on_canvas_mousewheel)
        refresh_status()
        update_display()

    # --- Variables de l'interface ---
    coachs_file_var = tk.StringVar(value="coachs_extract.csv")
    n_teams_var = tk.StringVar()
    n_days_var = tk.StringVar(value="11")

    # Définition des styles pour les lignes du Treeview
    style = ttk.Style()
    style.configure("Treeview", rowheight=25)
    style.configure("Treeview.Heading", font=("TkDefaultFont", 10, "bold"))
    style.map("Treeview", background=[("selected", "lightgrey")])
    style.configure("odd.Treeview", background="#f0f0f0")
    style.configure("even.Treeview", background="#ffffff")

    def update_n_teams_from_csv():
        try:
            coachs_data = load_coachs_from_csv(coachs_file_var.get())
            if coachs_data:
                n_teams_var.set(str(len(coachs_data)))
            else:
                n_teams_var.set("0")
        except Exception:
            n_teams_var.set("0")

    def select_coachs_file():
        file = filedialog.askopenfilename(
            title="Sélectionner le fichier coachs_extract.csv", filetypes=[("CSV", "*.csv")])
        if file:
            coachs_file_var.set(file)
            update_n_teams_from_csv()

    def generate_template_action():
        template_file = "coachs_extract.csv"
        generate_coachs_template(template_file)
        messagebox.showinfo(
            "Template créé", f"Le fichier {template_file} a été créé. Veuillez le remplir avant de lancer la génération.")
        coachs_file_var.set(template_file)
        update_n_teams_from_csv()

    # Spinner animé (label)
    spinner_label = tk.Label(root, text="", font=("TkDefaultFont", 12, "bold"))
    spinner_running = [False]
    spinner_frames = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]

    def animate_spinner(idx=0):
        if spinner_running[0]:
            spinner_label.config(
                text="Génération en cours... " + spinner_frames[idx % len(spinner_frames)])
            root.after(80, animate_spinner, idx + 1)
        else:
            spinner_label.config(text="")

    def do_generate():
        try:
            spinner_label.pack(fill=tk.X, padx=10, pady=5)
            spinner_running[0] = True
            animate_spinner()
            root.update_idletasks()
            n_teams = int(n_teams_var.get())
            n_days = int(n_days_var.get())
            if n_teams <= 0 or n_teams % 2 != 0:
                spinner_running[0] = False
                spinner_label.pack_forget()
                messagebox.showerror(
                    "Erreur", "Le nombre d'équipes doit être un nombre pair et supérieur à zéro.")
                return
            if n_days <= 0:
                spinner_running[0] = False
                spinner_label.pack_forget()
                messagebox.showerror(
                    "Erreur", "Le nombre de journées doit être supérieur à zéro.")
                return

            # Vérification du nombre maximal de journées possibles
            max_days = n_teams - 1
            if n_days > max_days:
                spinner_running[0] = False
                spinner_label.pack_forget()
                messagebox.showerror(
                    "Erreur", f"Le nombre de journées ne peut pas dépasser {max_days} pour {n_teams} équipes.")
                return

            coachs_data = load_coachs_from_csv(coachs_file_var.get())
            required_cols = {"num", "coach", "team", "roster"}
            if not coachs_data or not all(col.lower() in [k.lower() for k in coachs_data[0].keys()] for col in required_cols):
                spinner_running[0] = False
                spinner_label.pack_forget()
                messagebox.showerror(
                    "Erreur", f"Le fichier coachs doit contenir les colonnes : {', '.join(required_cols)}")
                return

            coachs_map = {str(row["num"]): row for row in coachs_data}

            gen = MatchupGenerator(n_teams, n_days)
            if not gen.generate():
                spinner_running[0] = False
                spinner_label.pack_forget()
                messagebox.showerror(
                    "Erreur", "La génération du calendrier a échoué. Veuillez vérifier les paramètres.")
                return

            date_str = datetime.now().strftime("%Y%m%d_%H%M%S")
            outdir = f"generated_{date_str}"
            ensure_dir(outdir)

            enriched_csv = os.path.join(outdir, "matchups_enriched.csv")
            gen.save_csv(os.path.join(outdir, "matchups_raw.csv"))
            save_enriched_matchups_csv(enriched_csv, gen.schedule, coachs_map)

            generate_per_day_and_per_coach_tables(enriched_csv, outdir)

            spinner_running[0] = False
            spinner_label.pack_forget()
            messagebox.showinfo(
                "Succès", f"Calendrier généré dans le dossier '{outdir}'.")

            display_results(outdir)

        except Exception as e:
            spinner_running[0] = False
            spinner_label.pack_forget()
            messagebox.showerror("Erreur", f"Une erreur est survenue : {e}")

    def display_results(outdir: str):
        list_journees.delete(0, tk.END)
        list_coachs.delete(0, tk.END)

        for item in tree_journee.get_children():
            tree_journee.delete(item)

        text_coach.delete(1.0, tk.END)

        try:
            enriched_csv_path = os.path.join(outdir, "matchups_enriched.csv")
            coachs_data = load_coachs_from_csv(enriched_csv_path)

            if not coachs_data:
                messagebox.showerror("Erreur d'affichage",
                                     "Le fichier de résultats est vide.")
                return

            headers_map = {h.lower(): h for h in coachs_data[0].keys()}
            journee_key = headers_map.get('journée')
            coach_local_key = headers_map.get('coach local')
            coach_visiteur_key = headers_map.get('coach visiteur')

            if not all([journee_key, coach_local_key, coach_visiteur_key]):
                messagebox.showerror(
                    "Erreur", "Colonnes 'Journée', 'Coach Local' ou 'Coach Visiteur' absentes du fichier enrichi.")
                return

            def extract_num(j):
                match = re.search(r'(\d+)', j)
                return int(match.group(1)) if match else 0

            journees = sorted(set(r[journee_key]
                              for r in coachs_data), key=extract_num)

            journee_dict = {
                j: [r for r in coachs_data if r[journee_key] == j] for j in journees}
            for j in journees:
                list_journees.insert(tk.END, j)

            def show_journee(evt):
                sel = list_journees.curselection()
                if sel:
                    j = list_journees.get(sel[0])
                    rows = journee_dict[j]

                    for item in tree_journee.get_children():
                        tree_journee.delete(item)

                    for i, r in enumerate(rows):
                        tag = "even" if i % 2 == 0 else "odd"
                        tree_journee.insert("", "end", values=[
                            r['Coach Local'], r['Équipe Local'], r['Roster Local'],
                            r['Coach Visiteur'], r['Équipe Visiteur'], r['Roster Visiteur']
                        ], tags=(tag,))

            list_journees.bind('<<ListboxSelect>>', show_journee)

            coachs_set = set(r[coach_local_key] for r in coachs_data) | set(
                r[coach_visiteur_key] for r in coachs_data)
            coachs_list = sorted(coachs_set)
            coach_dict = {c: [r for r in coachs_data if r[coach_local_key]
                              == c or r[coach_visiteur_key] == c] for c in coachs_list}
            for c in coachs_list:
                list_coachs.insert(tk.END, c)

            def show_coach(evt):
                sel = list_coachs.curselection()
                if sel:
                    c = list_coachs.get(sel[0])
                    rows = coach_dict[c]
                    text_coach.delete(1.0, tk.END)
                    text_coach.insert(tk.END, f"## Matchs de {c}\n\n")
                    for r in rows:
                        vs = r[coach_visiteur_key] if r[coach_local_key] == c else r[coach_local_key]
                        text_coach.insert(
                            tk.END, f"- {r[journee_key]} : vs {vs}\n")
            list_coachs.bind('<<ListboxSelect>>', show_coach)

        except Exception as e:
            messagebox.showerror("Erreur d'affichage",
                                 f"Impossible d'afficher les résultats : {e}")

    # --- Mise en page de l'UI ---
    frame_main = ttk.Frame(root, padding="10")
    frame_main.pack(fill=tk.BOTH, expand=True)

    # Bouton de présentation
    btn_pres = ttk.Button(root, text="Présentation Journée",
                          command=open_presentation_window)
    btn_pres.pack(side=tk.TOP, pady=5)

    frame_params = ttk.LabelFrame(frame_main, text="Paramètres de génération")
    frame_params.pack(fill=tk.X, padx=5, pady=5)

    ttk.Label(frame_params, text="Fichier Coachs :").grid(
        row=0, column=0, sticky=tk.W, pady=2)
    ttk.Entry(frame_params, textvariable=coachs_file_var, state="readonly",
              width=40).grid(row=0, column=1, padx=5, sticky=tk.W)
    ttk.Button(frame_params, text="Parcourir...",
               command=select_coachs_file).grid(row=0, column=2, padx=5)
    ttk.Button(frame_params, text="Générer un template",
               command=generate_template_action).grid(row=0, column=3, padx=5)

    ttk.Label(frame_params, text="Nb d'équipes :").grid(
        row=1, column=0, sticky=tk.W, pady=2)
    ttk.Entry(frame_params, textvariable=n_teams_var, state="readonly",
              width=5).grid(row=1, column=1, sticky=tk.W, padx=5)

    ttk.Label(frame_params, text="Nb de journées :").grid(
        row=1, column=2, sticky=tk.W, pady=2)
    ttk.Entry(frame_params, textvariable=n_days_var, width=5).grid(
        row=1, column=3, sticky=tk.W, padx=5)

    ttk.Button(frame_params, text="Générer", command=do_generate).grid(
        row=2, columnspan=4, pady=10)

    notebook = ttk.Notebook(frame_main)
    notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

    frame_journee = ttk.Frame(notebook)
    frame_coach = ttk.Frame(notebook)
    notebook.add(frame_journee, text="Par Journée")
    notebook.add(frame_coach, text="Par Coach")

    list_journees = tk.Listbox(frame_journee, width=25)
    list_journees.pack(side=tk.LEFT, fill=tk.Y, padx=5, pady=5)

    # Création du tableau Treeview
    columns = ("local_coach", "local_team", "local_roster",
               "visitor_coach", "visitor_team", "visitor_roster")
    tree_journee = ttk.Treeview(
        frame_journee, columns=columns, show="headings")
    tree_journee.heading("local_coach", text="Coach Local")
    tree_journee.heading("local_team", text="Équipe Local")
    tree_journee.heading("local_roster", text="Roster Local")
    tree_journee.heading("visitor_coach", text="Coach Visiteur")
    tree_journee.heading("visitor_team", text="Équipe Visiteur")
    tree_journee.heading("visitor_roster", text="Roster Visiteur")
    tree_journee.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)

    tree_journee.column("local_coach", width=120)
    tree_journee.column("local_team", width=120)
    tree_journee.column("local_roster", width=100)
    tree_journee.column("visitor_coach", width=120)
    tree_journee.column("visitor_team", width=120)
    tree_journee.column("visitor_roster", width=100)

    list_coachs = tk.Listbox(frame_coach, width=25)
    list_coachs.pack(side=tk.LEFT, fill=tk.Y, padx=5, pady=5)
    text_coach = tk.Text(frame_coach, wrap=tk.WORD, font=("TkDefaultFont", 12))
    text_coach.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)

    update_n_teams_from_csv()

    root.mainloop()


if __name__ == "__main__":
    main_ui()
# coding: utf-8
# V3 - Générateur de plannings de matchs

import random
from typing import List, Tuple, Dict, Any
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
    Utilise une méthode de randomisation simple et efficace.
    """

    def __init__(self, n_teams: int, n_days: int):
        if n_teams % 2 != 0:
            raise ValueError(
                "Le nombre d'équipes doit être pair.")
        self.n_teams = n_teams
        self.n_days = n_days
        self.teams = list(range(1, n_teams + 1))
        self.schedule: Dict[str, List[Tuple[int, int]]] = {}

    def generate(self) -> bool:
        """
        Génère un planning de matchs en utilisant une méthode de randomisation.
        Pour chaque journée, l'ensemble des équipes est mélangé, puis les équipes sont appariées
        séquentiellement pour former les rencontres.
        """
        teams_copy = list(self.teams)
        self.schedule = {}
        
        for i in range(1, self.n_days + 1):
            day_matches = []
            # Mélange aléatoire des équipes pour chaque journée
            random.shuffle(teams_copy)
            
            # Appariement séquentiel pour créer les matchs
            for j in range(0, self.n_teams, 2):
                team1 = teams_copy[j]
                team2 = teams_copy[j+1]
                day_matches.append((team1, team2))
                
            self.schedule[f"Journée {i}"] = day_matches
            
        return True

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
                local_data = coachs_map.get(str(match[0]), {})
                visiteur_data = coachs_map.get(str(match[1]), {})
                writer.writerow([
                    day,
                    local_data.get("coach", match[0]),
                    local_data.get("team", ""),
                    local_data.get("roster", ""),
                    visiteur_data.get("coach", match[1]),
                    visiteur_data.get("team", ""),
                    visiteur_data.get("roster", "")
                ])


def ensure_dir(path: str):
    if not os.path.exists(path):
        os.makedirs(path)


def save_markdown_table(filename, headers, rows):
    """Saves a list of rows to a markdown table, with improved formatting."""
    with open(filename, 'w', encoding='utf-8') as f:
        # Generate the header row
        header_line = '| ' + ' | '.join(headers) + ' |'
        f.write(header_line + '\n')
        
        # Generate the separator line with centered alignment
        alignment_line = '|'
        for _ in headers:
            alignment_line += ' :---: |'
        f.write(alignment_line + '\n')
        
        # Generate the data rows
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
        pres_win.geometry("900x550")
        pres_win.configure(bg="#2c3e50")

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
        main_frame = tk.Frame(pres_win, bg="#2c3e50", padx=20, pady=20)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Cadre de contrôle pour les boutons de navigation et le menu
        control_frame = tk.Frame(main_frame, bg="#2c3e50")
        control_frame.pack(fill=tk.X, pady=(0, 20))

        # Bouton "Précédent"
        btn_prev = ttk.Button(
            control_frame, text="< Précédent", command=lambda: change_day(-1))
        btn_prev.pack(side=tk.LEFT, padx=10)

        # Menu déroulant des journées
        journee_var = tk.StringVar(value=journees[0] if journees else "")
        journee_menu = ttk.Combobox(
            control_frame, textvariable=journee_var, values=journees, state="readonly", width=25)
        journee_menu.pack(side=tk.LEFT, expand=True, padx=10)

        # Bouton "Suivant"
        btn_next = ttk.Button(control_frame, text="Suivant >",
                              command=lambda: change_day(1))
        btn_next.pack(side=tk.LEFT, padx=10)

        # Bouton pour passer à la prochaine rencontre
        btn_next_match = ttk.Button(
            control_frame, text="Prochaine rencontre", command=lambda: show_next_match())
        btn_next_match.pack(side=tk.RIGHT, padx=10)

        # Bouton pour afficher tous les matchs de la journée
        btn_show_all = ttk.Button(
            control_frame, text="Afficher la journée", command=lambda: show_all_matches())
        btn_show_all.pack(side=tk.RIGHT, padx=10)

        # Bouton Pause/Lecture
        btn_pause = ttk.Button(control_frame, text="Lecture",
                               command=lambda: toggle_play())
        btn_pause.pack(side=tk.RIGHT, padx=10)

        # Espace pour le titre de la journée
        title_label = tk.Label(
            main_frame, text="", bg="#2c3e50", fg="#ecf0f1", font=("Helvetica", 24, "bold"))
        title_label.pack(pady=10)

        # Canvas d'affichage des matchs
        canvas = tk.Canvas(main_frame, bg="#34495e", highlightthickness=0)
        canvas.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

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

        def show_all_matches():
            nonlocal current_match_index, playing
            playing = False
            btn_pause.config(text="Lecture")
            if after_id:
                pres_win.after_cancel(after_id)

            current_match_index = len(journee_dict[journee_var.get()]) - 1
            update_display()
            btn_next_match.config(state=tk.DISABLED)

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

            local_coach = match_data.get(coach_local_key, "N/A")
            visiteur_coach = match_data.get(visiteur_coach_key, "N/A")
            local_team = match_data.get(team_local_key, "")
            visiteur_team = match_data.get(visiteur_team_key, "")
            local_roster = match_data.get(roster_local_key, "")
            visiteur_roster = match_data.get(roster_visiteur_key, "")

            canvas_width = canvas.winfo_width()
            x_left_final = canvas_width * 0.2
            x_right_final = canvas_width * 0.8
            x_vs = canvas_width * 0.5

            y_main = y_pos
            y_sub = y_pos + 25

            # This is key for a smooth animation: clear the old drawings
            for item_id in item_ids:
                canvas.delete(item_id)
            item_ids.clear()

            if step < 20:  # Increase steps for a smoother effect
                slide_dist = canvas_width / 2
                x_left_start = -slide_dist
                x_right_start = canvas_width + slide_dist

                progress = step / 20
                x_left_current = x_left_start + \
                    (x_left_final - x_left_start) * progress
                x_right_current = x_right_start + \
                    (x_right_final - x_right_start) * progress

                item_ids.append(canvas.create_text(x_vs, y_main, text="VS",
                                anchor="center", fill="#f1c40f", font=("Helvetica", 22, "bold")))
                item_ids.append(canvas.create_text(x_left_current, y_main, text=local_coach,
                                anchor="w", fill="#ecf0f1", font=("Helvetica", 20, "bold")))
                item_ids.append(canvas.create_text(x_right_current, y_main, text=visiteur_coach,
                                anchor="e", fill="#ecf0f1", font=("Helvetica", 20, "bold")))

                pres_win.after(20, lambda: animate_match(
                    match_data, y_pos, coach_local_key, visiteur_coach_key, team_local_key, visiteur_team_key, roster_local_key, roster_visiteur_key, step + 1, item_ids))
            else:
                # Final position, display full details
                canvas.create_text(x_left_final, y_main, text=local_coach,
                                   anchor="w", fill="#ecf0f1", font=("Helvetica", 20, "bold"))
                canvas.create_text(x_right_final, y_main, text=visiteur_coach,
                                   anchor="e", fill="#ecf0f1", font=("Helvetica", 20, "bold"))
                canvas.create_text(x_vs, y_main, text="VS", anchor="center",
                                   fill="#f1c40f", font=("Helvetica", 22, "bold"))
                canvas.create_text(
                    x_left_final, y_sub, text=f"{local_team} ({local_roster})", anchor="w", fill="#bdc3c7", font=("Helvetica", 12))
                canvas.create_text(
                    x_right_final, y_sub, text=f"{visiteur_team} ({visiteur_roster})", anchor="e", fill="#bdc3c7", font=("Helvetica", 12))
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

            rencontres = journee_dict.get(journee, [])
            canvas.delete("all")

            btn_next_match.config(state=tk.NORMAL)

            if not rencontres:
                canvas.create_text(canvas.winfo_width()/2, canvas.winfo_height()/2,
                                   text="Aucun match pour cette journée.", fill="#fff", font=("Helvetica", 16))
                btn_next_match.config(state=tk.DISABLED)
                return

            y_offset = 30
            spacing = 70

            # Fix for initial display and subsequent matches
            matches_to_show = rencontres[:current_match_index + 1]

            for i, r in enumerate(matches_to_show):
                if i == current_match_index:
                    animate_match(r, y_offset + i * spacing, coach_local_key, coach_visiteur_key,
                                  team_local_key, team_visiteur_key, roster_local_key, roster_visiteur_key)
                else:
                    local_coach = r.get(coach_local_key, "N/A")
                    visiteur_coach = r.get(coach_visiteur_key, "N/A")
                    local_team = r.get(team_local_key, "")
                    visiteur_team = r.get(team_visiteur_key, "")
                    local_roster = r.get(roster_local_key, "")
                    visiteur_roster = r.get(roster_visiteur_key, "")

                    canvas_width = canvas.winfo_width()
                    x_left_final = canvas_width * 0.2
                    x_right_final = canvas_width * 0.8
                    x_vs = canvas_width * 0.5

                    y_main = y_offset + i * spacing
                    y_sub = y_main + 25

                    canvas.create_text(x_left_final, y_main, text=local_coach,
                                       anchor="w", fill="#ecf0f1", font=("Helvetica", 20, "bold"))
                    canvas.create_text(x_right_final, y_main, text=visiteur_coach,
                                       anchor="e", fill="#ecf0f1", font=("Helvetica", 20, "bold"))
                    canvas.create_text(x_vs, y_main, text="VS", anchor="center", fill="#f1c40f", font=(
                        "Helvetica", 22, "bold"))

                    canvas.create_text(
                        x_left_final, y_sub, text=f"{local_team} ({local_roster})", anchor="w", fill="#bdc3c7", font=("Helvetica", 12))
                    canvas.create_text(
                        x_right_final, y_sub, text=f"{visiteur_team} ({visiteur_roster})", anchor="e", fill="#bdc3c7", font=("Helvetica", 12))

            # New and corrected animation loop logic
            if playing and current_match_index < len(rencontres) - 1:
                after_id = pres_win.after(3000, show_next_match)

        journee_menu.bind('<<ComboboxSelected>>', update_display)
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
            gen.generate()

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
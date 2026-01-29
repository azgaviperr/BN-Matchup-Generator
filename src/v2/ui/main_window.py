# coding: utf-8
"""
Modern GUI for BN Matchup Generator V2
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import os
import sys
import logging

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from v2.core.generator import MatchupGenerator, InvalidTeamCountError
from v2.core.models import CoachManager
from v2.exports.exporter import MatchupExporter
from v2.utils.file_utils import ensure_dir

logger = logging.getLogger(__name__)


class MatchupGeneratorGUI:
    """Modern GUI for the matchup generator."""
    
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("BN Matchup Generator V2")
        self.root.geometry("1200x800")
        
        # Application state
        self.coach_manager = CoachManager()
        self.generator = None
        self.schedule = None
        self.output_dir = None
        
        # Setup UI
        self._setup_styles()
        self._create_widgets()
        
    def _setup_styles(self):
        """Setup custom styles for the UI."""
        style = ttk.Style()
        style.theme_use('clam')
        
        # Configure colors
        style.configure('Title.TLabel', font=('Helvetica', 16, 'bold'))
        style.configure('Subtitle.TLabel', font=('Helvetica', 12))
        style.configure('Success.TLabel', foreground='green', font=('Helvetica', 10, 'bold'))
        style.configure('Error.TLabel', foreground='red', font=('Helvetica', 10, 'bold'))
        
    def _create_widgets(self):
        """Create all UI widgets."""
        # Main container
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Title
        title = ttk.Label(main_frame, text="BN Matchup Generator V2", style='Title.TLabel')
        title.pack(pady=10)
        
        subtitle = ttk.Label(main_frame, text="Générateur de calendrier moderne et modulaire", 
                            style='Subtitle.TLabel')
        subtitle.pack(pady=5)
        
        # Configuration frame
        config_frame = ttk.LabelFrame(main_frame, text="Configuration", padding="10")
        config_frame.pack(fill=tk.X, pady=10)
        
        # Coach file selection
        file_frame = ttk.Frame(config_frame)
        file_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(file_frame, text="Fichier Coachs:").pack(side=tk.LEFT, padx=5)
        
        self.file_var = tk.StringVar(value="coachs_extract.csv")
        file_entry = ttk.Entry(file_frame, textvariable=self.file_var, width=50, state="readonly")
        file_entry.pack(side=tk.LEFT, padx=5)
        
        ttk.Button(file_frame, text="Parcourir...", 
                  command=self._browse_file).pack(side=tk.LEFT, padx=5)
        ttk.Button(file_frame, text="Charger", 
                  command=self._load_coaches).pack(side=tk.LEFT, padx=5)
        
        # Status label for coaches
        self.coach_status = ttk.Label(config_frame, text="")
        self.coach_status.pack(pady=5)
        
        # Parameters frame
        param_frame = ttk.Frame(config_frame)
        param_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(param_frame, text="Nombre d'équipes:").pack(side=tk.LEFT, padx=5)
        self.teams_var = tk.StringVar(value="0")
        ttk.Entry(param_frame, textvariable=self.teams_var, width=10, 
                 state="readonly").pack(side=tk.LEFT, padx=5)
        
        ttk.Label(param_frame, text="Nombre de journées:").pack(side=tk.LEFT, padx=20)
        self.days_var = tk.StringVar(value="11")
        ttk.Spinbox(param_frame, from_=1, to=100, textvariable=self.days_var, 
                   width=10).pack(side=tk.LEFT, padx=5)
        
        # Action buttons
        action_frame = ttk.Frame(main_frame)
        action_frame.pack(fill=tk.X, pady=10)
        
        ttk.Button(action_frame, text="Générer le Calendrier", 
                  command=self._generate_schedule).pack(side=tk.LEFT, padx=5)
        ttk.Button(action_frame, text="Exporter", 
                  command=self._export_results).pack(side=tk.LEFT, padx=5)
        ttk.Button(action_frame, text="Présentation", 
                  command=self._show_presentation).pack(side=tk.LEFT, padx=5)
        
        # Status label
        self.status_label = ttk.Label(action_frame, text="")
        self.status_label.pack(side=tk.LEFT, padx=20)
        
        # Progress bar
        self.progress = ttk.Progressbar(main_frame, mode='indeterminate')
        
        # Results notebook
        self.notebook = ttk.Notebook(main_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True, pady=10)
        
        # Tab 1: Schedule by day
        day_frame = ttk.Frame(self.notebook)
        self.notebook.add(day_frame, text="Par Journée")
        
        # Listbox for days
        day_list_frame = ttk.Frame(day_frame)
        day_list_frame.pack(side=tk.LEFT, fill=tk.Y, padx=5, pady=5)
        
        ttk.Label(day_list_frame, text="Journées:").pack()
        self.day_listbox = tk.Listbox(day_list_frame, width=20)
        self.day_listbox.pack(fill=tk.BOTH, expand=True)
        self.day_listbox.bind('<<ListboxSelect>>', self._on_day_select)
        
        # Treeview for matches
        tree_frame = ttk.Frame(day_frame)
        tree_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        columns = ("local_coach", "local_team", "local_roster", 
                  "visitor_coach", "visitor_team", "visitor_roster")
        self.day_tree = ttk.Treeview(tree_frame, columns=columns, show="headings")
        
        self.day_tree.heading("local_coach", text="Coach Local")
        self.day_tree.heading("local_team", text="Équipe Local")
        self.day_tree.heading("local_roster", text="Roster Local")
        self.day_tree.heading("visitor_coach", text="Coach Visiteur")
        self.day_tree.heading("visitor_team", text="Équipe Visiteur")
        self.day_tree.heading("visitor_roster", text="Roster Visiteur")
        
        for col in columns:
            self.day_tree.column(col, width=150)
        
        scrollbar = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=self.day_tree.yview)
        self.day_tree.configure(yscrollcommand=scrollbar.set)
        
        self.day_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Tab 2: Schedule by coach
        coach_frame = ttk.Frame(self.notebook)
        self.notebook.add(coach_frame, text="Par Coach")
        
        coach_list_frame = ttk.Frame(coach_frame)
        coach_list_frame.pack(side=tk.LEFT, fill=tk.Y, padx=5, pady=5)
        
        ttk.Label(coach_list_frame, text="Coachs:").pack()
        self.coach_listbox = tk.Listbox(coach_list_frame, width=25)
        self.coach_listbox.pack(fill=tk.BOTH, expand=True)
        self.coach_listbox.bind('<<ListboxSelect>>', self._on_coach_select)
        
        # Text widget for coach matches
        text_frame = ttk.Frame(coach_frame)
        text_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        self.coach_text = tk.Text(text_frame, wrap=tk.WORD, font=("TkDefaultFont", 11))
        text_scrollbar = ttk.Scrollbar(text_frame, orient=tk.VERTICAL, 
                                      command=self.coach_text.yview)
        self.coach_text.configure(yscrollcommand=text_scrollbar.set)
        
        self.coach_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        text_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
    def _browse_file(self):
        """Open file browser dialog."""
        filename = filedialog.askopenfilename(
            title="Sélectionner le fichier des coachs",
            filetypes=[("CSV files", "*.csv"), ("JSON files", "*.json"), 
                      ("All files", "*.*")]
        )
        if filename:
            self.file_var.set(filename)
            self._load_coaches()
    
    def _load_coaches(self):
        """Load coaches from the selected file."""
        filepath = self.file_var.get()
        
        if not os.path.exists(filepath):
            self.coach_status.config(text="❌ Fichier introuvable", style='Error.TLabel')
            return
        
        try:
            if filepath.endswith('.json'):
                count = self.coach_manager.load_from_json(filepath)
            else:
                count = self.coach_manager.load_from_csv(filepath)
            
            # Validate
            errors = self.coach_manager.validate()
            if errors:
                messagebox.showerror("Erreurs de validation", "\n".join(errors))
                self.coach_status.config(text="❌ Erreurs de validation", style='Error.TLabel')
                return
            
            self.teams_var.set(str(count))
            self.coach_status.config(text=f"✓ {count} coachs chargés", style='Success.TLabel')
            logger.info(f"Loaded {count} coaches")
            
        except Exception as e:
            messagebox.showerror("Erreur", f"Erreur lors du chargement: {e}")
            self.coach_status.config(text="❌ Erreur de chargement", style='Error.TLabel')
    
    def _generate_schedule(self):
        """Generate the matchup schedule."""
        try:
            n_teams = len(self.coach_manager)
            if n_teams == 0:
                messagebox.showerror("Erreur", "Aucun coach chargé")
                return
            
            n_days = int(self.days_var.get())
            
            # Show progress
            self.progress.pack(fill=tk.X, pady=5)
            self.progress.start()
            self.status_label.config(text="Génération en cours...")
            self.root.update()
            
            # Generate
            self.generator = MatchupGenerator(n_teams, n_days)
            
            if not self.generator.generate():
                raise Exception("La génération a échoué")
            
            if not self.generator.validate_schedule():
                raise Exception("Le calendrier généré est invalide")
            
            self.schedule = self.generator.get_schedule()
            
            # Display results
            self._display_results()
            
            # Stop progress
            self.progress.stop()
            self.progress.pack_forget()
            self.status_label.config(text="✓ Calendrier généré avec succès")
            
            messagebox.showinfo("Succès", "Le calendrier a été généré avec succès!")
            
        except InvalidTeamCountError as e:
            self.progress.stop()
            self.progress.pack_forget()
            self.status_label.config(text="")
            messagebox.showerror("Erreur de configuration", str(e))
        except Exception as e:
            self.progress.stop()
            self.progress.pack_forget()
            self.status_label.config(text="")
            messagebox.showerror("Erreur", f"Erreur lors de la génération: {e}")
    
    def _display_results(self):
        """Display the generated schedule in the UI."""
        if not self.schedule:
            return
        
        # Clear existing data
        self.day_listbox.delete(0, tk.END)
        self.coach_listbox.delete(0, tk.END)
        
        # Prepare data
        self.schedule_data = {}
        self.coach_data = {}
        
        # Process schedule
        for day, matches in self.schedule.items():
            day_matches = []
            
            for match in matches:
                team1_id, team2_id = sorted(match)
                
                coach1 = self.coach_manager.get_coach_by_num(team1_id)
                coach2 = self.coach_manager.get_coach_by_num(team2_id)
                
                match_data = {
                    'local_coach': coach1.coach_name if coach1 else f"Team {team1_id}",
                    'local_team': coach1.team_name if coach1 else "",
                    'local_roster': coach1.roster if coach1 else "",
                    'visitor_coach': coach2.coach_name if coach2 else f"Team {team2_id}",
                    'visitor_team': coach2.team_name if coach2 else "",
                    'visitor_roster': coach2.roster if coach2 else "",
                }
                
                day_matches.append(match_data)
                
                # Add to coach data
                if coach1:
                    if coach1.coach_name not in self.coach_data:
                        self.coach_data[coach1.coach_name] = []
                    self.coach_data[coach1.coach_name].append({
                        'day': day,
                        'opponent': coach2.coach_name if coach2 else f"Team {team2_id}"
                    })
                
                if coach2:
                    if coach2.coach_name not in self.coach_data:
                        self.coach_data[coach2.coach_name] = []
                    self.coach_data[coach2.coach_name].append({
                        'day': day,
                        'opponent': coach1.coach_name if coach1 else f"Team {team1_id}"
                    })
            
            self.schedule_data[day] = day_matches
            self.day_listbox.insert(tk.END, day)
        
        # Populate coach listbox
        for coach_name in sorted(self.coach_data.keys()):
            self.coach_listbox.insert(tk.END, coach_name)
    
    def _on_day_select(self, event):
        """Handle day selection."""
        selection = self.day_listbox.curselection()
        if not selection:
            return
        
        day = self.day_listbox.get(selection[0])
        matches = self.schedule_data.get(day, [])
        
        # Clear tree
        for item in self.day_tree.get_children():
            self.day_tree.delete(item)
        
        # Populate tree
        for i, match in enumerate(matches):
            tag = "even" if i % 2 == 0 else "odd"
            self.day_tree.insert("", "end", values=[
                match['local_coach'], match['local_team'], match['local_roster'],
                match['visitor_coach'], match['visitor_team'], match['visitor_roster']
            ], tags=(tag,))
        
        # Configure tags
        self.day_tree.tag_configure("even", background="#f0f0f0")
        self.day_tree.tag_configure("odd", background="#ffffff")
    
    def _on_coach_select(self, event):
        """Handle coach selection."""
        selection = self.coach_listbox.curselection()
        if not selection:
            return
        
        coach_name = self.coach_listbox.get(selection[0])
        matches = self.coach_data.get(coach_name, [])
        
        # Clear and populate text
        self.coach_text.delete(1.0, tk.END)
        self.coach_text.insert(tk.END, f"Matchs de {coach_name}\n\n")
        
        for match in matches:
            self.coach_text.insert(tk.END, f"• {match['day']}: vs {match['opponent']}\n")
    
    def _export_results(self):
        """Export the results."""
        if not self.schedule:
            messagebox.showwarning("Attention", "Aucun calendrier à exporter")
            return
        
        from datetime import datetime
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.output_dir = f"generated_{timestamp}"
        
        ensure_dir(self.output_dir)
        
        # Prepare coach map
        coach_map = {}
        for coach in self.coach_manager.get_all_coaches():
            coach_map[str(coach.num)] = {
                "coach_name": coach.coach_name,
                "team_name": coach.team_name,
                "roster": coach.roster,
                "groupe": coach.groupe
            }
        
        exporter = MatchupExporter(self.schedule, coach_map)
        
        try:
            exporter.export_csv(os.path.join(self.output_dir, "matchups_enriched.csv"))
            exporter.export_json(os.path.join(self.output_dir, "matchups.json"))
            exporter.export_markdown(os.path.join(self.output_dir, "matchups.md"))
            
            messagebox.showinfo("Succès", f"Résultats exportés dans:\n{self.output_dir}")
            self.status_label.config(text=f"✓ Exporté dans {self.output_dir}")
            
        except Exception as e:
            messagebox.showerror("Erreur", f"Erreur lors de l'export: {e}")
    
    def _show_presentation(self):
        """Show presentation window (placeholder for now)."""
        if not self.schedule:
            messagebox.showwarning("Attention", "Aucun calendrier à présenter")
            return
        
        messagebox.showinfo("Info", "Mode présentation disponible prochainement")
    
    def run(self):
        """Start the GUI application."""
        self.root.mainloop()


if __name__ == "__main__":
    app = MatchupGeneratorGUI()
    app.run()

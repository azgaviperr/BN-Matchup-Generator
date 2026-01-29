# coding: utf-8
"""
Export functionality for matchup schedules in various formats.
"""

import csv
import json
from typing import Dict, List, Tuple
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

# Check for optional dependencies
try:
    import pandas as pd
    from reportlab.lib.pagesizes import A4
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle
    from reportlab.lib import colors
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False
    logger.warning("reportlab/pandas not available - PDF export disabled")


class MatchupExporter:
    """Handles exporting matchup schedules to various formats."""
    
    def __init__(self, schedule: Dict[str, List[Tuple[int, int]]], coach_map: Dict):
        """
        Initialize exporter.
        
        Args:
            schedule: Match schedule dictionary
            coach_map: Mapping of team numbers to coach data
        """
        self.schedule = schedule
        self.coach_map = coach_map
    
    def export_csv(self, filepath: str, enriched: bool = True, delimiter: str = ';'):
        """
        Export schedule to CSV.
        
        Args:
            filepath: Output file path
            enriched: If True, include coach/team details; if False, just team numbers
            delimiter: CSV delimiter
        """
        with open(filepath, 'w', encoding='utf-8', newline='') as f:
            if enriched:
                writer = csv.writer(f, delimiter=delimiter)
                writer.writerow([
                    "Journée", "Coach Local", "Équipe Local", "Roster Local",
                    "Coach Visiteur", "Équipe Visiteur", "Roster Visiteur"
                ])
                
                for day, matches in self.schedule.items():
                    for match in matches:
                        team1_id, team2_id = sorted(match)
                        
                        local_data = self.coach_map.get(str(team1_id), {})
                        visiteur_data = self.coach_map.get(str(team2_id), {})
                        
                        writer.writerow([
                            day,
                            local_data.get("coach_name", f"Team {team1_id}"),
                            local_data.get("team_name", ""),
                            local_data.get("roster", ""),
                            visiteur_data.get("coach_name", f"Team {team2_id}"),
                            visiteur_data.get("team_name", ""),
                            visiteur_data.get("roster", "")
                        ])
            else:
                writer = csv.writer(f, delimiter=delimiter)
                writer.writerow(["Journée", "Équipe Local", "Équipe Visiteur"])
                
                for day, matches in self.schedule.items():
                    for match in matches:
                        writer.writerow([day, match[0], match[1]])
        
        logger.info(f"Exported CSV to {filepath}")
    
    def export_json(self, filepath: str):
        """
        Export schedule to JSON.
        
        Args:
            filepath: Output file path
        """
        data = {
            "export_date": datetime.now().isoformat(),
            "schedule": []
        }
        
        for day, matches in self.schedule.items():
            day_data = {
                "day": day,
                "matches": []
            }
            
            for match in matches:
                team1_id, team2_id = sorted(match)
                
                local_data = self.coach_map.get(str(team1_id), {})
                visiteur_data = self.coach_map.get(str(team2_id), {})
                
                match_data = {
                    "local": {
                        "team_id": team1_id,
                        "coach": local_data.get("coach_name", f"Team {team1_id}"),
                        "team": local_data.get("team_name", ""),
                        "roster": local_data.get("roster", "")
                    },
                    "visitor": {
                        "team_id": team2_id,
                        "coach": visiteur_data.get("coach_name", f"Team {team2_id}"),
                        "team": visiteur_data.get("team_name", ""),
                        "roster": visiteur_data.get("roster", "")
                    }
                }
                
                day_data["matches"].append(match_data)
            
            data["schedule"].append(day_data)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        logger.info(f"Exported JSON to {filepath}")
    
    def export_markdown(self, filepath: str, day_filter: str = None):
        """
        Export schedule to Markdown.
        
        Args:
            filepath: Output file path
            day_filter: If provided, only export this specific day
        """
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write("# Planning des Matchs\n\n")
            
            for day, matches in self.schedule.items():
                if day_filter and day != day_filter:
                    continue
                
                f.write(f"## {day}\n\n")
                f.write("| Coach Local | Équipe Local | Roster | VS | Coach Visiteur | Équipe Visiteur | Roster |\n")
                f.write("|-------------|--------------|--------|----|-----------------|-----------------|---------|\n")
                
                for match in matches:
                    team1_id, team2_id = sorted(match)
                    
                    local_data = self.coach_map.get(str(team1_id), {})
                    visiteur_data = self.coach_map.get(str(team2_id), {})
                    
                    f.write(f"| {local_data.get('coach_name', f'Team {team1_id}')} | "
                           f"{local_data.get('team_name', '')} | "
                           f"{local_data.get('roster', '')} | "
                           f"VS | "
                           f"{visiteur_data.get('coach_name', f'Team {team2_id}')} | "
                           f"{visiteur_data.get('team_name', '')} | "
                           f"{visiteur_data.get('roster', '')} |\n")
                
                f.write("\n")
        
        logger.info(f"Exported Markdown to {filepath}")
    
    def export_pdf(self, filepath: str):
        """
        Export schedule to PDF.
        
        Args:
            filepath: Output file path
        """
        if not REPORTLAB_AVAILABLE:
            logger.warning("PDF export not available (reportlab not installed)")
            return
        
        try:
            doc = SimpleDocTemplate(filepath, pagesize=A4)
            elements = []
            
            # Prepare table data
            table_data = [[
                "Journée", "Coach Local", "Équipe Local", "Roster",
                "Coach Visiteur", "Équipe Visiteur", "Roster"
            ]]
            
            for day, matches in self.schedule.items():
                for match in matches:
                    team1_id, team2_id = sorted(match)
                    
                    local_data = self.coach_map.get(str(team1_id), {})
                    visiteur_data = self.coach_map.get(str(team2_id), {})
                    
                    table_data.append([
                        day,
                        local_data.get("coach_name", f"Team {team1_id}"),
                        local_data.get("team_name", ""),
                        local_data.get("roster", ""),
                        visiteur_data.get("coach_name", f"Team {team2_id}"),
                        visiteur_data.get("team_name", ""),
                        visiteur_data.get("roster", "")
                    ])
            
            # Create table
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
            
            elements.append(table)
            doc.build(elements)
            
            logger.info(f"Exported PDF to {filepath}")
        except Exception as e:
            logger.error(f"PDF export failed: {e}")

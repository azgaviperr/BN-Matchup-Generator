#!/usr/bin/env python3
# coding: utf-8
"""
BN Matchup Generator V2 - Main Entry Point
A modern, modular rewrite of the matchup generator with improved architecture.
"""

import sys
import os
import logging
from datetime import datetime

# Add src directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from v2.core.generator import MatchupGenerator, InvalidTeamCountError
from v2.core.models import CoachManager
from v2.exports.exporter import MatchupExporter
from v2.utils.file_utils import ensure_dir, sanitize_filename

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class MatchupGeneratorApp:
    """Main application controller for V2."""
    
    def __init__(self):
        self.coach_manager = CoachManager()
        self.generator = None
        self.schedule = None
    
    def load_coaches(self, filepath: str) -> bool:
        """
        Load coaches from a file (CSV or JSON).
        
        Args:
            filepath: Path to coach data file
            
        Returns:
            True if successful
        """
        try:
            if filepath.endswith('.json'):
                count = self.coach_manager.load_from_json(filepath)
            else:
                count = self.coach_manager.load_from_csv(filepath)
            
            logger.info(f"Loaded {count} coaches from {filepath}")
            
            # Validate
            errors = self.coach_manager.validate()
            if errors:
                logger.error(f"Validation errors: {errors}")
                return False
            
            return True
        except Exception as e:
            logger.error(f"Failed to load coaches: {e}")
            return False
    
    def generate_schedule(self, n_days: int, seed=None) -> bool:
        """
        Generate matchup schedule.
        
        Args:
            n_days: Number of days to generate
            seed: Optional random seed
            
        Returns:
            True if successful
        """
        try:
            n_teams = len(self.coach_manager)
            
            if n_teams == 0:
                logger.error("No coaches loaded")
                return False
            
            self.generator = MatchupGenerator(n_teams, n_days)
            
            if not self.generator.generate(seed=seed):
                logger.error("Schedule generation failed")
                return False
            
            self.schedule = self.generator.get_schedule()
            
            # Validate
            if not self.generator.validate_schedule():
                logger.error("Generated schedule is invalid")
                return False
            
            logger.info(f"Successfully generated schedule for {n_days} days")
            return True
            
        except InvalidTeamCountError as e:
            logger.error(f"Invalid team configuration: {e}")
            return False
        except Exception as e:
            logger.error(f"Schedule generation failed: {e}")
            return False
    
    def export_results(self, output_dir: str = None) -> str:
        """
        Export results to various formats.
        
        Args:
            output_dir: Output directory (generated if None)
            
        Returns:
            Path to output directory
        """
        if not self.schedule:
            logger.error("No schedule to export")
            return None
        
        # Create output directory
        if output_dir is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_dir = f"generated_{timestamp}"
        
        ensure_dir(output_dir)
        
        # Prepare coach map for exporter
        coach_map = {}
        for coach in self.coach_manager.get_all_coaches():
            coach_map[str(coach.num)] = {
                "coach_name": coach.coach_name,
                "team_name": coach.team_name,
                "roster": coach.roster,
                "groupe": coach.groupe
            }
        
        exporter = MatchupExporter(self.schedule, coach_map)
        
        # Export in various formats
        try:
            exporter.export_csv(os.path.join(output_dir, "matchups_enriched.csv"))
            exporter.export_csv(os.path.join(output_dir, "matchups_raw.csv"), enriched=False)
            exporter.export_json(os.path.join(output_dir, "matchups.json"))
            exporter.export_markdown(os.path.join(output_dir, "matchups.md"))
            
            # Try PDF export if available
            exporter.export_pdf(os.path.join(output_dir, "matchups.pdf"))
            
            # Export per-day files
            per_day_dir = os.path.join(output_dir, "par_journee")
            ensure_dir(per_day_dir)
            
            for day in self.schedule.keys():
                day_filename = sanitize_filename(day)
                exporter.export_markdown(
                    os.path.join(per_day_dir, f"{day_filename}.md"),
                    day_filter=day
                )
            
            logger.info(f"Results exported to {output_dir}")
            return output_dir
            
        except Exception as e:
            logger.error(f"Export failed: {e}")
            return None


def run_cli():
    """Run the application in CLI mode."""
    import argparse
    
    parser = argparse.ArgumentParser(description='BN Matchup Generator V2')
    parser.add_argument('--coaches', required=True, help='Path to coaches CSV/JSON file')
    parser.add_argument('--days', type=int, required=True, help='Number of days to generate')
    parser.add_argument('--output', help='Output directory (default: auto-generated)')
    parser.add_argument('--seed', type=int, help='Random seed for reproducibility')
    parser.add_argument('--verbose', action='store_true', help='Verbose logging')
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Run application
    app = MatchupGeneratorApp()
    
    print(f"Loading coaches from {args.coaches}...")
    if not app.load_coaches(args.coaches):
        print("ERROR: Failed to load coaches")
        sys.exit(1)
    
    print(f"Generating schedule for {args.days} days...")
    if not app.generate_schedule(args.days, seed=args.seed):
        print("ERROR: Failed to generate schedule")
        sys.exit(1)
    
    print("Exporting results...")
    output_dir = app.export_results(args.output)
    
    if output_dir:
        print(f"SUCCESS: Results exported to {output_dir}")
    else:
        print("ERROR: Failed to export results")
        sys.exit(1)


def run_gui():
    """Run the application in GUI mode."""
    from v2.ui.main_window import MatchupGeneratorGUI
    
    app = MatchupGeneratorGUI()
    app.run()


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] != '--gui':
        # CLI mode
        run_cli()
    else:
        # GUI mode
        print("Starting GUI mode...")
        try:
            run_gui()
        except ImportError:
            print("GUI not available, use CLI mode:")
            print("python matchup_generator_v2.py --coaches coachs_extract.csv --days 11")

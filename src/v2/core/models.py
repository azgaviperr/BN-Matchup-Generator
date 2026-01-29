# coding: utf-8
"""
Data models for coaches and teams.
"""

from typing import List, Dict, Optional
from dataclasses import dataclass, field, asdict
import json
import csv


@dataclass
class Coach:
    """Represents a coach with their team information."""
    
    num: int
    coach_name: str
    team_name: str
    roster: str
    groupe: str = ""
    
    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'Coach':
        """Create Coach from dictionary."""
        # Handle various key formats
        num = int(data.get("num", data.get("Num", 0)))
        coach_name = data.get("coach", data.get("Coach", data.get("coach_name", "")))
        team_name = data.get("team", data.get("Team", data.get("team_name", "")))
        roster = data.get("roster", data.get("Roster", ""))
        groupe = data.get("groupe", data.get("Groupe", ""))
        
        return cls(
            num=num,
            coach_name=coach_name,
            team_name=team_name,
            roster=roster,
            groupe=groupe
        )


class CoachManager:
    """Manages a collection of coaches."""
    
    def __init__(self):
        self.coaches: List[Coach] = []
    
    def add_coach(self, coach: Coach):
        """Add a coach to the collection."""
        self.coaches.append(coach)
    
    def get_coach_by_num(self, num: int) -> Optional[Coach]:
        """Get coach by their number."""
        for coach in self.coaches:
            if coach.num == num:
                return coach
        return None
    
    def get_all_coaches(self) -> List[Coach]:
        """Get all coaches."""
        return self.coaches.copy()
    
    def load_from_csv(self, filepath: str, delimiter: str = None) -> int:
        """
        Load coaches from CSV file.
        
        Args:
            filepath: Path to CSV file
            delimiter: CSV delimiter (auto-detected if None)
            
        Returns:
            Number of coaches loaded
        """
        self.coaches = []
        
        # Auto-detect delimiter if not provided
        if delimiter is None:
            with open(filepath, 'r', encoding='utf-8') as f:
                sample = f.read(2048)
                sniffer = csv.Sniffer()
                try:
                    delimiter = sniffer.sniff(sample, delimiters=[',', ';', '\t']).delimiter
                except:
                    delimiter = ','  # fallback
        
        with open(filepath, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f, delimiter=delimiter)
            for row in reader:
                try:
                    coach = Coach.from_dict(row)
                    self.coaches.append(coach)
                except Exception as e:
                    print(f"Warning: Could not parse row {row}: {e}")
        
        return len(self.coaches)
    
    def save_to_csv(self, filepath: str, delimiter: str = ';'):
        """
        Save coaches to CSV file.
        
        Args:
            filepath: Path to output CSV file
            delimiter: CSV delimiter
        """
        with open(filepath, 'w', encoding='utf-8', newline='') as f:
            fieldnames = ['num', 'coach', 'groupe', 'team', 'roster']
            writer = csv.DictWriter(f, fieldnames=fieldnames, delimiter=delimiter)
            writer.writeheader()
            
            for coach in self.coaches:
                writer.writerow({
                    'num': coach.num,
                    'coach': coach.coach_name,
                    'groupe': coach.groupe,
                    'team': coach.team_name,
                    'roster': coach.roster
                })
    
    def load_from_json(self, filepath: str) -> int:
        """
        Load coaches from JSON file.
        
        Args:
            filepath: Path to JSON file
            
        Returns:
            Number of coaches loaded
        """
        self.coaches = []
        
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        for item in data:
            try:
                coach = Coach.from_dict(item)
                self.coaches.append(coach)
            except Exception as e:
                print(f"Warning: Could not parse item {item}: {e}")
        
        return len(self.coaches)
    
    def save_to_json(self, filepath: str):
        """
        Save coaches to JSON file.
        
        Args:
            filepath: Path to output JSON file
        """
        data = [coach.to_dict() for coach in self.coaches]
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    def validate(self) -> List[str]:
        """
        Validate the coach data.
        
        Returns:
            List of validation errors (empty if valid)
        """
        errors = []
        
        if not self.coaches:
            errors.append("No coaches loaded")
            return errors
        
        # Check for duplicate numbers
        nums = [c.num for c in self.coaches]
        if len(nums) != len(set(nums)):
            errors.append("Duplicate coach numbers found")
        
        # Check for required fields
        for i, coach in enumerate(self.coaches):
            if not coach.coach_name:
                errors.append(f"Coach {i+1}: Missing coach name")
            if not coach.team_name:
                errors.append(f"Coach {i+1}: Missing team name")
            if not coach.roster:
                errors.append(f"Coach {i+1}: Missing roster")
        
        return errors
    
    def __len__(self) -> int:
        """Return number of coaches."""
        return len(self.coaches)

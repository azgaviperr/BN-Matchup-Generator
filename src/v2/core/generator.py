# coding: utf-8
"""
Improved matchup generator with better algorithm and error handling.
"""

import random
from typing import List, Tuple, Dict, Set, Optional
import logging

logger = logging.getLogger(__name__)


class MatchupGeneratorError(Exception):
    """Base exception for matchup generator errors."""
    pass


class InvalidTeamCountError(MatchupGeneratorError):
    """Raised when team count is invalid."""
    pass


class GenerationFailedError(MatchupGeneratorError):
    """Raised when matchup generation fails."""
    pass


class MatchupGenerator:
    """
    Improved matchup generator using round-robin algorithm.
    Guarantees that each pair of teams meets exactly once across all days.
    """

    def __init__(self, n_teams: int, n_days: int):
        """
        Initialize the matchup generator.
        
        Args:
            n_teams: Number of teams (must be even)
            n_days: Number of days to generate
            
        Raises:
            InvalidTeamCountError: If n_teams is odd or invalid
        """
        if n_teams <= 0:
            raise InvalidTeamCountError("Number of teams must be positive")
        if n_teams % 2 != 0:
            raise InvalidTeamCountError("Number of teams must be even")
        if n_days <= 0:
            raise InvalidTeamCountError("Number of days must be positive")
        if n_days > n_teams - 1:
            raise InvalidTeamCountError(
                f"Number of days cannot exceed {n_teams - 1} for {n_teams} teams"
            )
        
        self.n_teams = n_teams
        self.n_days = n_days
        self.teams = list(range(1, n_teams + 1))
        self.schedule: Dict[str, List[Tuple[int, int]]] = {}
        
        logger.info(f"Initialized MatchupGenerator with {n_teams} teams and {n_days} days")

    def generate(self, seed: Optional[int] = None) -> bool:
        """
        Generate matchups using an improved round-robin algorithm.
        
        Args:
            seed: Optional random seed for reproducibility
            
        Returns:
            True if generation succeeded, False otherwise
        """
        if seed is not None:
            random.seed(seed)
        
        try:
            # Use circle method for round-robin tournament
            self._generate_round_robin()
            return True
        except Exception as e:
            logger.error(f"Generation failed: {e}")
            return False

    def _generate_round_robin(self):
        """
        Generate matches using the circle method (round-robin algorithm).
        This guarantees a complete and fair schedule.
        """
        teams = self.teams.copy()
        
        # Shuffle teams for variety (controlled by seed if set)
        random.shuffle(teams)
        
        # For the circle method, we fix one team and rotate others
        fixed_team = teams[0]
        rotating_teams = teams[1:]
        
        self.schedule = {}
        
        for day in range(1, self.n_days + 1):
            day_matches = []
            
            # Match the fixed team with the first rotating team
            day_matches.append((fixed_team, rotating_teams[0]))
            
            # Match the remaining teams in pairs
            for i in range(1, len(rotating_teams) // 2 + 1):
                if i < len(rotating_teams) - i + 1:
                    day_matches.append((rotating_teams[i], rotating_teams[-i]))
            
            self.schedule[f"Journée {day}"] = day_matches
            
            # Rotate the teams (all except the fixed one)
            rotating_teams = [rotating_teams[-1]] + rotating_teams[:-1]
        
        logger.info(f"Successfully generated {self.n_days} days of matches")

    def get_schedule(self) -> Dict[str, List[Tuple[int, int]]]:
        """Get the generated schedule."""
        return self.schedule.copy()

    def get_all_matches(self) -> List[Tuple[int, int]]:
        """Get a flat list of all scheduled matches."""
        matches = []
        for day_matches in self.schedule.values():
            matches.extend(day_matches)
        return matches

    def validate_schedule(self) -> bool:
        """
        Validate that the schedule is correct:
        - No team plays twice on same day
        - Each team plays in each day
        - No repeat matchups
        
        Returns:
            True if schedule is valid
        """
        if not self.schedule:
            return False
        
        all_matchups: Set[Tuple[int, int]] = set()
        
        for day, matches in self.schedule.items():
            teams_on_day: Set[int] = set()
            
            # Check each match
            for match in matches:
                team1, team2 = match
                
                # Check no team plays twice on same day
                if team1 in teams_on_day or team2 in teams_on_day:
                    logger.error(f"Team plays twice on {day}")
                    return False
                
                teams_on_day.add(team1)
                teams_on_day.add(team2)
                
                # Check for duplicate matchups (normalize order)
                normalized_match = tuple(sorted(match))
                if normalized_match in all_matchups:
                    logger.error(f"Duplicate matchup: {normalized_match}")
                    return False
                
                all_matchups.add(normalized_match)
            
            # Check all teams play on this day
            if len(teams_on_day) != self.n_teams:
                logger.error(f"Not all teams play on {day}")
                return False
        
        return True

    def save_to_dict(self) -> Dict:
        """
        Export schedule as a dictionary for JSON serialization.
        
        Returns:
            Dictionary representation of the schedule
        """
        return {
            "n_teams": self.n_teams,
            "n_days": self.n_days,
            "schedule": {
                day: [[m[0], m[1]] for m in matches]
                for day, matches in self.schedule.items()
            }
        }

    @classmethod
    def load_from_dict(cls, data: Dict) -> 'MatchupGenerator':
        """
        Load schedule from a dictionary.
        
        Args:
            data: Dictionary with schedule data
            
        Returns:
            New MatchupGenerator instance with loaded schedule
        """
        gen = cls(data["n_teams"], data["n_days"])
        gen.schedule = {
            day: [tuple(m) for m in matches]
            for day, matches in data["schedule"].items()
        }
        return gen

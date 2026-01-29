# coding: utf-8
"""
Simple tests for V2 core functionality.
"""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from v2.core.generator import MatchupGenerator, InvalidTeamCountError
from v2.core.models import Coach, CoachManager


def test_matchup_generator_basic():
    """Test basic matchup generation."""
    print("Testing MatchupGenerator basic functionality...")
    
    # Test with 4 teams, 3 days
    gen = MatchupGenerator(4, 3)
    assert gen.n_teams == 4
    assert gen.n_days == 3
    
    # Generate schedule
    assert gen.generate() == True
    
    # Validate
    assert gen.validate_schedule() == True
    
    # Check schedule structure
    schedule = gen.get_schedule()
    assert len(schedule) == 3  # 3 days
    
    for day, matches in schedule.items():
        assert len(matches) == 2  # 4 teams = 2 matches per day
        
        # Check all teams play
        teams_in_day = set()
        for match in matches:
            teams_in_day.add(match[0])
            teams_in_day.add(match[1])
        assert len(teams_in_day) == 4
    
    print("✓ Basic generation test passed")


def test_matchup_generator_errors():
    """Test error handling."""
    print("Testing MatchupGenerator error handling...")
    
    # Test odd number of teams
    try:
        gen = MatchupGenerator(5, 3)
        assert False, "Should have raised InvalidTeamCountError"
    except InvalidTeamCountError:
        pass
    
    # Test too many days
    try:
        gen = MatchupGenerator(4, 10)  # Max is 3 days for 4 teams
        assert False, "Should have raised InvalidTeamCountError"
    except InvalidTeamCountError:
        pass
    
    print("✓ Error handling test passed")


def test_coach_model():
    """Test Coach and CoachManager."""
    print("Testing Coach model...")
    
    coach1 = Coach(
        num=1,
        coach_name="Coach A",
        team_name="Team A",
        roster="Humans",
        groupe="Group 1"
    )
    
    assert coach1.coach_name == "Coach A"
    assert coach1.num == 1
    
    # Test to_dict
    data = coach1.to_dict()
    assert data["coach_name"] == "Coach A"
    
    # Test from_dict
    coach2 = Coach.from_dict(data)
    assert coach2.coach_name == "Coach A"
    assert coach2.num == 1
    
    print("✓ Coach model test passed")


def test_coach_manager():
    """Test CoachManager."""
    print("Testing CoachManager...")
    
    manager = CoachManager()
    
    # Add coaches
    manager.add_coach(Coach(1, "Coach A", "Team A", "Humans"))
    manager.add_coach(Coach(2, "Coach B", "Team B", "Orcs"))
    
    assert len(manager) == 2
    
    # Get by num
    coach = manager.get_coach_by_num(1)
    assert coach.coach_name == "Coach A"
    
    # Validate
    errors = manager.validate()
    assert len(errors) == 0
    
    print("✓ CoachManager test passed")


def test_complete_workflow():
    """Test a complete workflow."""
    print("Testing complete workflow...")
    
    # Create coaches
    manager = CoachManager()
    manager.add_coach(Coach(1, "Alice", "Eagles", "Humans"))
    manager.add_coach(Coach(2, "Bob", "Crushers", "Orcs"))
    manager.add_coach(Coach(3, "Charlie", "Shadows", "Dark Elves"))
    manager.add_coach(Coach(4, "Diana", "Thunders", "Dwarves"))
    
    # Generate matchups
    gen = MatchupGenerator(4, 3)
    gen.generate()
    
    # Validate
    assert gen.validate_schedule() == True
    
    # Check no duplicate matchups
    all_matches = set()
    for day, matches in gen.schedule.items():
        for match in matches:
            normalized = tuple(sorted(match))
            assert normalized not in all_matches, "Duplicate matchup found!"
            all_matches.add(normalized)
    
    print("✓ Complete workflow test passed")


def run_all_tests():
    """Run all tests."""
    print("="*60)
    print("Running V2 Tests")
    print("="*60)
    
    try:
        test_matchup_generator_basic()
        test_matchup_generator_errors()
        test_coach_model()
        test_coach_manager()
        test_complete_workflow()
        
        print("="*60)
        print("✓ All tests passed!")
        print("="*60)
        return True
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)

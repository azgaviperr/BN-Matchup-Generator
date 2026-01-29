#!/usr/bin/env python3
# coding: utf-8
"""
Example: Complete V2 Workflow
Demonstrates all V2 features programmatically.
"""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from v2.core.generator import MatchupGenerator
from v2.core.models import Coach, CoachManager
from v2.exports.exporter import MatchupExporter
from v2.utils.file_utils import ensure_dir

def example_basic():
    """Basic matchup generation example."""
    print("=" * 60)
    print("Example 1: Basic Matchup Generation")
    print("=" * 60)
    
    # Create coaches
    manager = CoachManager()
    coaches_data = [
        (1, "Alice", "Eagles", "Humans", "A"),
        (2, "Bob", "Crushers", "Orcs", "A"),
        (3, "Charlie", "Shadows", "Dark Elves", "B"),
        (4, "Diana", "Thunders", "Dwarves", "B"),
    ]
    
    for num, name, team, roster, groupe in coaches_data:
        manager.add_coach(Coach(num, name, team, roster, groupe))
    
    print(f"✓ Loaded {len(manager)} coaches")
    
    # Generate schedule
    gen = MatchupGenerator(4, 3)
    gen.generate()
    
    print(f"✓ Generated schedule for 3 days")
    
    # Display schedule
    for day, matches in gen.get_schedule().items():
        print(f"\n{day}:")
        for match in matches:
            coach1 = manager.get_coach_by_num(match[0])
            coach2 = manager.get_coach_by_num(match[1])
            print(f"  {coach1.coach_name} ({coach1.team_name}) vs "
                  f"{coach2.coach_name} ({coach2.team_name})")
    
    print()

def example_file_io():
    """Example using file I/O."""
    print("=" * 60)
    print("Example 2: File-based Workflow")
    print("=" * 60)
    
    # Load from CSV
    manager = CoachManager()
    
    # Create sample CSV if it doesn't exist
    if not os.path.exists("coachs_extract.csv"):
        manager.add_coach(Coach(1, "Alice", "Eagles", "Humans"))
        manager.add_coach(Coach(2, "Bob", "Crushers", "Orcs"))
        manager.add_coach(Coach(3, "Charlie", "Shadows", "Dark Elves"))
        manager.add_coach(Coach(4, "Diana", "Thunders", "Dwarves"))
        manager.save_to_csv("coachs_extract.csv")
        print("✓ Created sample coachs_extract.csv")
    
    # Load it back
    manager = CoachManager()
    count = manager.load_from_csv("coachs_extract.csv")
    print(f"✓ Loaded {count} coaches from CSV")
    
    # Validate
    errors = manager.validate()
    if errors:
        print(f"✗ Validation errors: {errors}")
        return
    print("✓ Validation passed")
    
    # Generate
    gen = MatchupGenerator(len(manager), 3)
    gen.generate()
    print("✓ Generated schedule")
    
    # Export
    coach_map = {
        str(c.num): {
            "coach_name": c.coach_name,
            "team_name": c.team_name,
            "roster": c.roster,
            "groupe": c.groupe
        }
        for c in manager.get_all_coaches()
    }
    
    outdir = "example_output"
    ensure_dir(outdir)
    
    exporter = MatchupExporter(gen.get_schedule(), coach_map)
    exporter.export_csv(os.path.join(outdir, "schedule.csv"))
    exporter.export_json(os.path.join(outdir, "schedule.json"))
    exporter.export_markdown(os.path.join(outdir, "schedule.md"))
    
    print(f"✓ Exported results to {outdir}/")
    print()

def example_validation():
    """Example showing validation features."""
    print("=" * 60)
    print("Example 3: Validation and Error Handling")
    print("=" * 60)
    
    from v2.core.generator import InvalidTeamCountError
    
    # Test 1: Odd number of teams
    try:
        gen = MatchupGenerator(5, 3)
        print("✗ Should have raised error for odd teams")
    except InvalidTeamCountError as e:
        print(f"✓ Caught error for odd teams: {e}")
    
    # Test 2: Too many days
    try:
        gen = MatchupGenerator(4, 10)
        print("✗ Should have raised error for too many days")
    except InvalidTeamCountError as e:
        print(f"✓ Caught error for too many days: {e}")
    
    # Test 3: Valid generation and validation
    gen = MatchupGenerator(6, 5)
    gen.generate()
    
    if gen.validate_schedule():
        print("✓ Schedule validation passed")
    else:
        print("✗ Schedule validation failed")
    
    # Check for duplicate matchups
    all_matches = set()
    duplicates = False
    
    for day, matches in gen.get_schedule().items():
        for match in matches:
            normalized = tuple(sorted(match))
            if normalized in all_matches:
                print(f"✗ Duplicate matchup found: {normalized}")
                duplicates = True
            all_matches.add(normalized)
    
    if not duplicates:
        print(f"✓ No duplicate matchups (checked {len(all_matches)} matches)")
    
    print()

def example_serialization():
    """Example showing save/load of schedules."""
    print("=" * 60)
    print("Example 4: Schedule Serialization")
    print("=" * 60)
    
    # Generate a schedule
    gen = MatchupGenerator(4, 3)
    gen.generate()
    
    # Save to dict
    data = gen.save_to_dict()
    print(f"✓ Serialized schedule: {len(data['schedule'])} days")
    
    # Load it back
    gen2 = MatchupGenerator.load_from_dict(data)
    print(f"✓ Deserialized schedule: {len(gen2.get_schedule())} days")
    
    # Verify they're the same
    if gen.get_schedule() == gen2.get_schedule():
        print("✓ Schedules match after serialization")
    else:
        print("✗ Schedules don't match")
    
    print()

def example_reproducibility():
    """Example showing reproducible generation."""
    print("=" * 60)
    print("Example 5: Reproducible Generation with Seeds")
    print("=" * 60)
    
    # Generate with seed
    gen1 = MatchupGenerator(6, 5)
    gen1.generate(seed=42)
    schedule1 = gen1.get_all_matches()
    
    # Generate again with same seed
    gen2 = MatchupGenerator(6, 5)
    gen2.generate(seed=42)
    schedule2 = gen2.get_all_matches()
    
    if schedule1 == schedule2:
        print("✓ Same seed produces identical schedules")
    else:
        print("✗ Schedules differ with same seed")
    
    # Generate with different seed
    gen3 = MatchupGenerator(6, 5)
    gen3.generate(seed=123)
    schedule3 = gen3.get_all_matches()
    
    if schedule1 != schedule3:
        print("✓ Different seed produces different schedule")
    else:
        print("✗ Different seeds produced same schedule")
    
    print()

def run_all_examples():
    """Run all examples."""
    print("\n" + "=" * 60)
    print("BN Matchup Generator V2 - Complete Examples")
    print("=" * 60 + "\n")
    
    example_basic()
    example_file_io()
    example_validation()
    example_serialization()
    example_reproducibility()
    
    print("=" * 60)
    print("All examples completed successfully!")
    print("=" * 60)

if __name__ == "__main__":
    run_all_examples()

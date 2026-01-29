# Migration Guide - V1 to V2

## Overview

This guide helps you migrate from the legacy version (V1/V3) to the new V2 architecture.

## Key Differences

### Architecture

**V1/V3:**
- Single monolithic file (880 lines)
- Mixed business logic and UI
- Limited error handling

**V2:**
- Modular structure with separate concerns
- Clean separation of core logic, UI, and exports
- Comprehensive error handling and logging

### Algorithm

**V1/V3:**
- Random shuffling with retry attempts
- May fail after 1001 tries
- No guaranteed optimal solution

**V2:**
- Round-robin algorithm
- Always succeeds for valid inputs
- Mathematically optimal distribution

### Usage

**V1/V3:**
```bash
python matchup_generator.py  # GUI only
```

**V2:**
```bash
python matchup_generator_v2.py              # GUI mode
python matchup_generator_v2.py --cli ...    # CLI mode
```

## File Format Compatibility

The V2 is 100% compatible with V1 CSV files. Your existing `coachs_extract.csv` files will work without modification.

### Required Columns
- `num` - Team number (integer)
- `coach` - Coach name (string)
- `team` - Team name (string)
- `roster` - Roster/race (string)
- `groupe` - Group (optional, string)

## Feature Comparison

| Feature | V1 | V2 |
|---------|----|----|
| GUI | ✓ | ✓ |
| CLI | ✗ | ✓ |
| CSV Export | ✓ | ✓ |
| JSON Export | ✗ | ✓ |
| Markdown Export | ✓ | ✓ |
| PDF Export | ✓ | ✓* |
| Tests | ✗ | ✓ |
| Logging | Basic | Complete |
| Error Messages | Basic | Detailed |
| Validation | Basic | Comprehensive |

*PDF export requires optional dependencies

## Migration Steps

### 1. Install V2

V2 is installed alongside V1, not replacing it:

```bash
# Install dependencies (if needed)
pip install -r requirements.txt
```

### 2. Test with Existing Data

```bash
# Test V2 with your existing coach file
python matchup_generator_v2.py --coaches coachs_extract.csv --days 11
```

### 3. Compare Results

Both versions should produce valid schedules, but:
- V2 uses a different algorithm (round-robin)
- Schedules will differ but both are correct
- V2 guarantees success for valid inputs

### 4. Update Build Scripts

If you build executables:

```bash
# V1 build
python build.py

# V2 build
python build_v2.py
```

## Code Migration

If you've extended the V1 code, here's how to migrate:

### Loading Coaches

**V1:**
```python
def load_coachs_from_csv(csv_path):
    with open(csv_path, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        return [row for row in reader]
```

**V2:**
```python
from v2.core.models import CoachManager

manager = CoachManager()
manager.load_from_csv("coachs_extract.csv")
```

### Generating Schedule

**V1:**
```python
gen = MatchupGenerator(n_teams, n_days)
if gen.generate():
    schedule = gen.schedule
```

**V2:**
```python
from v2.core.generator import MatchupGenerator

gen = MatchupGenerator(n_teams, n_days)
if gen.generate():
    schedule = gen.get_schedule()
    # Also validate
    is_valid = gen.validate_schedule()
```

### Exporting Results

**V1:**
```python
save_enriched_matchups_csv(filename, schedule, coachs_map)
```

**V2:**
```python
from v2.exports.exporter import MatchupExporter

exporter = MatchupExporter(schedule, coach_map)
exporter.export_csv(filename)
exporter.export_json(json_file)
exporter.export_markdown(md_file)
```

## Backwards Compatibility

V2 maintains compatibility with:
- ✓ CSV file format
- ✓ Output directory structure
- ✓ File naming conventions
- ✓ French UI text

V2 changes:
- ✗ Internal API (for developers)
- ✗ Algorithm (different but correct results)

## Troubleshooting

### "Module not found" Error

Make sure you're running from the repository root:
```bash
cd /path/to/BN-Matchup-Generator
python matchup_generator_v2.py
```

### GUI Not Working

Try CLI mode:
```bash
python matchup_generator_v2.py --coaches coachs_extract.csv --days 11
```

### Different Results Than V1

This is expected! V2 uses a round-robin algorithm while V1 uses random shuffling. Both produce valid schedules, they're just different.

## Need Help?

- Check the [V2 README](README_V2.md)
- Run tests: `python test_v2.py`
- Open an issue on GitHub

## Recommendation

- **New projects**: Use V2
- **Existing projects**: Can continue with V1 or migrate to V2
- **Development**: V2 architecture is cleaner for contributions

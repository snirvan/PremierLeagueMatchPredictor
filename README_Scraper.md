# Premier League Match Data Scraper

This script automatically downloads the latest Premier League match data from [football-data.co.uk](https://www.football-data.co.uk/englandm.php) and updates your existing dataset with new matches, including all engineered features.

## Features

- 🔄 **Automatic Data Download**: Fetches the latest 2025/2026 season data from football-data.co.uk
- 🆕 **New Match Detection**: Identifies matches not already in your dataset
- ⚙️ **Feature Engineering**: Applies all the same feature engineering as your existing pipeline:
  - Rolling statistics (goals, shots, cards, points)
  - Head-to-head features
  - Market value integration
  - Goal difference calculations
  - Gap features (value_gap, points_gap, etc.)
  - Balance features (ratios between home/away stats)
- 💾 **Safe Updates**: Creates backups before updating your data
- 🔍 **Smart Column Alignment**: Ensures new data matches your existing dataset structure

## Usage

### Prerequisites

Make sure you have the required Python packages:

```bash
pip install -r scraper_requirements.txt
```

Or if using your virtual environment:

```bash
source venv/bin/activate
pip install -r scraper_requirements.txt
```

### Running the Scraper

Simply run the script:

```bash
python update_matches_scraper.py
```

### What It Does

1. **Downloads** the latest CSV from https://www.football-data.co.uk/mmz4281/2526/E0.csv
2. **Compares** with your existing `matches_features_with_balance.csv`
3. **Identifies** any new matches not in your dataset
4. **Engineers** all the features for new matches using the same logic as your pipeline
5. **Updates** your dataset with the new matches
6. **Creates** a timestamped backup of your original file

### Output

The script will:
- Show progress messages as it works
- Display how many new matches were found and added
- Create a backup file like `matches_features_with_balance.csv.backup_20250910_143022`
- Update your main `matches_features_with_balance.csv` file

### Example Output

```
🚀 Starting Premier League Match Data Update

📥 Downloading latest 2025/2026 Premier League data...
✅ Successfully downloaded latest data
📂 Loading existing data from matches_features_with_balance.csv...
📊 Existing dataset has 2272 matches
🔄 Processing new season data...
✅ Processed 38 matches from new season
🔍 Identifying new matches...
🆕 Found 5 new matches
⚙️  Engineering features for new matches...
✅ Engineered features for 5 new matches
🔄 Updating dataset...
💾 Backup created: matches_features_with_balance.csv.backup_20250910_143022

✅ Successfully updated dataset!
📈 Added 5 new matches
📊 Total matches in dataset: 2277
💾 Updated file: matches_features_with_balance.csv

🆕 Sample of new matches:
        Date    HomeTeam     AwayTeam  FTHG  FTAG FTR
2025-08-15   Liverpool  Bournemouth     4     2   H
2025-08-16  Aston Villa    Newcastle     0     0   D
2025-08-16     Brighton      Fulham     1     1   D
2025-08-16   Sunderland     West Ham     3     0   H
2025-08-17      Arsenal      Wolves     2     0   H
```

## Files Used

- **Input**: `matches_features_with_balance.csv` (your existing dataset)
- **Input**: `premier_league_market_values.csv` (for market value features, optional)
- **Output**: Updated `matches_features_with_balance.csv`
- **Backup**: `matches_features_with_balance.csv.backup_YYYYMMDD_HHMMSS`

## Feature Engineering Details

The scraper applies the exact same feature engineering pipeline as your existing scripts:

### Rolling Features (5-game window)
- Goals for/against (mean & sum)
- Shots & shots on target (mean & sum)
- Cards (mean & sum)
- Points (mean & sum)

### Derived Features
- Goal difference rolling stats
- Previous season points
- Head-to-head points (last 5 meetings)
- Market value integration

### Gap Features (absolute differences)
- `value_gap`: Market value difference
- `points_gap`: Points difference
- `goal_diff_gap`: Goal difference gap
- `shots_gap`: Shots per game gap
- `shots_ot_gap`: Shots on target gap
- `cards_gap`: Cards per game gap
- `goals_for_gap`: Goals scored gap
- `conceded_gap`: Goals conceded gap

### Balance Features (ratios)
- `shots_ratio`: Home shots / Away shots
- `shots_ot_ratio`: Home shots on target / Away shots on target
- `goals_for_ratio`: Home goals for / Away goals for
- `conceded_ratio`: Home goals against / Away goals against

## Configuration

You can modify these settings at the top of `update_matches_scraper.py`:

```python
CURRENT_SEASON_URL = "https://www.football-data.co.uk/mmz4281/2526/E0.csv"
EXISTING_DATA_FILE = "matches_features_with_balance.csv"
MARKET_VALUES_FILE = "premier_league_market_values.csv"
ROLLING_WINDOW = 5
CURRENT_SEASON = 2025
```

## Automation

You can set this up to run automatically using cron (Linux/Mac) or Task Scheduler (Windows):

### Cron Example (daily at 9 AM)
```bash
0 9 * * * cd /path/to/PremierLeaguePredictor && python update_matches_scraper.py
```

## Error Handling

The script includes robust error handling:
- Network timeouts and connection errors
- Missing files (creates defaults where possible)
- Column mismatches (adds missing columns)
- Data validation and cleanup

## Notes

- The script only adds **new** matches - it won't duplicate existing data
- All feature engineering uses the same rolling window and logic as your existing pipeline
- Market values are optional - if the file is missing, values default to 0
- The script is designed to be safe - it always creates backups before making changes

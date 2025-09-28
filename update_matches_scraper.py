#!/usr/bin/env python3
"""
Premier League Match Data Updater

This script scrapes the latest 2025/2026 Premier League match data from 
football-data.co.uk and updates the existing matches_features_with_balance.csv
with any new matches, including all engineered features.

Usage:
    python update_matches_scraper.py
"""

import requests
import pandas as pd
import numpy as np
from datetime import datetime
import os
import sys

# Configuration
CURRENT_SEASON_URL = "https://www.football-data.co.uk/mmz4281/2526/E0.csv"
EXISTING_DATA_FILE = "matches_features_with_balance.csv"
MARKET_VALUES_FILE = "premier_league_market_values.csv"
ROLLING_WINDOW = 5
CURRENT_SEASON = 2025

def download_latest_data():
    """Download the latest season data from football-data.co.uk"""
    print("📥 Downloading latest 2025/2026 Premier League data...")
    
    try:
        response = requests.get(CURRENT_SEASON_URL, timeout=30)
        response.raise_for_status()
        
        # Save to temporary file
        temp_file = "temp_new_season.csv"
        with open(temp_file, 'wb') as f:
            f.write(response.content)
        
        print("✅ Successfully downloaded latest data")
        return temp_file
    
    except requests.RequestException as e:
        print(f"❌ Error downloading data: {e}")
        sys.exit(1)

def load_existing_data():
    """Load the existing matches dataset"""
    if not os.path.exists(EXISTING_DATA_FILE):
        print(f"❌ Existing data file not found: {EXISTING_DATA_FILE}")
        sys.exit(1)
    
    print(f"📂 Loading existing data from {EXISTING_DATA_FILE}...")
    return pd.read_csv(EXISTING_DATA_FILE, parse_dates=['Date'])

def load_market_values():
    """Load market value data for feature engineering"""
    if not os.path.exists(MARKET_VALUES_FILE):
        print(f"⚠️  Market values file not found: {MARKET_VALUES_FILE}")
        return None
    
    return pd.read_csv(MARKET_VALUES_FILE)

def preprocess_new_data(temp_file):
    """Load and preprocess the new season data"""
    print("🔄 Processing new season data...")
    
    # Load new data
    new_df = pd.read_csv(temp_file)
    
    # Add season column
    new_df['Season'] = CURRENT_SEASON
    
    # Convert date
    new_df['Date'] = pd.to_datetime(new_df['Date'], format='%d/%m/%Y')
    
    # Create Result column (-1: Away win, 0: Draw, 1: Home win)
    result_map = {'H': 1, 'D': 0, 'A': -1}
    new_df['Result'] = new_df['FTR'].map(result_map)
    
    # Clean up temporary file
    os.remove(temp_file)
    
    print(f"✅ Processed {len(new_df)} matches from new season")
    return new_df

def identify_new_matches(new_df, existing_df):
    """Identify matches that are not in the existing dataset"""
    print("🔍 Identifying new matches...")
    
    # Create unique match identifiers
    new_df['match_id'] = (new_df['Date'].dt.strftime('%Y-%m-%d') + 
                         '_' + new_df['HomeTeam'] + '_' + new_df['AwayTeam'])
    
    existing_df['match_id'] = (existing_df['Date'].dt.strftime('%Y-%m-%d') + 
                              '_' + existing_df['HomeTeam'] + '_' + existing_df['AwayTeam'])
    
    # Find new matches
    new_match_ids = set(new_df['match_id']) - set(existing_df['match_id'])
    new_matches = new_df[new_df['match_id'].isin(new_match_ids)].copy()
    
    print(f"🆕 Found {len(new_matches)} new matches")
    
    if len(new_matches) == 0:
        print("✅ No new matches to process")
        return None
    
    # Remove temporary match_id columns
    new_matches = new_matches.drop('match_id', axis=1)
    
    return new_matches

def compute_points(row):
    """Return points for home and away teams from match result."""
    # Ensure Result is properly mapped
    if pd.isna(row.get("Result")) if hasattr(pd, 'isna') else row.get("Result") is None:
        # If Result is missing, map from FTR
        result_map = {'H': 1, 'D': 0, 'A': -1}
        result = result_map.get(row.get("FTR"))
    else:
        result = row["Result"]
    
    if result == 1:      # Home win
        return 3, 0
    elif result == -1:   # Away win
        return 0, 3
    else:                # Draw (result == 0)
        return 1, 1

def build_team_match_history(df):
    """Expand matches into team-centric rows for rolling features."""
    rows = []
    for _, row in df.iterrows():
        home_points, away_points = compute_points(row)

        rows.append({
            "Season": row["Season"],
            "Date": row["Date"],
            "Team": row["HomeTeam"],
            "Opponent": row["AwayTeam"],
            "is_home": 1,
            "GoalsFor": row["FTHG"],
            "GoalsAgainst": row["FTAG"],
            "Shots": row.get("HS", np.nan),
            "ShotsOT": row.get("HST", np.nan),
            "Cards": row.get("HY", 0) + 2 * row.get("HR", 0),
            "Points": home_points
        })

        rows.append({
            "Season": row["Season"],
            "Date": row["Date"],
            "Team": row["AwayTeam"],
            "Opponent": row["HomeTeam"],
            "is_home": 0,
            "GoalsFor": row["FTAG"],
            "GoalsAgainst": row["FTHG"],
            "Shots": row.get("AS", np.nan),
            "ShotsOT": row.get("AST", np.nan),
            "Cards": row.get("AY", 0) + 2 * row.get("AR", 0),
            "Points": away_points
        })
    return pd.DataFrame(rows)

def compute_rolling_features(team_df):
    """Compute rolling averages AND sums per team."""
    team_df = team_df.sort_values(["Team", "Date"])
    for col in ["GoalsFor", "GoalsAgainst", "Shots", "ShotsOT", "Cards", "Points"]:
        team_df[f"{col}_rolling_mean"] = (
            team_df.groupby("Team")[col]
            .transform(lambda x: x.shift().rolling(ROLLING_WINDOW, min_periods=1).mean())
        )
        team_df[f"{col}_rolling_sum"] = (
            team_df.groupby("Team")[col]
            .transform(lambda x: x.shift().rolling(ROLLING_WINDOW, min_periods=1).sum())
        )
    return team_df

def compute_prev_season_points(team_df):
    """Total points per season → carried into next year as PrevSeasonPoints."""
    season_points = team_df.groupby(["Season", "Team"])["Points"].sum().reset_index()
    season_points["PrevSeason"] = season_points["Season"] + 1
    season_points = season_points.rename(columns={"Points": "PrevSeasonPoints"})
    return season_points[["PrevSeason", "Team", "PrevSeasonPoints"]]

def normalize_team_names(df):
    """Normalize team names to handle inconsistencies between seasons"""
    team_mapping = {
        "Nottm Forest": "Nott'm Forest",
        "Fullham": "Fulham",
        # Add more mappings as needed
    }
    
    df = df.copy()
    if 'HomeTeam' in df.columns:
        df['HomeTeam'] = df['HomeTeam'].replace(team_mapping)
    if 'AwayTeam' in df.columns:
        df['AwayTeam'] = df['AwayTeam'].replace(team_mapping)
    if 'Team' in df.columns:
        df['Team'] = df['Team'].replace(team_mapping)
    
    return df

def compute_h2h_features(df, n=5):
    """Compute head-to-head points for both home and away teams over last N matches."""
    h2h_rows = []
    for i, row in df.iterrows():
        home, away, match_date = row["HomeTeam"], row["AwayTeam"], row["Date"]

        past = df[
            (((df["HomeTeam"] == home) & (df["AwayTeam"] == away)) |
             ((df["HomeTeam"] == away) & (df["AwayTeam"] == home))) &
            (df["Date"] < match_date)
        ].sort_values("Date", ascending=False).head(n)

        points_home, points_away = 0, 0
        for _, p in past.iterrows():
            # Home team perspective
            if p["HomeTeam"] == home:
                points_home += 3 if p["Result"] == 1 else 1 if p["Result"] == 0 else 0
            else:
                points_home += 3 if p["Result"] == -1 else 1 if p["Result"] == 0 else 0

            # Away team perspective
            if p["HomeTeam"] == away:
                points_away += 3 if p["Result"] == 1 else 1 if p["Result"] == 0 else 0
            else:
                points_away += 3 if p["Result"] == -1 else 1 if p["Result"] == 0 else 0

        h2h_rows.append({
            "Season": row["Season"],
            "Date": row["Date"],
            "HomeTeam": home,
            "AwayTeam": away,
            "h2h_points_home": points_home,
            "h2h_points_away": points_away
        })
    return pd.DataFrame(h2h_rows)

def add_market_values(features_df, market_df):
    """Add market value features"""
    if market_df is None:
        print("⚠️  Skipping market values (file not found)")
        features_df['home_value'] = 0.0
        features_df['away_value'] = 0.0
        return features_df
    
    # Standardize market data
    market_df = market_df.rename(columns={
        "Year": "Season",
        "Team": "Team",
        "Market Value": "market_value_million"
    })
    
    # Home merge
    home_market = market_df.rename(columns={
        "Team": "HomeTeam",
        "market_value_million": "home_value"
    })
    features_df = features_df.merge(
        home_market[["Season", "HomeTeam", "home_value"]],
        on=["Season", "HomeTeam"],
        how="left"
    )
    
    # Away merge
    away_market = market_df.rename(columns={
        "Team": "AwayTeam",
        "market_value_million": "away_value"
    })
    features_df = features_df.merge(
        away_market[["Season", "AwayTeam", "away_value"]],
        on=["Season", "AwayTeam"],
        how="left"
    )
    
    # Fill missing values with 0
    features_df['home_value'] = features_df['home_value'].fillna(0.0)
    features_df['away_value'] = features_df['away_value'].fillna(0.0)
    
    return features_df

def add_goal_diff_features(features_df):
    """Add goal difference rolling features"""
    # Home rolling goal differentials
    features_df["home_goal_diff_rolling_mean"] = (
        features_df["home_GoalsFor_rolling_mean"] - features_df["home_GoalsAgainst_rolling_mean"]
    )
    features_df["home_goal_diff_rolling_sum"] = (
        features_df["home_GoalsFor_rolling_sum"] - features_df["home_GoalsAgainst_rolling_sum"]
    )
    
    # Away rolling goal differentials
    features_df["away_goal_diff_rolling_mean"] = (
        features_df["away_GoalsFor_rolling_mean"] - features_df["away_GoalsAgainst_rolling_mean"]
    )
    features_df["away_goal_diff_rolling_sum"] = (
        features_df["away_GoalsFor_rolling_sum"] - features_df["away_GoalsAgainst_rolling_sum"]
    )
    
    return features_df

def add_points_features(features_df, team_df):
    """Add cumulative points features for current season"""
    # Calculate cumulative points for current season up to each match
    season_points = []
    
    for _, row in features_df.iterrows():
        # Get home team's cumulative points in current season before this match
        home_season_matches = team_df[
            (team_df['Team'] == row['HomeTeam']) & 
            (team_df['Season'] == row['Season']) & 
            (team_df['Date'] < row['Date'])
        ]
        home_points_sum = home_season_matches['Points'].sum() if not home_season_matches.empty else 0.0
        
        # Get away team's cumulative points in current season before this match
        away_season_matches = team_df[
            (team_df['Team'] == row['AwayTeam']) & 
            (team_df['Season'] == row['Season']) & 
            (team_df['Date'] < row['Date'])
        ]
        away_points_sum = away_season_matches['Points'].sum() if not away_season_matches.empty else 0.0
        
        season_points.append({
            'home_points_sum': home_points_sum,
            'away_points_sum': away_points_sum
        })
    
    # Add the calculated points to features_df
    points_df = pd.DataFrame(season_points)
    features_df['home_points_sum'] = points_df['home_points_sum']
    features_df['away_points_sum'] = points_df['away_points_sum']
    
    return features_df

def add_gap_features(features_df):
    """Add gap features (absolute differences between home and away stats)"""
    
    # Market value gap
    if "home_value" in features_df.columns and "away_value" in features_df.columns:
        features_df["value_gap"] = (features_df["home_value"] - features_df["away_value"]).abs()
    
    # Points gap (based on current season totals)
    if "home_points_sum" in features_df.columns and "away_points_sum" in features_df.columns:
        features_df["points_gap"] = (features_df["home_points_sum"] - features_df["away_points_sum"]).abs()
    
    # Goal difference gap
    if "home_goal_diff_rolling_sum" in features_df.columns and "away_goal_diff_rolling_sum" in features_df.columns:
        features_df["goal_diff_gap"] = (features_df["home_goal_diff_rolling_sum"] - features_df["away_goal_diff_rolling_sum"]).abs()
    
    # Shots gap
    if "home_Shots_rolling_mean" in features_df.columns and "away_Shots_rolling_mean" in features_df.columns:
        features_df["shots_gap"] = (features_df["home_Shots_rolling_mean"] - features_df["away_Shots_rolling_mean"]).abs()
    
    # Shots on target gap
    if "home_ShotsOT_rolling_mean" in features_df.columns and "away_ShotsOT_rolling_mean" in features_df.columns:
        features_df["shots_ot_gap"] = (features_df["home_ShotsOT_rolling_mean"] - features_df["away_ShotsOT_rolling_mean"]).abs()
    
    # Cards gap
    if "home_Cards_rolling_mean" in features_df.columns and "away_Cards_rolling_mean" in features_df.columns:
        features_df["cards_gap"] = (features_df["home_Cards_rolling_mean"] - features_df["away_Cards_rolling_mean"]).abs()
    
    # Goals for gap
    if "home_GoalsFor_rolling_mean" in features_df.columns and "away_GoalsFor_rolling_mean" in features_df.columns:
        features_df["goals_for_gap"] = (features_df["home_GoalsFor_rolling_mean"] - features_df["away_GoalsFor_rolling_mean"]).abs()
    
    # Goals against gap
    if "home_GoalsAgainst_rolling_mean" in features_df.columns and "away_GoalsAgainst_rolling_mean" in features_df.columns:
        features_df["conceded_gap"] = (features_df["home_GoalsAgainst_rolling_mean"] - features_df["away_GoalsAgainst_rolling_mean"]).abs()
    
    return features_df

def add_balance_features(features_df):
    """Add ratio features for balance analysis"""
    
    # Shots ratio (avoid div by zero)
    if "home_Shots_rolling_mean" in features_df.columns and "away_Shots_rolling_mean" in features_df.columns:
        features_df["shots_ratio"] = features_df["home_Shots_rolling_mean"] / (features_df["away_Shots_rolling_mean"] + 1e-6)
    
    # Shots on target ratio
    if "home_ShotsOT_rolling_mean" in features_df.columns and "away_ShotsOT_rolling_mean" in features_df.columns:
        features_df["shots_ot_ratio"] = features_df["home_ShotsOT_rolling_mean"] / (features_df["away_ShotsOT_rolling_mean"] + 1e-6)
    
    # Goals For ratio
    if "home_GoalsFor_rolling_mean" in features_df.columns and "away_GoalsFor_rolling_mean" in features_df.columns:
        features_df["goals_for_ratio"] = features_df["home_GoalsFor_rolling_mean"] / (features_df["away_GoalsFor_rolling_mean"] + 1e-6)
    
    # Goals Against ratio
    if "home_GoalsAgainst_rolling_mean" in features_df.columns and "away_GoalsAgainst_rolling_mean" in features_df.columns:
        features_df["conceded_ratio"] = features_df["home_GoalsAgainst_rolling_mean"] / (features_df["away_GoalsAgainst_rolling_mean"] + 1e-6)
    
    return features_df

def engineer_features_for_new_matches(new_matches, existing_df, market_df):
    """Apply all feature engineering to new matches"""
    print("⚙️  Engineering features for new matches...")
    
    # Fix the Result column in existing data (it appears to be corrupted)
    existing_df = existing_df.copy()
    result_map = {'H': 1, 'D': 0, 'A': -1}
    existing_df['Result'] = existing_df['FTR'].map(result_map)
    
    # Create complete historical dataset for proper rolling calculations
    # This includes both existing data and new matches
    all_matches = pd.concat([existing_df, new_matches], ignore_index=True)
    all_matches = all_matches.sort_values(['Date']).reset_index(drop=True)
    
    # Build team match history from ALL data (existing + new)
    team_df = build_team_match_history(all_matches)
    
    # Compute rolling features using complete history
    team_df = compute_rolling_features(team_df)
    
    # Normalize team names to handle inconsistencies
    existing_df_norm = normalize_team_names(existing_df)
    all_matches_norm = normalize_team_names(all_matches)
    team_df = normalize_team_names(team_df)
    
    # Calculate previous season points from existing data only
    # This ensures we use actual historical performance, not including new matches
    existing_team_df = build_team_match_history(existing_df_norm)
    prev_points = compute_prev_season_points(existing_team_df)
    
    # Merge previous season points into the complete team dataset
    team_df = team_df.merge(
        prev_points, left_on=["Season", "Team"], right_on=["PrevSeason", "Team"], how="left"
    )
    team_df = team_df.drop(columns=["PrevSeason"], errors='ignore')
    
    # Fill missing previous season points with 0 (for newly promoted teams)
    team_df['PrevSeasonPoints'] = team_df['PrevSeasonPoints'].fillna(0.0)
    
    # Filter team_df to only include rows for new matches
    # Create a mapping to identify which team-date combinations are from new matches
    new_match_keys = set()
    for _, row in new_matches.iterrows():
        new_match_keys.add((row['Season'], row['Date'], row['HomeTeam']))
        new_match_keys.add((row['Season'], row['Date'], row['AwayTeam']))
    
    # Filter team_df to only rows corresponding to new matches
    team_df_new = team_df[
        team_df.apply(lambda x: (x['Season'], x['Date'], x['Team']) in new_match_keys, axis=1)
    ].copy()
    
    # Start with new matches
    features_df = new_matches.copy()
    
    # Home features - merge with filtered team data
    home_feats = team_df_new[team_df_new['is_home'] == 1].add_prefix("home_")
    features_df = features_df.merge(
        home_feats,
        left_on=["Season", "Date", "HomeTeam"],
        right_on=["home_Season", "home_Date", "home_Team"],
        how="left"
    )
    
    # Away features - merge with filtered team data  
    away_feats = team_df_new[team_df_new['is_home'] == 0].add_prefix("away_")
    features_df = features_df.merge(
        away_feats,
        left_on=["Season", "Date", "AwayTeam"],
        right_on=["away_Season", "away_Date", "away_Team"],
        how="left"
    )
    
    # Head-to-head features using complete match history
    h2h = compute_h2h_features(all_matches)
    h2h_new = h2h[h2h['Season'] == CURRENT_SEASON].copy()
    features_df = features_df.merge(
        h2h_new, on=["Season", "Date", "HomeTeam", "AwayTeam"], how="left"
    )
    
    # Add market values
    features_df = add_market_values(features_df, market_df)
    
    # Add goal difference features
    features_df = add_goal_diff_features(features_df)
    
    # Add points features (pass team_df for season calculations)
    features_df = add_points_features(features_df, team_df)
    
    # Add gap features
    features_df = add_gap_features(features_df)
    
    # Add balance/ratio features
    features_df = add_balance_features(features_df)
    
    # Clean up extra columns
    cols_to_drop = [col for col in features_df.columns if col.startswith('home_Season') or 
                    col.startswith('home_Date') or col.startswith('home_Team') or 
                    col.startswith('home_Opponent') or col.startswith('away_Season') or
                    col.startswith('away_Date') or col.startswith('away_Team') or
                    col.startswith('away_Opponent') or col.startswith('home_is_home') or
                    col.startswith('away_is_home')]
    
    features_df = features_df.drop(columns=cols_to_drop, errors='ignore')
    
    # Fill any remaining NaN values with 0.0
    features_df = features_df.fillna(0.0)
    
    print(f"✅ Engineered features for {len(features_df)} new matches")
    return features_df

def update_dataset(existing_df, new_features_df):
    """Update the existing dataset with new matches"""
    print("🔄 Updating dataset...")
    
    # Ensure column alignment
    existing_cols = set(existing_df.columns)
    new_cols = set(new_features_df.columns)
    
    # Add missing columns to new data with default values
    for col in existing_cols - new_cols:
        new_features_df[col] = 0.0
        print(f"⚠️  Added missing column '{col}' with default value 0.0")
    
    # Add missing columns to existing data with default values
    for col in new_cols - existing_cols:
        existing_df[col] = 0.0
        print(f"⚠️  Added missing column '{col}' to existing data with default value 0.0")
    
    # Reorder columns to match
    column_order = list(existing_df.columns)
    new_features_df = new_features_df.reindex(columns=column_order)
    
    # Combine datasets
    updated_df = pd.concat([existing_df, new_features_df], ignore_index=True)
    updated_df = updated_df.sort_values(['Date']).reset_index(drop=True)
    
    return updated_df

def main():
    """Main execution function"""
    print("🚀 Starting Premier League Match Data Update\n")
    
    # Download latest data
    temp_file = download_latest_data()
    
    # Load existing data
    existing_df = load_existing_data()
    print(f"📊 Existing dataset has {len(existing_df)} matches")
    
    # Load market values
    market_df = load_market_values()
    
    # Process new data
    new_df = preprocess_new_data(temp_file)
    
    # Identify new matches
    new_matches = identify_new_matches(new_df, existing_df)
    
    if new_matches is None:
        print("✅ Dataset is already up to date!")
        return
    
    # Engineer features for new matches
    new_features_df = engineer_features_for_new_matches(new_matches, existing_df, market_df)
    
    # Update dataset
    updated_df = update_dataset(existing_df, new_features_df)
    
    # Create backup
    backup_file = f"{EXISTING_DATA_FILE}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    existing_df.to_csv(backup_file, index=False)
    print(f"💾 Backup created: {backup_file}")
    
    # Save updated dataset
    updated_df.to_csv(EXISTING_DATA_FILE, index=False)
    
    print(f"\n✅ Successfully updated dataset!")
    print(f"📈 Added {len(new_features_df)} new matches")
    print(f"📊 Total matches in dataset: {len(updated_df)}")
    print(f"💾 Updated file: {EXISTING_DATA_FILE}")
    
    # Show sample of new matches
    if len(new_features_df) > 0:
        print(f"\n🆕 Sample of new matches:")
        print(new_features_df[['Date', 'HomeTeam', 'AwayTeam', 'FTHG', 'FTAG', 'FTR']].to_string(index=False))

if __name__ == "__main__":
    main()

import pandas as pd

def add_balance_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Adds gap and ratio features for goals scored, goals conceded, and shots.
    These rely on rolling mean stats to normalize per game.
    """

    # Goals For (scored) gap
    if "home_GoalsFor_rolling_mean" in df.columns and "away_GoalsFor_rolling_mean" in df.columns:
        df["goals_for_gap"] = (df["home_GoalsFor_rolling_mean"] - df["away_GoalsFor_rolling_mean"]).abs()

    # Goals Against (conceded) gap
    if "home_GoalsAgainst_rolling_mean" in df.columns and "away_GoalsAgainst_rolling_mean" in df.columns:
        df["conceded_gap"] = (df["home_GoalsAgainst_rolling_mean"] - df["away_GoalsAgainst_rolling_mean"]).abs()

    # Shots ratio (avoid div by zero)
    if "home_Shots_rolling_mean" in df.columns and "away_Shots_rolling_mean" in df.columns:
        df["shots_ratio"] = df["home_Shots_rolling_mean"] / (df["away_Shots_rolling_mean"] + 1e-6)

    # Shots on target ratio
    if "home_ShotsOT_rolling_mean" in df.columns and "away_ShotsOT_rolling_mean" in df.columns:
        df["shots_ot_ratio"] = df["home_ShotsOT_rolling_mean"] / (df["away_ShotsOT_rolling_mean"] + 1e-6)

    # Goals For ratio
    if "home_GoalsFor_rolling_mean" in df.columns and "away_GoalsFor_rolling_mean" in df.columns:
        df["goals_for_ratio"] = df["home_GoalsFor_rolling_mean"] / (df["away_GoalsFor_rolling_mean"] + 1e-6)

    # Goals Against ratio
    if "home_GoalsAgainst_rolling_mean" in df.columns and "away_GoalsAgainst_rolling_mean" in df.columns:
        df["conceded_ratio"] = df["home_GoalsAgainst_rolling_mean"] / (df["away_GoalsAgainst_rolling_mean"] + 1e-6)

    return df


if __name__ == "__main__":
    # Load the latest CSV
    df = pd.read_csv("matches_features_with_gaps.csv")

    # Add new balance features
    df = add_balance_features(df)

    # Save updated file
    df.to_csv("matches_features_with_balance.csv", index=False)

    print("✅ Added balance features (gaps + ratios). Saved to matches_features_with_balance.csv")
    print("New columns added:", [c for c in df.columns if "gap" in c or "ratio" in c])

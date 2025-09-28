import pandas as pd

def main():
    # Load engineered features
    df = pd.read_csv("matches_features.csv")

    # Columns to drop
    drop_cols = [
        "home_Date",
        "away_Date",
        "away_MatchID",
        "home_Team",
        "home_Opponent",
        "away_Team",
        "away_Opponent"
    ]
    df = df.drop(columns=[c for c in drop_cols if c in df.columns], errors="ignore")

    # Rename home_MatchID → MatchID
    if "home_MatchID" in df.columns:
        df = df.rename(columns={"home_MatchID": "MatchID"})

    # Save cleaned file
    df.to_csv("matches_features_clean.csv", index=False)
    print("✅ Saved cleaned file: matches_features_clean.csv")

    # Preview first rows
    print(df.head())

if __name__ == "__main__":
    main()

import pandas as pd

def liverpool_2019(df):
    """Filter Liverpool games in the 2019 season."""
    mask = (df["Season"] == 2019) & (
        (df["HomeTeam"] == "Liverpool") | (df["AwayTeam"] == "Liverpool")
    )
    test_df = df[mask]
    test_df.to_csv("matches_features_liverpool_2019.csv", index=False)
    print(f"✅ Saved {len(test_df)} rows to matches_features_liverpool_2019.csv")
    print(test_df.head())

def liverpool_vs_city(df):
    """Filter all Liverpool vs Man City games across all seasons."""
    mask = (
        ((df["HomeTeam"] == "Liverpool") & (df["AwayTeam"] == "Man City")) |
        ((df["HomeTeam"] == "Man City") & (df["AwayTeam"] == "Liverpool"))
    )
    test_df = df[mask]
    test_df.to_csv("matches_features_liverpool_vs_city.csv", index=False)
    print(f"✅ Saved {len(test_df)} rows to matches_features_liverpool_vs_city.csv")
    print(test_df.head())

def main():
    # Load engineered features
    df = pd.read_csv("matches_features.csv", parse_dates=["Date"])

    # Run tests
    # liverpool_2019(df)
    liverpool_vs_city(df)

if __name__ == "__main__":
    main()

import pandas as pd

def main():
    # Load datasets
    matches = pd.read_csv("matches_features_clean_updated.csv")
    market = pd.read_csv("premier_league_market_values.csv")

    # Standardize column names
    market = market.rename(columns={
        "Year": "Season",
        "Team": "Team",
        "Market Value": "market_value_million"
    })

    # --- Home merge ---
    home = market.rename(columns={
        "Team": "HomeTeam",
        "market_value_million": "home_value"
    })
    matches = matches.merge(
        home[["Season", "HomeTeam", "home_value"]],
        on=["Season", "HomeTeam"],
        how="left"
    )

    # --- Away merge ---
    away = market.rename(columns={
        "Team": "AwayTeam",
        "market_value_million": "away_value"
    })
    matches = matches.merge(
        away[["Season", "AwayTeam", "away_value"]],
        on=["Season", "AwayTeam"],
        how="left"
    )

    # Save enriched dataset
    matches.to_csv("matches_features_with_values.csv", index=False)
    print("✅ Saved matches_features_with_values.csv")
    print(matches[["Season", "HomeTeam", "home_value", "AwayTeam", "away_value"]].head())

if __name__ == "__main__":
    main()

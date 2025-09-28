import pandas as pd
from collections import deque

# Load dataset
df = pd.read_csv("matches_features_final.csv")

# Drop leaking columns
df = df.drop(columns=["home_Points", "away_Points"], errors="ignore")

# Function to assign points from FTR
def get_points(ftr, team_type):
    if team_type == "home":
        return 3 if ftr == "H" else (1 if ftr == "D" else 0)
    else:  # away
        return 3 if ftr == "A" else (1 if ftr == "D" else 0)

df["home_match_points"] = df["FTR"].apply(lambda x: get_points(x, "home"))
df["away_match_points"] = df["FTR"].apply(lambda x: get_points(x, "away"))

# Sort matches chronologically
df = df.sort_values(by=["Season", "Date", "Time"]).reset_index(drop=True)

# Initialize new columns
for col in [
    "home_points_sum", "away_points_sum",
    "home_points_rolling_sum", "away_points_rolling_sum",
    "home_points_rolling_mean", "away_points_rolling_mean",
    "home_points_sum_5", "away_points_sum_5",
    "home_points_mean_5", "away_points_mean_5"
]:
    df[col] = 0.0

# Compute stats per team per season
for season in df["Season"].unique():
    season_df = df[df["Season"] == season]
    teams = pd.concat([season_df["HomeTeam"], season_df["AwayTeam"]]).unique()

    for team in teams:
        team_games = season_df[
            (season_df["HomeTeam"] == team) | (season_df["AwayTeam"] == team)
        ].sort_values(by=["Date", "Time"])

        cum_points = 0
        rolling_points = []
        last5 = deque(maxlen=5)  # adaptive rolling window

        for idx, row in team_games.iterrows():
            # Before this match: record sums/means
            if row["HomeTeam"] == team:
                # season-to-date cumulative
                df.at[idx, "home_points_sum"] = cum_points
                df.at[idx, "home_points_rolling_sum"] = sum(rolling_points)
                df.at[idx, "home_points_rolling_mean"] = (
                    sum(rolling_points) / len(rolling_points) if rolling_points else 0
                )

                # adaptive 5-game rolling
                df.at[idx, "home_points_sum_5"] = sum(last5)
                df.at[idx, "home_points_mean_5"] = (
                    sum(last5) / len(last5) if last5 else 0
                )

                # After match: update
                points = row["home_match_points"]
                rolling_points.append(points)
                cum_points += points
                last5.append(points)

            elif row["AwayTeam"] == team:
                # season-to-date cumulative
                df.at[idx, "away_points_sum"] = cum_points
                df.at[idx, "away_points_rolling_sum"] = sum(rolling_points)
                df.at[idx, "away_points_rolling_mean"] = (
                    sum(rolling_points) / len(rolling_points) if rolling_points else 0
                )

                # adaptive 5-game rolling
                df.at[idx, "away_points_sum_5"] = sum(last5)
                df.at[idx, "away_points_mean_5"] = (
                    sum(last5) / len(last5) if last5 else 0
                )

                # After match: update
                points = row["away_match_points"]
                rolling_points.append(points)
                cum_points += points
                last5.append(points)

# Drop helper columns
df = df.drop(columns=["home_match_points", "away_match_points"])

# Save fixed dataset
df.to_csv("matches_features_final_points_fixed.csv", index=False)

print("✅ Added adaptive rolling 5-game points features (sum & mean).")

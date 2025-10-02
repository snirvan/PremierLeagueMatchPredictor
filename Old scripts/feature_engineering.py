# import pandas as pd
# import numpy as np

# ROLLING_WINDOW = 5

# # -----------------------------
# # Helper: Convert Result to Points
# # -----------------------------
# def compute_points(row):
#     """Return points for home and away teams from match result."""
#     if row["Result"] == 1:      # Home win
#         return 3, 0
#     elif row["Result"] == -1:   # Away win
#         return 0, 3
#     else:                       # Draw
#         return 1, 1

# # -----------------------------
# # Step 1: Expand Matches into Team-Level Rows
# # -----------------------------
# def build_team_match_history(df):
#     """Expand matches into team-centric rows for rolling features."""
#     rows = []
#     for idx, row in df.iterrows():
#         home_points, away_points = compute_points(row)

#         rows.append({
#             "Season": row["Season"],
#             "Date": row["Date"],
#             "MatchID": idx,
#             "Team": row["HomeTeam"],
#             "Opponent": row["AwayTeam"],
#             "is_home": 1,
#             "GoalsFor": row["FTHG"],
#             "GoalsAgainst": row["FTAG"],
#             "Shots": row.get("HS", np.nan),
#             "ShotsOT": row.get("HST", np.nan),
#             "Cards": row.get("HY", 0) + 2 * row.get("HR", 0),
#             "Points": home_points
#         })

#         rows.append({
#             "Season": row["Season"],
#             "Date": row["Date"],
#             "MatchID": idx,
#             "Team": row["AwayTeam"],
#             "Opponent": row["HomeTeam"],
#             "is_home": 0,
#             "GoalsFor": row["FTAG"],
#             "GoalsAgainst": row["FTHG"],
#             "Shots": row.get("AS", np.nan),
#             "ShotsOT": row.get("AST", np.nan),
#             "Cards": row.get("AY", 0) + 2 * row.get("AR", 0),
#             "Points": away_points
#         })
#     return pd.DataFrame(rows)

# # -----------------------------
# # Step 2: Rolling Features (Mean + Sum)
# # -----------------------------
# def compute_rolling_features(team_df):
#     """Compute rolling averages AND sums per team (adaptive window)."""
#     team_df = team_df.sort_values(["Team", "Date"])
#     for col in ["GoalsFor", "GoalsAgainst", "Shots", "ShotsOT", "Cards", "Points"]:
#         team_df[f"{col}_rolling_mean"] = (
#             team_df.groupby("Team")[col]
#             .transform(lambda x: x.shift().rolling(ROLLING_WINDOW, min_periods=1).mean())
#         )
#         team_df[f"{col}_rolling_sum"] = (
#             team_df.groupby("Team")[col]
#             .transform(lambda x: x.shift().rolling(ROLLING_WINDOW, min_periods=1).sum())
#         )
#     return team_df


# # -----------------------------
# # Step 3: Previous Season Points
# # -----------------------------
# def compute_prev_season_points(team_df):
#     """Total points per season → carried into next year as PrevSeasonPoints."""
#     season_points = team_df.groupby(["Season", "Team"])["Points"].sum().reset_index()
#     season_points["PrevSeason"] = season_points["Season"] + 1
#     season_points = season_points.rename(columns={"Points": "PrevSeasonPoints"})
#     return season_points[["PrevSeason", "Team", "PrevSeasonPoints"]]

# # -----------------------------
# # Step 4: Head-to-Head Features
# # -----------------------------
# def compute_h2h_features(df, n=5):
#     """Compute head-to-head points for both home and away teams over last N matches."""
#     h2h_rows = []
#     for i, row in df.iterrows():
#         home, away, match_date = row["HomeTeam"], row["AwayTeam"], row["Date"]

#         past = df[
#             (((df["HomeTeam"] == home) & (df["AwayTeam"] == away)) |
#              ((df["HomeTeam"] == away) & (df["AwayTeam"] == home))) &
#             (df["Date"] < match_date)
#         ].sort_values("Date", ascending=False).head(n)

#         points_home, points_away = 0, 0
#         for _, p in past.iterrows():
#             # Home team perspective
#             if p["HomeTeam"] == home:
#                 points_home += 3 if p["Result"] == 1 else 1 if p["Result"] == 0 else 0
#             else:
#                 points_home += 3 if p["Result"] == -1 else 1 if p["Result"] == 0 else 0

#             # Away team perspective
#             if p["HomeTeam"] == away:
#                 points_away += 3 if p["Result"] == 1 else 1 if p["Result"] == 0 else 0
#             else:
#                 points_away += 3 if p["Result"] == -1 else 1 if p["Result"] == 0 else 0

#         h2h_rows.append({
#             "MatchID": i,
#             "h2h_points_home": points_home,
#             "h2h_points_away": points_away
#         })
#     return pd.DataFrame(h2h_rows)

# # -----------------------------
# # Main Pipeline
# # -----------------------------
# def main():
#     # Load combined matches
#     df = pd.read_csv("matches_all.csv", parse_dates=["Date"])

#     # Team-level history
#     team_df = build_team_match_history(df)

#     # Rolling features
#     team_df = compute_rolling_features(team_df)

#     # Previous season points
#     prev_points = compute_prev_season_points(team_df)
#     team_df = team_df.merge(
#         prev_points, left_on=["Season", "Team"], right_on=["PrevSeason", "Team"], how="left"
#     )
#     team_df = team_df.drop(columns=["PrevSeason"])

#     # Merge back into match-level dataset
#     features = df.copy()
#     features = features.reset_index().rename(columns={"index": "MatchID"})

#     # Home features
#     home_feats = team_df.add_prefix("home_")
#     features = features.merge(
#         home_feats,
#         left_on=["MatchID", "HomeTeam"],
#         right_on=["home_MatchID", "home_Team"],
#         how="left"
#     )

#     # Away features
#     away_feats = team_df.add_prefix("away_")
#     features = features.merge(
#         away_feats,
#         left_on=["MatchID", "AwayTeam"],
#         right_on=["away_MatchID", "away_Team"],
#         how="left"
#     )

#     # Head-to-head features
#     h2h = compute_h2h_features(df)
#     features = features.merge(h2h, on="MatchID", how="left")

#     # Save engineered dataset
#     features.to_csv("matches_features.csv", index=False)
#     print("✅ Saved features to matches_features.csv")

# if __name__ == "__main__":
#     main()








import pandas as pd
import numpy as np

ROLLING_WINDOW = 5

# -----------------------------
# Helper: Convert Result to Points
# -----------------------------
def compute_points(row):
    """Return points for home and away teams from match result."""
    if row["Result"] == 1:      # Home win
        return 3, 0
    elif row["Result"] == -1:   # Away win
        return 0, 3
    else:                       # Draw
        return 1, 1

# -----------------------------
# Step 1: Expand Matches into Team-Level Rows
# -----------------------------
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

# -----------------------------
# Step 2: Rolling Features (Mean + Sum)
# -----------------------------
def compute_rolling_features(team_df):
    """Compute rolling averages AND sums per team (adaptive window)."""
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

# -----------------------------
# Step 3: Previous Season Points
# -----------------------------
def compute_prev_season_points(team_df):
    """Total points per season → carried into next year as PrevSeasonPoints."""
    season_points = team_df.groupby(["Season", "Team"])["Points"].sum().reset_index()
    season_points["PrevSeason"] = season_points["Season"] + 1
    season_points = season_points.rename(columns={"Points": "PrevSeasonPoints"})
    return season_points[["PrevSeason", "Team", "PrevSeasonPoints"]]

# -----------------------------
# Step 4: Head-to-Head Features
# -----------------------------
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

# -----------------------------
# Main Pipeline
# -----------------------------
def main():
    # Load combined matches
    df = pd.read_csv("matches_all.csv", parse_dates=["Date"])

    # Team-level history
    team_df = build_team_match_history(df)

    # Rolling features
    team_df = compute_rolling_features(team_df)

    # Previous season points
    prev_points = compute_prev_season_points(team_df)
    team_df = team_df.merge(
        prev_points, left_on=["Season", "Team"], right_on=["PrevSeason", "Team"], how="left"
    )
    team_df = team_df.drop(columns=["PrevSeason"])

    # Merge back into match-level dataset
    features = df.copy()

    # Home features
    home_feats = team_df.add_prefix("home_")
    features = features.merge(
        home_feats,
        left_on=["Season", "Date", "HomeTeam"],
        right_on=["home_Season", "home_Date", "home_Team"],
        how="left"
    )

    # Away features
    away_feats = team_df.add_prefix("away_")
    features = features.merge(
        away_feats,
        left_on=["Season", "Date", "AwayTeam"],
        right_on=["away_Season", "away_Date", "away_Team"],
        how="left"
    )

    # Head-to-head features
    h2h = compute_h2h_features(df)
    features = features.merge(
        h2h, on=["Season", "Date", "HomeTeam", "AwayTeam"], how="left"
    )

    # Save engineered dataset
    features.to_csv("matches_features.csv", index=False)
    print("✅ Saved features to matches_features.csv")

if __name__ == "__main__":
    main()


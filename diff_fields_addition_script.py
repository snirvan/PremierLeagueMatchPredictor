import pandas as pd

def add_gap_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Adds relative 'gap' features (absolute differences between home and away stats).
    Smaller gaps = higher chance of draws.
    """

    # Market value gap
    if "home_value" in df.columns and "away_value" in df.columns:
        df["value_gap"] = (df["home_value"] - df["away_value"]).abs()

    # Points gap
    if "home_points_sum" in df.columns and "away_points_sum" in df.columns:
        df["points_gap"] = (df["home_points_sum"] - df["away_points_sum"]).abs()

    if "home_points_rolling_mean" in df.columns and "away_points_rolling_mean" in df.columns:
        df["points_gap_rolling"] = (df["home_points_rolling_mean"] - df["away_points_rolling_mean"]).abs()

    # Goal difference gap
    if "home_goal_diff_rolling_sum" in df.columns and "away_goal_diff_rolling_sum" in df.columns:
        df["goal_diff_gap"] = (df["home_goal_diff_rolling_sum"] - df["away_goal_diff_rolling_sum"]).abs()

    # Shots gap
    if "home_Shots_rolling_mean" in df.columns and "away_Shots_rolling_mean" in df.columns:
        df["shots_gap"] = (df["home_Shots_rolling_mean"] - df["away_Shots_rolling_mean"]).abs()

    # Shots on target gap
    if "home_ShotsOT_rolling_mean" in df.columns and "away_ShotsOT_rolling_mean" in df.columns:
        df["shots_ot_gap"] = (df["home_ShotsOT_rolling_mean"] - df["away_ShotsOT_rolling_mean"]).abs()

    # Cards gap
    if "home_Cards_rolling_mean" in df.columns and "away_Cards_rolling_mean" in df.columns:
        df["cards_gap"] = (df["home_Cards_rolling_mean"] - df["away_Cards_rolling_mean"]).abs()

    return df


if __name__ == "__main__":
    # Load your features file
    df = pd.read_csv("matches_features_final_cleaned.csv")

    # Add gap features
    df = add_gap_features(df)

    # Save to a new CSV (so your training script can pick it up)
    df.to_csv("matches_features_with_gaps.csv", index=False)

    print("✅ Gap features added and saved to matches_features_with_gaps.csv")
    print("New columns added:", [c for c in df.columns if "gap" in c])

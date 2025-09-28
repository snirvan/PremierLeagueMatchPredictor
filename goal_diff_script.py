# import pandas as pd

# # Load dataset
# df = pd.read_csv("matches_features_with_values.csv")

# # Home rolling goal differentials
# df["home_goal_diff_rolling_mean"] = (
#     df["home_GoalsFor_rolling_mean"] - df["home_GoalsAgainst_rolling_mean"]
# )
# df["home_goal_diff_rolling_sum"] = (
#     df["home_GoalsFor_rolling_sum"] - df["home_GoalsAgainst_rolling_sum"]
# )

# # Away rolling goal differentials
# df["away_goal_diff_rolling_mean"] = (
#     df["away_GoalsFor_rolling_mean"] - df["away_GoalsAgainst_rolling_mean"]
# )
# df["away_goal_diff_rolling_sum"] = (
#     df["away_GoalsFor_rolling_sum"] - df["away_GoalsAgainst_rolling_sum"]
# )

# # Save updated dataset
# df.to_csv("matches_features_final.csv", index=False)

# print("✅ Added rolling goal differential fields for home and away (mean & sum).")

import pandas as pd

# Load the dataset
df = pd.read_csv("matches_features_final.csv")

# Print all column names
print("Total columns:", len(df.columns))
print("\nColumn names:\n")
for col in df.columns:
    print(col)

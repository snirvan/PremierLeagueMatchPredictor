import pandas as pd

# Load dataset
df = pd.read_csv("matches_features_final_points_fixed.csv")

# Remove redundant rolling sum columns
drop_cols = ["home_points_rolling_sum", "away_points_rolling_sum"]

# Identify betting odds columns
odds_prefixes = ["B365", "BW", "IW", "PS", "WH", "VC", "Max", "Avg", "BF", "1XB", "P", "PC"]
odds_cols = [c for c in df.columns if any(c.startswith(prefix) for prefix in odds_prefixes)]

# Add AHh, AHCh, and Result explicitly
drop_cols.extend(odds_cols)
drop_cols.extend(["AHh", "AHCh", "Result"])

print(f"Removing {len(drop_cols)} columns.")

# Drop them
df = df.drop(columns=drop_cols, errors="ignore")

# Save cleaned dataset
df.to_csv("matches_features_final_clean.csv", index=False)

print("✅ Cleaned dataset saved as matches_features_final_clean.csv")
print(f"Remaining columns: {len(df.columns)}")

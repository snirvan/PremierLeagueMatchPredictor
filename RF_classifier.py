import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report, confusion_matrix
from sklearn.preprocessing import LabelEncoder
from imblearn.over_sampling import RandomOverSampler
import joblib

# ==========================
# Load dataset
# ==========================
# df = pd.read_csv("matches_features_final_cleaned.csv")
# df = pd.read_csv("matches_features_with_gaps.csv")
df = pd.read_csv("matches_features_with_balance.csv")


# ==========================
# Train / Valid / Test Split
# ==========================
train_df = df[df["Season"].between(2019, 2021)]
valid_df = df[df["Season"].between(2022, 2023)]
test_df  = df[df["Season"] == 2024]

print("Train:", train_df.shape, "Valid:", valid_df.shape, "Test:", test_df.shape)

# ==========================
# Features & Target
# ==========================
target_col = "FTR"

# Columns to drop (IDs + leakage + all bookmaker odds)
# ==========================
# Columns to drop
# ==========================

# Comment out drop_cols - using selected features instead
# drop_cols = [
#     # IDs / Metadata
#     "Div", "Date", "Time", "HomeTeam", "AwayTeam", "Referee", "Season",
#
#     # Match outcomes (leakage)
#     "FTHG", "FTAG", "FTR", "HTHG", "HTAG", "HTR", "Result",
#
#     # Raw match stats (leakage if used directly)
#     "HS", "AS", "HST", "AST", "HF", "AF", "HC", "AC", "HY", "AY", "HR", "AR",
#
#     # Redundant engineered fields
#     "home_points_rolling_sum", "away_points_rolling_sum",
#     "home_points_sum_5", "away_points_sum_5", "home_points_mean_5", "away_points_mean_5",
#
#     #Droping Sums
#     "home_Shots_rolling_sum","away_Shots_rolling_sum", "home_ShotsOT_rolling_sum", "away_ShotsOT_rolling_sum", "away_ShotsOT_rolling_sum",
#     "home_Cards_rolling_sum","away_Cards_rolling_sum", "home_points_rolling_sum", "away_points_rolling_sum", "home_goal_diff_rolling_sum","away_goal_diff_rolling_sum",
#
#     #Droping Cards
#     "home_Cards", "away_Cards",
#     "home_Cards_rolling_mean", "away_Cards_rolling_mean",
#     "home_Cards_rolling_sum", "away_Cards_rolling_sum",
#     "cards_gap"
#
#     ## Overpowered inequality inducing features
#     # "home_value", "away_value"
# ]

# Selected features approach - only use features we want
selected_features = [
    # Rolling goals
    "home_GoalsFor_rolling_mean", "home_GoalsFor_rolling_sum",
    "home_GoalsAgainst_rolling_mean", "home_GoalsAgainst_rolling_sum",
    "away_GoalsFor_rolling_mean", "away_GoalsFor_rolling_sum",
    "away_GoalsAgainst_rolling_mean", "away_GoalsAgainst_rolling_sum",

    # Rolling shots (means only)
    "home_Shots_rolling_mean",
    "away_Shots_rolling_mean",

    # Rolling shots on target (means only)
    "home_ShotsOT_rolling_mean",
    "away_ShotsOT_rolling_mean",

    # Rolling points (season-to-date averages)
    "home_Points_rolling_mean", "away_Points_rolling_mean",

    # Prev season baseline
    "home_PrevSeasonPoints", "away_PrevSeasonPoints",

    # Head-to-head
    "h2h_points_home", "h2h_points_away",

    # Market values (include unless you decide to drop them)
    "home_value", "away_value",

    # Rolling goal differentials (means only)
    "home_goal_diff_rolling_mean",
    "away_goal_diff_rolling_mean",

    # Fixed points totals
    "home_points_sum", "away_points_sum"
]


# Drop bookmaker odds (anything with typical bookmaker prefixes)
# odds_prefixes = ["B365", "BW", "IW", "PS", "WH", "VC", "Max", "Avg", "BF", "1XB", "P", "PC"]
# odds_cols = [c for c in df.columns if any(c.startswith(prefix) for prefix in odds_prefixes)]
# drop_cols.extend(odds_cols)

print(f"Using {len(selected_features)} selected features.")

def prepare_xy(df):
    # Use only selected features
    X = df[selected_features].fillna(0)
    y = df[target_col]
    return X, y

X_train, y_train = prepare_xy(train_df)
X_valid, y_valid = prepare_xy(valid_df)
X_test, y_test   = prepare_xy(test_df)

# Encode target labels
le = LabelEncoder()
y_train_enc = le.fit_transform(y_train)
y_valid_enc = le.transform(y_valid)
y_test_enc  = le.transform(y_test)

print("Class distribution before oversampling:", pd.Series(y_train_enc).value_counts().to_dict())

# ==========================
# Apply Oversampling
# ==========================
# Apply oversampling only to training set
ros = RandomOverSampler(random_state=42)
X_train_resampled, y_train_resampled = ros.fit_resample(X_train, y_train_enc)

print("✅ Applied RandomOverSampler")
print("Class distribution after oversampling:", pd.Series(y_train_resampled).value_counts().to_dict())

# ==========================
# Random Forest Classifier
# ==========================
rf = RandomForestClassifier(
    n_estimators=300,
    max_depth=20,
    random_state=42
    # class_weight="balanced"
)

rf.fit(X_train_resampled, y_train_resampled)

# ==========================
# Validation Results
# ==========================
y_valid_pred = rf.predict(X_valid)
print("\n--- Validation Results (2022–23) ---")
print(confusion_matrix(y_valid_enc, y_valid_pred))
print(classification_report(y_valid_enc, y_valid_pred, target_names=le.classes_))

# ==========================
# Test Results
# ==========================
y_test_pred = rf.predict(X_test)
print("\n--- Test Results (2024) ---")
print(confusion_matrix(y_test_enc, y_test_pred))
print(classification_report(y_test_enc, y_test_pred, target_names=le.classes_))

# ==========================
# Feature Importances
# ==========================
import matplotlib.pyplot as plt

importances = rf.feature_importances_
feature_names = X_train_resampled.columns

# Sort by importance
indices = importances.argsort()[::-1]
top_n = 20  # number of top features to plot

plt.figure(figsize=(10, 6))
plt.barh(range(top_n), importances[indices[:top_n]][::-1], align="center")
plt.yticks(range(top_n), [feature_names[i] for i in indices[:top_n]][::-1])
plt.xlabel("Feature Importance")
plt.title("Top 20 Important Features in Random Forest")
plt.tight_layout()
plt.show()

# ==========================
# Save the trained model
# ==========================
print("\n--- Saving Model ---")
joblib.dump(rf, "rf_model.pkl")
joblib.dump(le, "label_encoder.pkl")
print("✅ Model saved as 'rf_model.pkl'")
print("✅ Label encoder saved as 'label_encoder.pkl'")

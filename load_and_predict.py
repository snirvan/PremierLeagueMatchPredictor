import joblib
import pandas as pd
from sklearn.metrics import classification_report, confusion_matrix

# ==========================
# Load trained model and label encoder
# ==========================
print("Loading saved model...")
rf = joblib.load("rf_model.pkl")
le = joblib.load("label_encoder.pkl")
print("✅ Model and label encoder loaded successfully")

# ==========================
# Load and prepare data for prediction
# ==========================
# Load the same dataset (you can replace this with new data)
df = pd.read_csv("matches_features_with_balance.csv")

# Use the same preprocessing as in training
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

def prepare_features(df):
    """Prepare features for prediction (same as training)"""
    # Use only selected features
    X = df[selected_features].fillna(0)
    return X

# ==========================
# Example: Predict on 2024 data
# ==========================
test_df = df[df["Season"] == 2024]
X_test = prepare_features(test_df)
y_test = test_df["FTR"]

# Make predictions
print(f"\nMaking predictions on {len(X_test)} matches from 2024...")
y_pred = rf.predict(X_test)
y_pred_proba = rf.predict_proba(X_test)

# Convert predictions back to original labels
y_pred_labels = le.inverse_transform(y_pred)
y_test_enc = le.transform(y_test)

# ==========================
# Evaluation
# ==========================
print("\n--- Prediction Results ---")
print("Confusion Matrix:")
print(confusion_matrix(y_test_enc, y_pred))
print("\nClassification Report:")
print(classification_report(y_test_enc, y_pred, target_names=le.classes_))

# ==========================
# Example: Predict on a single match
# ==========================
print("\n--- Single Match Prediction Example ---")
if len(X_test) > 0:
    # Take the first match as an example
    sample_match = X_test.iloc[0:1]
    sample_actual = y_test.iloc[0]
    
    prediction = rf.predict(sample_match)[0]
    prediction_proba = rf.predict_proba(sample_match)[0]
    prediction_label = le.inverse_transform([prediction])[0]
    
    print(f"Actual result: {sample_actual}")
    print(f"Predicted result: {prediction_label}")
    print(f"Prediction probabilities:")
    for i, class_label in enumerate(le.classes_):
        print(f"  {class_label}: {prediction_proba[i]:.3f}")

# ==========================
# Feature importance (from loaded model)
# ==========================
print(f"\n--- Model Info ---")
print(f"Model type: {type(rf).__name__}")
print(f"Number of features: {len(X_test.columns)}")
print(f"Classes: {list(le.classes_)}")
print(f"Number of estimators: {rf.n_estimators}")

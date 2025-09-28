from flask import Flask, jsonify, request
from flask_cors import CORS
import pandas as pd
import joblib
import os
import sys

# Add parent directory to path to import our modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

app = Flask(__name__)
CORS(app)  # Enable CORS for frontend

# Global variables to store loaded model and data
rf_model = None
label_encoder = None
df = None

def load_model_and_data():
    """Load the trained model, label encoder, and dataset"""
    global rf_model, label_encoder, df
    
    try:
        # Load model and encoder from parent directory
        parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        
        rf_model = joblib.load(os.path.join(parent_dir, "rf_model.pkl"))
        label_encoder = joblib.load(os.path.join(parent_dir, "label_encoder.pkl"))
        df = pd.read_csv(os.path.join(parent_dir, "matches_features_with_balance.csv"))
        
        print("✅ Model, encoder, and data loaded successfully")
        print(f"Available seasons: {sorted(df['Season'].unique())}")
        print(f"Total matches: {len(df)}")
        
    except Exception as e:
        print(f"❌ Error loading model or data: {e}")
        raise e

def prepare_features(match_df):
    """Prepare features for prediction (same as training)"""
    # Use selected features approach (same as RF_classifier.py)
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
    
    # Use only selected features
    X = match_df[selected_features].fillna(0)
    return X

@app.route('/api/seasons', methods=['GET'])
def get_seasons():
    """Get list of available seasons (filtered to 2023, 2024, 2025)"""
    try:
        # Filter to only show the specific seasons we want
        available_seasons = sorted(df['Season'].unique().tolist())
        target_seasons = [2023, 2024, 2025]
        filtered_seasons = [s for s in target_seasons if s in available_seasons]
        
        return jsonify({
            "success": True,
            "seasons": filtered_seasons
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/api/matches/<int:season>', methods=['GET'])
def get_matches_by_season(season):
    """Get all matches for a specific season with predictions"""
    try:
        # Filter matches by season
        season_df = df[df['Season'] == season].copy()
        
        if len(season_df) == 0:
            return jsonify({
                "success": False,
                "error": f"No matches found for season {season}"
            }), 404
        
        # Prepare features for prediction
        X = prepare_features(season_df)
        
        # Make predictions
        predictions = rf_model.predict(X)
        prediction_probabilities = rf_model.predict_proba(X)
        
        # Convert predictions back to labels
        predicted_labels = label_encoder.inverse_transform(predictions)
        
        # Prepare response data
        matches = []
        for idx, (_, row) in enumerate(season_df.iterrows()):
            # Handle cases where FTR might be empty (for future matches)
            actual_result = row.get('FTR', '')
            if pd.isna(actual_result) or actual_result == '':
                actual_result = None
            
            match_data = {
                "id": idx,
                "date": row['Date'],
                "time": row.get('Time', ''),
                "homeTeam": row['HomeTeam'],
                "awayTeam": row['AwayTeam'],
                "actualResult": actual_result,
                "predictedResult": predicted_labels[idx],
                "homeGoals": int(row['FTHG']) if pd.notna(row['FTHG']) else None,
                "awayGoals": int(row['FTAG']) if pd.notna(row['FTAG']) else None,
                "confidence": {
                    "H": float(prediction_probabilities[idx][label_encoder.transform(['H'])[0]]),
                    "D": float(prediction_probabilities[idx][label_encoder.transform(['D'])[0]]),
                    "A": float(prediction_probabilities[idx][label_encoder.transform(['A'])[0]])
                }
            }
            matches.append(match_data)
        
        return jsonify({
            "success": True,
            "season": season,
            "totalMatches": len(matches),
            "matches": matches
        })
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/api/accuracy/<int:season>', methods=['GET'])
def get_season_accuracy(season):
    """Get prediction accuracy for a specific season"""
    try:
        # Filter matches by season
        season_df = df[df['Season'] == season].copy()
        
        if len(season_df) == 0:
            return jsonify({
                "success": False,
                "error": f"No matches found for season {season}"
            }), 404
        
        # Prepare features and make predictions
        X = prepare_features(season_df)
        predictions = rf_model.predict(X)
        predicted_labels = label_encoder.inverse_transform(predictions)
        
        # Calculate accuracy
        actual_results = season_df['FTR'].values
        correct_predictions = sum(pred == actual for pred, actual in zip(predicted_labels, actual_results))
        accuracy = correct_predictions / len(predicted_labels)
        
        # Calculate accuracy by result type
        result_accuracy = {}
        for result_type in ['H', 'D', 'A']:
            mask = actual_results == result_type
            if mask.sum() > 0:
                correct = sum((predicted_labels[mask] == actual_results[mask]))
                result_accuracy[result_type] = correct / mask.sum()
            else:
                result_accuracy[result_type] = 0.0
        
        return jsonify({
            "success": True,
            "season": season,
            "overallAccuracy": accuracy,
            "accuracyByResult": result_accuracy,
            "totalMatches": len(predicted_labels),
            "correctPredictions": correct_predictions
        })
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        "success": True,
        "message": "Premier League Predictor API is running",
        "modelLoaded": rf_model is not None,
        "dataLoaded": df is not None
    })

if __name__ == '__main__':
    # Load model and data on startup
    load_model_and_data()
    
    # Run the Flask app
    app.run(debug=True, host='0.0.0.0', port=5001)

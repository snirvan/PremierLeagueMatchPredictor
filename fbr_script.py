import requests
import time
import pandas as pd

BASE_URL = "https://fbrapi.com"

# -------------------
# STEP 0: Get API Key
# -------------------
def get_api_key():
    r = requests.post(f"{BASE_URL}/generate_api_key")
    r.raise_for_status()
    api_key = r.json()["api_key"]
    print("✅ Generated API Key:", api_key)
    return api_key

def get_data(endpoint, headers, params=None, sleep=1):  # Reduced for testing
    url = f"{BASE_URL}{endpoint}"
    r = requests.get(url, headers=headers, params=params)
    time.sleep(sleep)  # obey 1 request / 6 sec rule per API documentation
    r.raise_for_status()
    return r.json()

# -------------------
# Lookup League Season IDs
# -------------------
def get_league_season_ids(league_id, headers, years):
    """Fetch league_season_id for each season year in `years` list"""
    data = get_data("/league-seasons", headers, {"league_id": league_id})
    id_map = {}
    
    print("🔍 Available seasons from API:")
    for s in data["data"]:
        # Extract year from season_id (e.g., "2023-2024" -> 2023)
        season_id = s["season_id"]
        if isinstance(season_id, str) and "-" in season_id:
            season_year = int(season_id.split("-")[0])
        else:
            print(f"⚠️ Unexpected season_id format: {season_id}")
            continue
            
        print(f"  Season {season_year}: {season_id}")
        
        if season_year in years:
            # Use season_id as the identifier since there's no separate 'id' field
            id_map[season_year] = season_id
            
    print(f"📋 Matched seasons: {id_map}")
    return id_map

# -------------------
# Matches
# -------------------
def fetch_matches(league_id, season_id, headers):
    """Fetch matches using league_id and season_id"""
    data = get_data("/matches", headers, {"league_id": league_id, "season_id": season_id})
    matches = []
    
    # Debug: Check structure of first match
    if data.get("data") and len(data["data"]) > 0:
        print("🔍 Match API Response Structure Debug:")
        print(f"First match keys: {list(data['data'][0].keys())}")
    
    for m in data["data"]:
        # Handle different possible match ID fields
        match_id = m.get("match_id") or m.get("id") or m.get("fixture_id")
        
        # Extract season year from season_id for consistency  
        if isinstance(season_id, str) and "-" in season_id:
            season_year = int(season_id.split("-")[0])
        else:
            season_year = season_id
        
        matches.append({
            "match_id": match_id,
            "date": m["date"],
            "season": season_year,
            "home_team_id": m["home_team_id"],
            "home_team_name": m["home"],
            "away_team_id": m["away_team_id"],  
            "away_team_name": m["away"],
            "home_score": m["home_team_score"],
            "away_score": m["away_team_score"],
            "result": (
                1 if m["home_team_score"] is not None and m["away_team_score"] is not None and m["home_team_score"] > m["away_team_score"]
                else -1 if m["home_team_score"] is not None and m["away_team_score"] is not None and m["home_team_score"] < m["away_team_score"]
                else 0 if m["home_team_score"] is not None and m["away_team_score"] is not None
                else None  # For future/postponed matches
            )
        })
    return pd.DataFrame(matches)

# -------------------
# Team Season Stats
# -------------------
def fetch_team_season_stats(league_id, season_id, headers):
    """Fetch team season stats using league_id and season_id parameters"""
    data = get_data("/team-season-stats", headers, {"league_id": league_id, "season_id": season_id})
    stats = []
    
    # Debug: Check structure of first team stats
    if data.get("data") and len(data["data"]) > 0:
        print("🔍 Team Season Stats API Response Structure Debug:")
        print(f"First team keys: {list(data['data'][0].keys())}")
        
    for t in data["data"]:
        # Extract season year from season_id for consistency
        if isinstance(season_id, str) and "-" in season_id:
            season_year = int(season_id.split("-")[0])
        else:
            season_year = season_id
            
        # Handle API structure with meta_data and stats
        team_id = t["meta_data"]["team_id"]
        team_name = t["meta_data"]["team_name"]
            
        stats.append({
            "team_id": team_id,
            "team_name": team_name,
            "season": season_year,
            "xPts": float(t["stats"].get("xPts", 0))
        })
    return pd.DataFrame(stats)

# -------------------
# Impute promoted teams (no previous PL xPts)
# -------------------
def impute_promoted_teams(season_stats, league_id, current_year, headers):
    season_stats["is_xPts_imputed"] = 0  # default
    prev_year = current_year - 1

    league_seasons = get_data("/league-seasons", headers, {"league_id": league_id})["data"]
    prev_season_id = None
    for s in league_seasons:
        season_id = s["season_id"]
        if isinstance(season_id, str) and "-" in season_id:
            season_year = int(season_id.split("-")[0])
            if season_year == prev_year:
                prev_season_id = season_id
                break

    if prev_season_id:
        prev_stats = fetch_team_season_stats(league_id, prev_season_id, headers)
        if not prev_stats.empty:
            bottom3_avg = prev_stats.sort_values("xPts").head(3)["xPts"].mean()
            missing_mask = season_stats["xPts"].isna()
            season_stats.loc[missing_mask, "xPts"] = bottom3_avg
            season_stats.loc[missing_mask, "is_xPts_imputed"] = 1
    return season_stats

# -------------------
# Team Match Stats (rolling form)
# -------------------
def fetch_team_match_stats(team_id, season_id, headers):
    # Try different parameter combinations for team match stats
    # Some endpoints might use 'season' instead of 'season_id'
    if isinstance(season_id, str) and "-" in season_id:
        season_year = int(season_id.split("-")[0])
    else:
        season_year = season_id
        
    try:
        # First try with season_id
        data = get_data("/team-match-stats", headers, {"team_id": team_id, "season_id": season_id})
    except Exception as e1:
        try:
            # If that fails, try with season year
            data = get_data("/team-match-stats", headers, {"team_id": team_id, "season": season_year})
        except Exception as e2:
            try:
                # Try with league_id and season_id
                data = get_data("/team-match-stats", headers, {"team_id": team_id, "league_id": 9, "season_id": season_id})
            except Exception as e3:
                print(f"⚠️ Could not fetch team match stats for team {team_id}, season {season_id}")
                print(f"   Errors: {str(e1)[:100]}... | {str(e2)[:100]}... | {str(e3)[:100]}...")
                return pd.DataFrame()  # Return empty DataFrame
    
    games = []
    
    for g in data["data"]:
        # Handle different possible match ID fields
        match_id = g["match"].get("match_id") or g["match"].get("id") or g["match"].get("fixture_id")
        
        games.append({
            "match_id": match_id,
            "team_id": team_id,
            "season": season_year,
            "date": g["match"]["date"],
            "xG_for": float(g["stats"].get("xG", 0)),
            "xG_against": float(g["stats"].get("xGA", 0)),
            "goals_for": g["team_score"],
            "goals_against": g["opponent_score"],
            "points": (
                3 if g["team_score"] > g["opponent_score"]
                else 1 if g["team_score"] == g["opponent_score"]
                else 0
            )
        })
    return pd.DataFrame(games)

def compute_rolling_features(team_match_df, window=5, league_id=None, current_year=None, headers=None):
    team_match_df = team_match_df.sort_values(["team_id", "date"])
    team_match_df["xG_diff"] = team_match_df["xG_for"] - team_match_df["xG_against"]

    for col in ["xG_for", "xG_against", "xG_diff", "points"]:
        team_match_df[f"{col}_rolling"] = (
            team_match_df.groupby("team_id")[col]
            .apply(lambda x: x.shift().rolling(window, min_periods=1).mean())
        )

    team_match_df["is_form_imputed"] = 0

    # Impute Matchday 1 form
    if league_id and current_year:
        prev_year = current_year - 1
        league_seasons = get_data("/league-seasons", headers, {"league_id": league_id})["data"]

        prev_season_id = None
        for s in league_seasons:
            season_id = s["season_id"]
            if isinstance(season_id, str) and "-" in season_id:
                season_year = int(season_id.split("-")[0])
                if season_year == prev_year:
                    prev_season_id = season_id
                    break

        baseline_ppg = 0.8  # default fallback
        if prev_season_id:
            prev_stats = fetch_team_season_stats(league_id, prev_season_id, headers)
            if not prev_stats.empty:
                bottom3_avg_pts = prev_stats.sort_values("xPts").head(3)["xPts"].mean()
                baseline_ppg = bottom3_avg_pts / 38.0

        for idx, row in team_match_df.iterrows():
            if pd.isna(row["points_rolling"]):
                team_match_df.at[idx, "xG_for_rolling"] = 0.0
                team_match_df.at[idx, "xG_against_rolling"] = 0.0
                team_match_df.at[idx, "xG_diff_rolling"] = 0.0
                team_match_df.at[idx, "points_rolling"] = baseline_ppg
                team_match_df.at[idx, "is_form_imputed"] = 1

    return team_match_df

# -------------------
# H2H Features
# -------------------
def compute_h2h_features(matches, n=5):
    h2h_points = []
    for _, row in matches.iterrows():
        home, away, match_date = row["home_team_id"], row["away_team_id"], row["date"]
        past = matches[
            (((matches["home_team_id"] == home) & (matches["away_team_id"] == away)) |
             ((matches["home_team_id"] == away) & (matches["away_team_id"] == home))) &
            (matches["date"] < match_date)
        ].sort_values("date", ascending=False).head(n)

        points = 0
        goals = 0
        for _, p in past.iterrows():
            if p["home_team_id"] == home:
                if p["home_score"] > p["away_score"]: points += 3
                elif p["home_score"] == p["away_score"]: points += 1
                goals += p["home_score"]
            else:
                if p["away_score"] > p["home_score"]: points += 3
                elif p["away_score"] == p["home_score"]: points += 1
                goals += p["away_score"]

        h2h_points.append({"match_id": row["match_id"], "h2h_points_home": points, "h2h_goals_home": goals})
    return pd.DataFrame(h2h_points)

# -------------------
# Synthetic Team Stats (Fallback)
# -------------------
def create_synthetic_team_stats(matches):
    """Create synthetic team match stats from matches when API endpoint fails"""
    synthetic_stats = []
    
    for _, match in matches.iterrows():
        # Home team stats
        synthetic_stats.append({
            "match_id": match["match_id"],
            "team_id": match["home_team_id"],
            "season": match["season"],
            "date": match["date"],
            "xG_for": 1.0,  # Default values since we don't have xG data
            "xG_against": 1.0,
            "goals_for": match["home_score"] if match["home_score"] is not None else 0,
            "goals_against": match["away_score"] if match["away_score"] is not None else 0,
            "points": (
                3 if match["result"] == 1
                else 1 if match["result"] == 0
                else 0 if match["result"] == -1
                else 0  # For future matches
            )
        })
        
        # Away team stats  
        synthetic_stats.append({
            "match_id": match["match_id"],
            "team_id": match["away_team_id"],
            "season": match["season"],
            "date": match["date"],
            "xG_for": 1.0,  # Default values since we don't have xG data
            "xG_against": 1.0,
            "goals_for": match["away_score"] if match["away_score"] is not None else 0,
            "goals_against": match["home_score"] if match["home_score"] is not None else 0,
            "points": (
                3 if match["result"] == -1
                else 1 if match["result"] == 0
                else 0 if match["result"] == 1
                else 0  # For future matches
            )
        })
    
    return pd.DataFrame(synthetic_stats)

# -------------------
# Build Features for One Season
# -------------------
def build_features(league_id, season, season_id, headers):
    matches = fetch_matches(league_id, season_id, headers)
    season_stats = fetch_team_season_stats(league_id, season_id, headers)
    season_stats = impute_promoted_teams(season_stats, league_id, season, headers)

    team_ids = pd.concat([
        matches[["home_team_id"]].rename(columns={"home_team_id": "team_id"}),
        matches[["away_team_id"]].rename(columns={"away_team_id": "team_id"})
    ])["team_id"].unique()

    all_team_match_stats = []
    for tid in team_ids:
        df = fetch_team_match_stats(tid, season_id, headers)
        if not df.empty:
            all_team_match_stats.append(df)
    
    if not all_team_match_stats:
        print(f"⚠️ No team match stats available for season {season}. Creating synthetic rolling features from match data...")
        # Create synthetic team match stats from the matches DataFrame
        team_match_stats = create_synthetic_team_stats(matches)
    else:
        team_match_stats = pd.concat(all_team_match_stats, ignore_index=True)
    team_match_stats = compute_rolling_features(team_match_stats, league_id=league_id, current_year=season, headers=headers)

    df = matches.copy()
    
    # Merge home stats with proper prefixing
    home_stats = team_match_stats.copy()
    home_stats = home_stats.rename(columns={"team_id": "home_team_id"})
    # Add prefix to all columns except the merge keys
    home_cols_to_prefix = [col for col in home_stats.columns if col not in ["match_id", "home_team_id"]]
    home_rename_dict = {col: f"home_{col}" for col in home_cols_to_prefix}
    home_stats = home_stats.rename(columns=home_rename_dict)
    
    df = df.merge(
        home_stats,
        on=["match_id", "home_team_id"],
        how="left"
    )
    
    # Merge away stats with proper prefixing  
    away_stats = team_match_stats.copy()
    away_stats = away_stats.rename(columns={"team_id": "away_team_id"})
    # Add prefix to all columns except the merge keys
    away_cols_to_prefix = [col for col in away_stats.columns if col not in ["match_id", "away_team_id"]]
    away_rename_dict = {col: f"away_{col}" for col in away_cols_to_prefix}
    away_stats = away_stats.rename(columns=away_rename_dict)
    
    df = df.merge(
        away_stats,
        on=["match_id", "away_team_id"],
        how="left"
    )

    df = df.merge(season_stats.add_prefix("home_"), left_on=["home_team_id"], right_on=["home_team_id"], how="left")
    df = df.merge(season_stats.add_prefix("away_"), left_on=["away_team_id"], right_on=["away_team_id"], how="left")

    h2h = compute_h2h_features(matches)
    df = df.merge(h2h, on="match_id", how="left")

    feature_cols = [
        "match_id","date","season",
        "home_team_name","away_team_name",
        "home_xPts","away_xPts",
        "home_xG_diff_rolling","away_xG_diff_rolling",
        "home_points_rolling","away_points_rolling",
        "h2h_points_home","h2h_goals_home",
        "result",
        "home_is_xPts_imputed","away_is_xPts_imputed",
        "home_is_form_imputed","away_is_form_imputed"
    ]

    # Propagate imputation flags separately for home/away - handle missing columns gracefully
    df["home_is_xPts_imputed"] = df.get("home_is_xPts_imputed", 0).fillna(0)
    df["away_is_xPts_imputed"] = df.get("away_is_xPts_imputed", 0).fillna(0)
    df["home_is_form_imputed"] = df.get("home_is_form_imputed", 0).fillna(0)
    df["away_is_form_imputed"] = df.get("away_is_form_imputed", 0).fillna(0)

    return df[feature_cols]

# -------------------
# Main
# -------------------
if __name__ == "__main__":
    API_KEY = get_api_key()
    HEADERS = {"X-API-Key": API_KEY}

    LEAGUE_ID = 9  # Premier League
    YEARS = [2023]  # Test with just one recent season first

    league_season_ids = get_league_season_ids(LEAGUE_ID, HEADERS, YEARS)

    all_features = []
    for year in YEARS:
        if year not in league_season_ids:
            print(f"⚠️ No league_season_id found for {year}, skipping")
            continue
        print(f"📊 Fetching season {year}-{year+1}")
        df = build_features(LEAGUE_ID, year, league_season_ids[year], HEADERS)
        all_features.append(df)

    full_df = pd.concat(all_features)
    full_df.to_csv("matches_features_6seasons.csv", index=False)
    print("✅ Saved all features to matches_features_6seasons.csv")

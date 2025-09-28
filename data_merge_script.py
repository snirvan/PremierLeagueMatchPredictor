import pandas as pd
import glob
import os

def load_and_clean_csv(file, season_year):
    df = pd.read_csv(file)

    # Ensure Date is datetime
    df["Date"] = pd.to_datetime(df["Date"], dayfirst=True, errors="coerce")

    # Add season label (e.g. 2019 means 2019–20 season)
    df["Season"] = season_year

    # Normalize result to numeric: H=1, D=0, A=-1
    result_map = {"H": 1, "D": 0, "A": -1}
    if "FTR" in df.columns:
        df["Result"] = df["FTR"].map(result_map)
    elif "Res" in df.columns:
        df["Result"] = df["Res"].map(result_map)

    return df

if __name__ == "__main__":
    folder = "data"
    season_map = {
        "PL_19.csv": 2019,
        "PL_20.csv": 2020,
        "PL_21.csv": 2021,
        "PL_22.csv": 2022,
        "PL_23.csv": 2023,
        "PL_24.csv": 2024,
    }

    all_dfs = []
    for fname, year in season_map.items():
        path = os.path.join(folder, fname)
        if os.path.exists(path):
            print(f"📂 Loading {fname}")
            df = load_and_clean_csv(path, year)
            all_dfs.append(df)
        else:
            print(f"⚠️ File missing: {path}")

    full_df = pd.concat(all_dfs, ignore_index=True)

    print("✅ Combined shape:", full_df.shape)
    print("✅ Columns:", full_df.columns.tolist())

    # Save combined dataset
    full_df.to_csv("matches_all.csv", index=False)
    print("💾 Saved to matches_all.csv")

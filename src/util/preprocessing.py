import pandas as pd
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
RAW_CSV = "data/raw/results_raw.csv"
OUT_FULL = "data/processed/results_full.csv"
OUT_10Y = "data/processed/results_last_10yrs.csv"
OUT_5Y = "data/processed/results_last_5yrs.csv"

CUTOFF_10Y = "2016-06-01"
CUTOFF_5Y = "2021-06-01"

def load_and_validate(path: str) -> pd.DataFrame:
    path = os.path.join(BASE_DIR, path)
    df = pd.read_csv(path)
    required = ["date","home_team","away_team","home_score","away_score",
                "tournament","city","country","neutral"]
    for c in required:
        if c not in df.columns:
            raise ValueError(f"Missing required column: {c}")
    return df

def clean_and_validate(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    # parse date
    df["date"] = pd.to_datetime(df["date"], format="%Y-%m-%d", errors="coerce")
    df = df.dropna(subset=["date"])

    # convert scores to int
    df["home_score"] = pd.to_numeric(df["home_score"], errors="coerce")
    df["away_score"] = pd.to_numeric(df["away_score"], errors="coerce")
    df = df.dropna(subset=["home_score","away_score"])
    df["home_score"] = df["home_score"].astype(int)
    df["away_score"] = df["away_score"].astype(int)

    def get_result(row):
        if row.home_score > row.away_score:
            return "home_win"
        elif row.home_score < row.away_score:
            return "away_win"
        else:
            return "draw"

    df["result"] = df.apply(get_result, axis=1)

    # strip whitespace from team names
    df["home_team"] = df["home_team"].str.strip()
    df["away_team"] = df["away_team"].str.strip()

    # lowercase everything
    for col in ["home_team", "away_team", "result", "tournament", "city", "country"]:
        df[col] = df[col].str.strip().str.lower()

    # validate home advantage: if neutral==False, home_team should equal country
    # note: there are exceptions to this due to historic events or countries that aren't formally recognized. a few examples:
    # 21624 1997-01-12  DR Congo    Congo       Zaïre       -->
    # 26739 2002-10-16  Serbia      Finland     Yugoslavia  --> NEUTRAL == FALSE, but HOME_TEAM != COUNTRY
    # 42352 2019-03-25  Catalonia   Venezuela   Spain       -->
    invalid_adv = df[(df["neutral"] == False) & (df["home_team"] != df["country"])]
    if len(invalid_adv) > 0:
        print(f"Warning: {len(invalid_adv)} rows state home advantage but country != home_team:")
        print(invalid_adv[["date","home_team","away_team","country"]])


    column_order = [
            "date", "home_team", "away_team",
             "result", "home_score", "away_score", 
            "tournament", "city", "country", "neutral"
        ]

    df = df[column_order]
    df = df.drop_duplicates().reset_index(drop=True)
    return df

def filter_by_cutoff(df: pd.DataFrame, cutoff_date: str) -> pd.DataFrame:
    cutoff = pd.to_datetime(cutoff_date)
    return df[df["date"] >= cutoff].reset_index(drop=True)

def main():
    df_raw = load_and_validate(RAW_CSV)
    df_clean = clean_and_validate(df_raw)

    # full
    df_clean.to_csv(os.path.join(BASE_DIR, OUT_FULL), index=False)

    # last 10 years
    df_10y = filter_by_cutoff(df_clean, CUTOFF_10Y)
    df_10y.to_csv(os.path.join(BASE_DIR,OUT_10Y), index=False)

    # last 5 years
    df_5y = filter_by_cutoff(df_clean, CUTOFF_5Y)
    df_5y.to_csv(os.path.join(BASE_DIR,OUT_5Y), index=False)

    print(f"Saved cleaned datasets: full={len(df_clean)}, 10yr={len(df_10y)}, 5yr={len(df_5y)} rows")

if __name__ == "__main__":
    main()

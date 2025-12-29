import numpy as np
import pandas as pd
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
RESULTS_FULL_CSV = "data/processed/results_full.csv"
RESULTS_10Y_CSV = "data/processed/results_last_10yrs.csv"
RESULTS_5Y_CSV = "data/processed/results_last_5yrs.csv"

ACTIVE_CSV = RESULTS_5Y_CSV

MIN_MATCHES = 20
SHRINK_K = 25
DECAY_LAMBDA = 0.001

# ============================================================
# 1. DATASET OVERVIEW
# ============================================================
def dataset_overview(df):
    print("\n=== DATASET OVERVIEW ===")
    print(f"Total matches: {len(df)}")
    print(f"First match:   {df['date'].min()}")
    print(f"Last match:    {df['date'].max()}")
    print(f"Unique teams:  {df['home_team'].nunique()}")
    print(f"Tournaments:   {df['tournament'].nunique()}")


# ============================================================
# 2. TOURNAMENT-LEVEL GOAL ENVIRONMENT
# ============================================================
def tournament_environment(df):
    print("\n=== TOURNAMENT GOAL ENVIRONMENTS ===")

    # compute groupby for home and away goals
    home_avg = df.groupby("tournament")["home_score"].mean()
    away_avg = df.groupby("tournament")["away_score"].mean()
    matches_count = df.groupby("tournament")["home_score"].count()

    # combine into a single DataFrame
    env = pd.DataFrame({
        "matches": matches_count,
        "avg_home_goals": home_avg,
        "avg_away_goals": away_avg,
        "avg_total_goals": home_avg + away_avg
    })

    print(env.sort_values("matches", ascending=False).head(15))
    return env


# ============================================================
# 3. HOME VS NEUTRAL GOAL PROFILE
# ============================================================
def home_vs_neutral_goals(df):
    print("\n=== HOME VS NEUTRAL GOALS ===")

    home = df[df["neutral"] == False]
    neutral = df[df["neutral"] == True]

    home_adv = home["home_score"].mean() - home["away_score"].mean()

    print(f"Home matches:      {len(home)}")
    print(f"Neutral matches:   {len(neutral)}")
    print(f"Home advantage:    {round(home_adv, 3)}")
    print(f"Neutral avg goals: {round((neutral['home_score'] + neutral['away_score']).mean(), 3)}")

    return home_adv


# ============================================================
# 4. SCORELINE DISTRIBUTION
# ============================================================
def scoreline_distribution(df):
    df["scoreline"] = df["home_score"].astype(str) + "-" + df["away_score"].astype(str)
    dist = df["scoreline"].value_counts()

    print("\n=== TOP 20 COMMON SCORELINES ===")
    print(dist.head(20))

    return dist


# ============================================================
# 5. TEAM GOAL PROFILES
# ============================================================
def team_goal_profiles(df):
    print("\n=== TEAM GOAL PROFILES (GF/GA) ===")  # GF ... Goals for | GA ... Goals Against

    teams = pd.concat([df["home_team"], df["away_team"]]).unique()
    data = {}

    for team in teams:
        home = df[df["home_team"] == team]
        away = df[df["away_team"] == team]

        matches = len(home) + len(away)
        if matches == 0:
            continue

        gf = home["home_score"].sum() + away["away_score"].sum()
        ga = home["away_score"].sum() + away["home_score"].sum()

        data[team] = {
            "matches": matches,
            "goals_for": gf,
            "goals_against": ga,
            "avg_gf": gf / matches,
            "avg_ga": ga / matches,
        }

    df_gp = pd.DataFrame(data).T

    print("\nMost scoring teams:")
    print(df_gp[df_gp["matches"] >= MIN_MATCHES].sort_values("avg_gf", ascending=False).head(15))

    print("\nBest defensive teams (lowest GA):")
    print(df_gp[df_gp["matches"] >= MIN_MATCHES].sort_values("avg_ga").head(15))

    return df_gp


# ============================================================
# 6. ATTACK & DEFENSE STRENGTH
# ============================================================
def weighted_median(values, weights):
    """
    Compute the weighted median of `values` with corresponding `weights`.
    """
    values, weights = np.array(values), np.array(weights)
    sorter = np.argsort(values)
    values, weights = values[sorter], weights[sorter]
    cumsum = np.cumsum(weights)
    cutoff = weights.sum() / 2.0
    return values[np.searchsorted(cumsum, cutoff)]


def compute_attack_defense(df):
    """
    Compute attack and defense strengths for teams using weighted medians.

    Weights account for match recency and tournament importance.
    Team medians are shrunk toward global medians to stabilize estimates for few matches.
    Attack = GF relative to global median; Defense = GA relative to global median.
    Values are log-transformed and normalized to [0,1]. Teams with fewer than MIN_MATCHES are skipped.

    Parameters:
        df (pd.DataFrame): Match results with 'home_team', 'away_team',
                           'home_score', 'away_score', 'date', 'tournament'.

    Returns:
        pd.DataFrame: Team strengths including matches, weighted medians, raw and normalized attack/defense.
    """

    df = df.copy()
    df["date"] = pd.to_datetime(df["date"])
    current_date = df["date"].max()

    # Tournament importance
    major = [
        "fifa world cup", "fifa world cup qualification",
        "uefa euro", "uefa euro qualification",
        "copa américa", "copa américa qualification",
        "african cup of nations", "african cup of nations qualification",
        "afc asian cup", "afc asian cup qualification",
        "gold cup", "gold cup qualification",
        "uefa nations league", "concacaf nations league"
    ]
    friendlies = ["friendly", "kirin challenge cup", "three nations cup", "tri nation tournament", "tri-nations series", "island games", "fifa series"]
    minor_regional = ["baltic cup", "saff cup", "aff championship", "aff championship qualification",
                      "conifa world football cup qualification", "conifa asia cup",
                      "conifa south america football cup", "conifa africa football cup"]

    def get_tournament_weight(name):
        t = str(name).lower()
        if t in major:
            if "world cup" in t: return 1.5
            if "euro" in t or "copa américa" in t or "african cup" in t or "afc asian cup" in t or "gold cup" in t: return 1.3
            return 1.2
        elif t in friendlies:
            return 1.0
        elif t in minor_regional:
            return 0.9
        return 1.0

    # Recency + tournament weight
    df["days_ago"] = (current_date - df["date"]).dt.days
    df["weight"] = np.exp(-DECAY_LAMBDA * df["days_ago"]) * df["tournament"].apply(get_tournament_weight)

    teams = pd.concat([df["home_team"], df["away_team"]]).unique()
    strengths = []

    all_gf = np.concatenate([df["home_score"], df["away_score"]])
    all_ga = np.concatenate([df["away_score"], df["home_score"]])
    all_weights = np.concatenate([df["weight"], df["weight"]])
    global_median_gf = weighted_median(all_gf, all_weights)
    global_median_ga = weighted_median(all_ga, all_weights)

    for team in teams:
        home = df[df["home_team"] == team]
        away = df[df["away_team"] == team]
        matches = len(home) + len(away)
        if matches < MIN_MATCHES:
            continue

        gf_values = np.concatenate([home["home_score"], away["away_score"]])
        gf_weights = np.concatenate([home["weight"], away["weight"]])
        gf_median = weighted_median(gf_values, gf_weights)
        gf_shrink = (gf_median * matches + SHRINK_K * global_median_gf) / (matches + SHRINK_K)

        ga_values = np.concatenate([home["away_score"], away["home_score"]])
        ga_weights = np.concatenate([home["weight"], away["weight"]])
        ga_median = weighted_median(ga_values, ga_weights)
        ga_shrink = (ga_median * matches + SHRINK_K * global_median_ga) / (matches + SHRINK_K)

        attack_raw = gf_shrink / global_median_gf
        defense_raw = global_median_ga / ga_shrink

        strengths.append({
            "team": team,
            "matches": matches,
            "median_gf_weighted": round(gf_shrink, 3),
            "median_ga_weighted": round(ga_shrink, 3),
            "attack_strength_raw": round(attack_raw, 3),
            "defense_strength_raw": round(defense_raw, 3)
        })

    df_strengths = pd.DataFrame(strengths)
    df_strengths["attack_strength"] = np.log1p(df_strengths["attack_strength_raw"])
    df_strengths["attack_strength"] = (df_strengths["attack_strength"] - df_strengths["attack_strength"].min()) / \
                                      (df_strengths["attack_strength"].max() - df_strengths["attack_strength"].min())
    df_strengths["defense_strength"] = np.log1p(df_strengths["defense_strength_raw"])
    df_strengths["defense_strength"] = (df_strengths["defense_strength"] - df_strengths["defense_strength"].min()) / \
                                       (df_strengths["defense_strength"].max() - df_strengths["defense_strength"].min())

    df_strengths.sort_values("attack_strength", ascending=False, inplace=True)
    return df_strengths


# ============================================================
# MAIN
# ============================================================
def main():
    df = pd.read_csv(os.path.join(BASE_DIR, ACTIVE_CSV))
    df["date"] = pd.to_datetime(df["date"], format="%Y-%m-%d", errors="coerce")
    dataset_overview(df)
    tournament_environment(df)
    home_vs_neutral_goals(df)
    scoreline_distribution(df)
    team_goal_profiles(df)

    compute_attack_defense(df)


if __name__ == "__main__":
    main()

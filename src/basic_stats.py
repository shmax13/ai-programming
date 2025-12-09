import pandas as pd
import os

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
RESULTS_FULL_CSV = "data/processed/results_full.csv"
RESULTS_10Y_CSV = "data/processed/results_last_10yrs.csv"
RESULTS_5Y_CSV = "data/processed/results_last_5yrs.csv"

ACTIVE_CSV = RESULTS_5Y_CSV
PRINT_ALL = False

def generate_stats(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculates basic statistics (W-L-D) for every team in the dataset.
    """
    stats = {}

    # get all unique teams
    all_teams = pd.concat([df['home_team'], df['away_team']]).unique()
    
    for team in all_teams:
        
        # home matches
        home_games = df[df['home_team'] == team]
        home_wins = (home_games['result'] == 'home_win').sum()
        home_draws = (home_games['result'] == 'draw').sum()
        home_losses = (home_games['result'] == 'away_win').sum()
        
        # away matches
        away_games = df[df['away_team'] == team]
        away_wins = (away_games['result'] == 'away_win').sum()
        away_draws = (away_games['result'] == 'draw').sum()
        away_losses = (away_games['result'] == 'home_win').sum()
        
        # aggregate
        total_games = len(home_games) + len(away_games)
        total_wins = home_wins + away_wins
        total_losses = home_losses + away_losses
        total_draws = home_draws + away_draws

        stats[team] = {
            'Total Games': total_games,
            'Wins': total_wins,
            'Losses': total_losses,
            'Draws': total_draws,
            'Home Wins': home_wins,
            'Home Losses': home_losses,
            'Away Wins': away_wins,
            'Away Losses': away_losses
        }

    stats_df = pd.DataFrame.from_dict(stats, orient='index')
    stats_df.index.name = 'Team'
    
    stats_df['Win %'] = (stats_df['Wins'] / stats_df['Total Games'] * 100).round(2)
    
    # sort by total games played
    return stats_df.sort_values(by='Total Games', ascending=False)


def main():
    try:
        df_clean = pd.read_csv(os.path.join(BASE_DIR, ACTIVE_CSV))
        
        stats_df = generate_stats(df_clean)

        if (PRINT_ALL):
            print("## ⚽ All Teams by Games Played (All-Time) ##")
            print(stats_df.to_string(index=True))
        else:
            print("## ⚽ Top 10 Teams by Games Played (All-Time) ##")
            print(stats_df.head(10).to_string(index=True))

        print("\n---")
        print(f"Successfully calculated stats for {len(stats_df)} teams.")
        
    except FileNotFoundError:
        print(f"Error: The cleaned CSV file was not found at {ACTIVE_CSV}. Please ensure preprocessing.py has been run.")


if __name__ == "__main__":
    main()
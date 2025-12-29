import numpy as np

# dummy skill function. replace this in notebooks with actual skill functions.
def dummy_skill_function(team):
    return np.random.normal(0, 1)

# globals. dirty but works as long as only simulate_world_cup is called sequentially
skill_func = dummy_skill_function # dummy just gives a random skill to each team



# groups. unconfirmed playoff spots are educated guesses.
groups = {
    "A": ["mexico", "south korea", "south africa", "denmark"],
    "B": ["canada", "switzerland", "qatar", "italy"],
    "C": ["brazil", "morocco", "scotland", "haiti"],
    "D": ["united states", "paraguay", "australia", "turkey"],
    "E": ["germany", "ecuador", "ivory coast", "curaçao"],
    "F": ["netherlands", "japan", "tunisia", "sweden"],
    "G": ["belgium", "egypt", "iran", "new zealand"],
    "H": ["spain", "cape verde", "saudi arabia", "uruguay"],
    "I": ["france", "senegal", "norway", "iraq"],
    "J": ["argentina", "algeria", "austria", "jordan"],
    "K": ["portugal", "colombia", "uzbekistan", "dr congo"],
    "L": ["england", "croatia", "ghana", "panama"]
}

# very basic match simulation
def simulate_match(team1, team2, max_draw_prob=0.15):
    s1 = skill_func(team1)
    s2 = skill_func(team2)
    skill_diff = s1 - s2
    
    # draw probability higher when skills are close
    draw_prob = max_draw_prob * np.exp(-abs(skill_diff))
    
    # win probability for home team
    p_home_win = 1 / (1 + np.exp(-skill_diff))
    
    r = np.random.rand()
    if r < p_home_win:
        return team1
    elif r < p_home_win + draw_prob:
        return "draw"
    else:
        return team2
    
# knockout match -> draw is not possible
def simulate_knockout_match(team1, team2):
    return simulate_match(team1, team2, 0)

# simulate one single group
def simulate_group(team_list):
    """
    Round-robin simulation for a list of teams.
    Returns a list of dicts with team points, sorted by points.
    """
    # Initialize points
    points = {team: 0 for team in team_list}

    for i, t1 in enumerate(team_list):
        for j, t2 in enumerate(team_list):
            if i < j:
                winner = simulate_match(t1, t2)
                if winner == t1:
                    points[t1] += 3
                elif winner == t2:
                    points[t2] += 3
                else:  # draw
                    points[t1] += 1
                    points[t2] += 1

    # convert to sorted table
    table = sorted([{"team": team, "points": pts} for team, pts in points.items()],
                   key=lambda x: x["points"], reverse=True)

    return table

# simulate all groups
def simulate_group_stage():
    group_tables = {}
    for group_name, teams in groups.items():
        table = simulate_group(teams)
        group_tables[group_name] = table

    return group_tables

# from the group stage results, create a list of matchups for the round of 32.
# this follows the official placements (https://en.wikipedia.org/wiki/2026_FIFA_World_Cup_knockout_stage)
def create_knockouts_list(group_tables):
    # TODO: do 3rd placed teams properly
    r32 = [
        group_tables["E"][0]['team'],  group_tables["A"][2]['team'],  # Match 1: 1E vs 3A/B/C/D/F
        group_tables["I"][0]['team'],  group_tables["C"][2]['team'],  # Match 2: 1I vs 3C/D/F/G/H
        group_tables["A"][1]['team'],  group_tables["B"][1]['team'],  # Match 3: 2A vs 2B
        group_tables["F"][0]['team'],  group_tables["C"][1]['team'],  # Match 4: 1F vs 2C

        group_tables["K"][1]['team'],  group_tables["L"][1]['team'],  # Match 5: 2K vs 2L    
        group_tables["H"][0]['team'],  group_tables["J"][1]['team'],  # Match 6: 1H vs 2J 
        group_tables["D"][0]['team'],  group_tables["B"][2]['team'],  # Match 7: 1D vs 3B/E/F/I/J   
        group_tables["G"][0]['team'],  group_tables["F"][2]['team'],  # Match 8: 1G vs 3A/E/H/I/J  

        group_tables["C"][0]['team'],  group_tables["F"][1]['team'],  # Match 9: 1C vs 2F    
        group_tables["E"][1]['team'],  group_tables["I"][1]['team'],  # Match 10: 2E vs 2I    
        group_tables["A"][0]['team'],  group_tables["I"][2]['team'],  # Match 11: 1A vs 3C/E/F/H/I    
        group_tables["L"][0]['team'],  group_tables["K"][2]['team'],  # Match 12: 1L vs 3E/H/I/J/K 

        group_tables["J"][0]['team'],  group_tables["H"][1]['team'],  # Match 13: 1J vs 2H   
        group_tables["D"][1]['team'],  group_tables["G"][1]['team'],  # Match 14: 2D vs 2G   
        group_tables["B"][0]['team'],  group_tables["G"][2]['team'],  # Match 15: 1B vs 3E/F/G/I/J    
        group_tables["K"][0]['team'],  group_tables["D"][2]['team'],  # Match 16: 1K vs 3D/E/I/J/L
    ]

    return r32

def simulate_knockouts(group_tables):
    # first, create list of teams for round of 32
    # eg ["usa", "canada", "mexico", "austria", .."] 
    # means the first two games are usa vs canada and mexico vs austria. 
    # the winners will face again in round of 16.
    r32 = create_knockouts_list(group_tables)

    # Helper to run a round
    def run_round(teams):
        winners = []
        for i in range(0, len(teams), 2):
            t1, t2 = teams[i], teams[i+1]
            winner = simulate_knockout_match(t1, t2)
            winners.append(winner)
        return winners

    # Round of 16
    r16 = run_round(r32)

    # Quarterfinals
    qf = run_round(r16)

    # Semifinals
    sf = run_round(qf)

    # Final
    final = run_round(sf)

    # Winner
    champion = final[0]

    return r32, r16, qf, sf, final, champion

# helper function to print group stage results nicely
def print_group_results(group_tables):
    print("GROUP RESULTS:")
    for group, table in group_tables.items():
        print(f"Group {group}")
        for row in table:
            print(f"  {row['team']:<15} {row['points']}")
    print()

# helper function to print placement results nicely
def print_placements(placements):
    print("PLACEMENTS:")
    for team, stage in sorted(placements.items()):
        print(f"{team:<15} {stage}")
    print()


def calculate_placements(group_tables, r32, r16, qf, sf, f, champion):
    """
    Calculate how far each team got in the tournament.
    Returns: dict {team_name: stage}
    Stages: "GROUPS", "R32", "R16", "QF", "SF", "F", "Winner"
    """
    placements = {}
    for group, table in group_tables.items():
        for row in table:
            placements[row['team']] = "GROUPS"
    for team in r32:
        placements[team] = "R32"
    for team in r16:
        placements[team] = "R16"
    for team in qf:
        placements[team] = "QF"
    for team in sf:
        placements[team] = "SF"
    for team in f:
        placements[team] = "F"
    placements[champion] = "WINNER"

    return placements

# main function. try to call only this from other modules/notebooks.
def simulate_world_cup(sf=dummy_skill_function, verbose=True):
    global skill_func
    skill_func = sf

    group_tables = simulate_group_stage()
    r32, r16, qf, sf, f, c = simulate_knockouts(group_tables)
    placements = calculate_placements(group_tables, r32, r16, qf, sf, f, c)

    if verbose:
        print_group_results(group_tables)
        print_placements(placements)

    return placements


# for testing
if __name__ == '__main__':
    simulate_world_cup()
import numpy as np

# groups. playoff teams are just missing for now...
groups = {
    "A": ["mexico", "south korea", "south africa"],
    "B": ["canada", "switzerland", "qatar"],
    "C": ["brazil", "morocco", "scotland", "haiti"],
    "D": ["united states", "paraguay", "australia"],
    "E": ["germany", "ecuador", "ivory coast", "curaçao"],
    "F": ["netherlands", "japan", "tunisia"],
    "G": ["belgium", "egypt", "iran", "new zealand"],
    "H": ["spain", "cape verde", "saudi arabia", "uruguay"],
    "I": ["france", "senegal", "norway"],
    "J": ["argentina", "algeria", "austria", "jordan"],
    "K": ["portugal", "colombia", "uzbekistan"],
    "L": ["england", "croatia", "ghana", "panama"]
}

# very basic match simulation
def simulate_match(team1, team2, skill_func, max_draw_prob=0.15):
    s1 = skill_func(team1)
    s2 = skill_func(team2)
    skill_diff = s1 - s2
    
    # draw probability higher when skills are close
    draw_prob = max_draw_prob * np.exp(-abs(skill_diff))
    
    # win probability for home team
    p_home_win = 1 / (1 + np.exp(-skill_diff))
    
    r = np.random.rand()
    if r < p_home_win:
        return "home_win"
    elif r < p_home_win + draw_prob:
        return "draw"
    else:
        return "away_win"

# very basic group simulation
def simulate_group(team_list, skill_func):
    """
    Round-robin simulation for a list of teams.
    Returns a list of dicts with team points, sorted by points.
    """
    # Initialize points
    points = {team: 0 for team in team_list}

    for i, t1 in enumerate(team_list):
        for j, t2 in enumerate(team_list):
            if i < j:
                result = simulate_match(t1, t2, skill_func)

                if result == "home_win":
                    points[t1] += 3
                elif result == "away_win":
                    points[t2] += 3
                else:  # draw
                    points[t1] += 1
                    points[t2] += 1

    # convert to sorted table
    table = sorted([{"team": team, "points": pts} for team, pts in points.items()],
                   key=lambda x: x["points"], reverse=True)

    return table
import pandas as pd

data = pd.read_csv("../dataset/cleaned_match_results.csv")
team_stats = data.groupby(['match_id', 'team_id', 'outcome']).agg({
    'kills': 'sum',
    'deaths': 'sum',
    'assists': 'sum',
    'total_damage_dealt': 'sum',
    'gold_earned': 'sum',
    'cs': 'sum',
    'KDA': 'mean',
    'Kill Participation': 'mean',
}).reset_index()

team_stats.to_csv("team_aggregated_stats.csv", index=False)

print("Aggregated data saved to team_aggregated_stats.csv")
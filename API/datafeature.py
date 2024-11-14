import pandas as pd

# Load data
data = pd.read_csv("../dataset/cleaned_match_results.csv")
# Group by match_id and team_id, aggregate as needed
team_stats = data.groupby(['match_id', 'team_id', 'outcome']).agg({
    'kills': 'sum',
    'deaths': 'sum',
    'assists': 'sum',
    'total_damage_dealt': 'sum',
    'gold_earned': 'sum',
    'cs': 'sum',
    'KDA': 'mean',
    'Kill Participation': 'mean',
    # add other aggregations as needed
}).reset_index()

# Save to a new CSV file
team_stats.to_csv("team_aggregated_stats.csv", index=False)

print("Aggregated data saved to team_aggregated_stats.csv")
import pandas as pd
import json
import os

# Define the folder containing JSON files
folder_path = 'data/'  # Adjust the path as needed

# Define lists to store extracted data
matches_list = []

# Loop through each JSON file in the specified folder
for filename in os.listdir(folder_path):
    if filename.endswith('.json'):
        # Load JSON data
        with open(os.path.join(folder_path, filename), 'r') as file:
            data = json.load(file)

        # Get the first key in the dictionary (assuming it's the player name)
        first_key = next(iter(data))

        # Access the player's matches
        matches_data = data[first_key]  # Access the player's matches using the first key

        # Loop through each match in the data
        for match in matches_data:
            # Check if 'metadata' and 'info' keys exist
            if 'metadata' in match and 'info' in match:
                metadata = match['metadata']
                info = match['info']  # List of team-level data (2 teams per match)

                # Check if the game mode is not "ARAM"
                if info.get('gameMode') != "ARAM":
                    teams = info.get('teams', [])  # Extract teams info
                    participants_info = info.get('participants', [])  # Get participants info from the 'info' field
                    win_team_id = None
                    game_duration = info.get('gameDuration', 0)

                    # Check if the game duration is at least 180 seconds (3 minutes)
                    if game_duration >= 180:
                        # Determine which team won
                        for team in teams:
                            if team.get('win', False):  # Check if the team won
                                win_team_id = team['teamId']  # Get the winning team's ID
                                break

                        # Create a dictionary to store objective metrics for each team
                        team_objectives = {
                            team['teamId']: {
                                'dragon_kills': team['objectives']['dragon']['kills'],
                                'baron_kills': team['objectives']['baron']['kills'],
                                'tower_kills': team['objectives']['tower']['kills']
                            } for team in teams
                        }

                        # Create entries for each participant
                        for participant in participants_info:
                            kills = participant['kills']
                            deaths = participant['deaths']
                            assists = participant['assists']
                            gold_earned = participant['goldEarned']

                            # Calculate derived metrics
                            kda = (kills + assists) / deaths if deaths > 0 else (kills + assists)  # Avoid division by zero
                            total_kills = sum(p['kills'] for p in participants_info)
                            kill_participation = (kills + assists) / total_kills if total_kills > 0 else 0
                            avg_gold_per_minute = gold_earned / (game_duration / 60) if game_duration > 0 else 0

                            participant_data = {
                                'match_id': metadata['matchId'],
                                'participant_id': participant['summonerId'],  # Ensure correct participant ID
                                'team_id': participant['teamId'],  # Ensure to get the correct team ID
                                'outcome': 'win' if participant['teamId'] == win_team_id else 'lose',  # Determine outcome
                                'label': 1 if participant['teamId'] == win_team_id else 0,  # Label: 1 for win, 0 for lose
                                'kills': kills,
                                'deaths': deaths,
                                'assists': assists,
                                'total_damage_dealt': participant['totalDamageDealtToChampions'],
                                'gold_earned': gold_earned,
                                'cs': participant['totalMinionsKilled'],  # CS = creep score
                                'wards_placed': participant['wardsPlaced'],
                                'wards_killed': participant['wardsKilled'],
                                'dragon_kills': team_objectives.get(participant['teamId'], {}).get('dragon_kills', 0),
                                'baron_kills': team_objectives.get(participant['teamId'], {}).get('baron_kills', 0),
                                'tower_kills': team_objectives.get(participant['teamId'], {}).get('tower_kills', 0),
                                'game_duration': game_duration,
                                'game_mode': info.get('gameMode', ''),  # Get the game mode with default
                                'KDA': kda,
                                'Kill Participation': kill_participation,
                                'Average Gold per Minute': avg_gold_per_minute,
                            }

                            # Exclude participants with "Bot" in their ID
                            if "BOT" not in participant['summonerId']:
                                matches_list.append(participant_data)

# Create a DataFrame from the extracted data
df = pd.DataFrame(matches_list)

# Display the updated DataFrame
print(df[['participant_id', 'kills', 'deaths', 'assists', 'KDA', 'Kill Participation', 'Average Gold per Minute']])

# Save the DataFrame to a CSV file
df.to_csv('match_results_with_objectives.csv', index=False)

# Optional: Display a message indicating the file has been saved
print("DataFrame saved to 'match_results_with_objectives.csv'")

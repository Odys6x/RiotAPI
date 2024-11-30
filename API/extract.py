import pandas as pd
import json
import os

folder_path = 'data/'

matches_list = []

for filename in os.listdir(folder_path):
    if filename.endswith('.json'):
        with open(os.path.join(folder_path, filename), 'r') as file:
            data = json.load(file)
        first_key = next(iter(data))

        matches_data = data[first_key]
        for match in matches_data:
            if 'metadata' in match and 'info' in match:
                metadata = match['metadata']
                info = match['info']

                if info.get('gameMode') != "ARAM":
                    teams = info.get('teams', [])
                    participants_info = info.get('participants', [])
                    win_team_id = None
                    game_duration = info.get('gameDuration', 0)

                    if game_duration >= 180:
                        for team in teams:
                            if team.get('win', False):
                                win_team_id = team['teamId']
                                break

                        team_objectives = {
                            team['teamId']: {
                                'dragon_kills': team['objectives']['dragon']['kills'],
                                'baron_kills': team['objectives']['baron']['kills'],
                                'tower_kills': team['objectives']['tower']['kills']
                            } for team in teams
                        }

                        for participant in participants_info:
                            kills = participant['kills']
                            deaths = participant['deaths']
                            assists = participant['assists']
                            gold_earned = participant['goldEarned']

                            kda = (kills + assists) / deaths if deaths > 0 else (kills + assists)
                            total_kills = sum(p['kills'] for p in participants_info)
                            kill_participation = (kills + assists) / total_kills if total_kills > 0 else 0
                            avg_gold_per_minute = gold_earned / (game_duration / 60) if game_duration > 0 else 0

                            participant_data = {
                                'match_id': metadata['matchId'],
                                'participant_id': participant['summonerId'],
                                'team_id': participant['teamId'],
                                'outcome': 'win' if participant['teamId'] == win_team_id else 'lose',
                                'label': 1 if participant['teamId'] == win_team_id else 0,
                                'kills': kills,
                                'deaths': deaths,
                                'assists': assists,
                                'total_damage_dealt': participant['totalDamageDealtToChampions'],
                                'gold_earned': gold_earned,
                                'cs': participant['totalMinionsKilled'],
                                'wards_placed': participant['wardsPlaced'],
                                'wards_killed': participant['wardsKilled'],
                                'dragon_kills': team_objectives.get(participant['teamId'], {}).get('dragon_kills', 0),
                                'baron_kills': team_objectives.get(participant['teamId'], {}).get('baron_kills', 0),
                                'tower_kills': team_objectives.get(participant['teamId'], {}).get('tower_kills', 0),
                                'game_duration': game_duration,
                                'game_mode': info.get('gameMode', ''),
                                'KDA': kda,
                                'Kill Participation': kill_participation,
                                'Average Gold per Minute': avg_gold_per_minute,
                            }

                            if "BOT" not in participant['summonerId']:
                                matches_list.append(participant_data)

df = pd.DataFrame(matches_list)

print(df[['participant_id', 'kills', 'deaths', 'assists', 'KDA', 'Kill Participation', 'Average Gold per Minute']])

df.to_csv('match_results_with_objectives.csv', index=False)

print("DataFrame saved to 'match_results_with_objectives.csv'")

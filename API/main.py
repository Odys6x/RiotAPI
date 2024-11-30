import time
import requests
import json

API_KEY = 'RGAPI-a7989b51-3943-4f64-aa72-6f53a77df708'


def get_match_ids(puuid, count=100):
    url = f"https://sea.api.riotgames.com/lol/match/v5/matches/by-puuid/{puuid}/ids?start=0&count={count}&api_key={API_KEY}"
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Error fetching match IDs for PUUID {puuid}: {response.status_code}")
        return []


def get_match_details(match_id):
    url = f"https://sea.api.riotgames.com/lol/match/v5/matches/{match_id}?api_key={API_KEY}"
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Error fetching match details for match ID {match_id}: {response.status_code}")
        return {}


def save_to_file(data, filename):
    with open(filename, 'w') as f:
        json.dump(data, f, indent=4)
    print(f"Data saved to {filename}")


def load_puuids_from_file(filename):
    with open(filename) as f:
        data = json.load(f)
    puuids = {}
    for riot_id, matches in data.items():
        if matches:
            puuids[riot_id] = matches[0]['metadata']['participants']
    return puuids


puuids_filename = "player_matches.json"
puuids = load_puuids_from_file(puuids_filename)

all_matches = {}

count = 0
for riot_id, puuid_list in puuids.items():
    player_matches = []

    for puuid in puuid_list:
        match_ids = get_match_ids(puuid)
        for match_id in match_ids:
            match_details = get_match_details(match_id)
            player_matches.append(match_details)
            count = count + 1
            print(count)
            print(f"{match_id} Done, wait for the next match")
            time.sleep(1.2)
        print(f"{puuid} done, Next Player")

    all_matches[riot_id] = player_matches

output_filename = "player_matches_with_details.json"
save_to_file(all_matches, output_filename)

for summoner, matches in all_matches.items():
    print(f"{summoner} has {len(matches)} matches.")

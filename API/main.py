import time
import requests
import json
import os

API_KEY = 'RGAPI-a7989b51-3943-4f64-aa72-6f53a77df708'


# Function to get match IDs for a player (Region is 'asia')
def get_match_ids(puuid, count=100):
    url = f"https://sea.api.riotgames.com/lol/match/v5/matches/by-puuid/{puuid}/ids?start=0&count={count}&api_key={API_KEY}"
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Error fetching match IDs for PUUID {puuid}: {response.status_code}")
        return []


# Function to get match details based on match ID (Region is 'sea')
def get_match_details(match_id):
    url = f"https://sea.api.riotgames.com/lol/match/v5/matches/{match_id}?api_key={API_KEY}"
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Error fetching match details for match ID {match_id}: {response.status_code}")
        return {}


# Function to save data to a local JSON file
def save_to_file(data, filename):
    with open(filename, 'w') as f:
        json.dump(data, f, indent=4)
    print(f"Data saved to {filename}")


# Function to load PUUIDs from a JSON file
def load_puuids_from_file(filename):
    with open(filename) as f:
        data = json.load(f)
    puuids = {}
    for riot_id, matches in data.items():
        # Assuming the matches contain a metadata key where PUUID is available
        if matches:
            puuids[riot_id] = matches[0]['metadata']['participants']  # Adjust this as per your actual structure
    return puuids


# Load PUUIDs from the previously saved file
puuids_filename = "player_matches.json"  # Your PUUIDs file
puuids = load_puuids_from_file(puuids_filename)

# Main flow (loop moved out of function)
all_matches = {}

# For each Riot ID and PUUID list, process matches
count = 0
for riot_id, puuid_list in puuids.items():
    player_matches = []

    # Process each PUUID outside the function
    for puuid in puuid_list:
        match_ids = get_match_ids(puuid)
        for match_id in match_ids:
            match_details = get_match_details(match_id)
            player_matches.append(match_details)
            count = count + 1
            print(count)
            print(f"{match_id} Done, wait for the next match")
            time.sleep(1.2)  # Sleep to respect rate limits (adjust based on actual API limits)
        print(f"{puuid} done, Next Player")

    # Store player matches for each Riot ID
    all_matches[riot_id] = player_matches

# Save the player match data to a local file
output_filename = "player_matches_with_details.json"
save_to_file(all_matches, output_filename)

# Example of checking the output
for summoner, matches in all_matches.items():
    print(f"{summoner} has {len(matches)} matches.")

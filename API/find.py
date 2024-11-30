import json

with open('player_matches.json') as f:
    data = json.load(f)

player_key = "livinglight47#SG2"
puuids = set()

if player_key in data:
    matches = data[player_key]
    for match in matches:
        participants = match['metadata']['participants']

        puuids.update(participants)

output_data = {
    "participants": list(puuids)
}

with open('participants.json', 'w') as outfile:
    json.dump(output_data, outfile, indent=4)

print("Unique participants saved to 'participants.json'")

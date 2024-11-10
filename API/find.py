import json

# Load your JSON data
with open('player_matches.json') as f:  # Replace with your actual file name
    data = json.load(f)

player_key = "livinglight47#SG2"  # Key for the specific player
puuids = set()  # Use a set to store unique puuids

# Iterate through the matches for the specified player
if player_key in data:
    matches = data[player_key]  # Get matches for Odys6x#6969
    for match in matches:
        # Access participants directly
        participants = match['metadata']['participants']

        # Add each puuid to the set to ensure uniqueness
        puuids.update(participants)  # Update the set with participants

# Create a dictionary to hold the unique participants
output_data = {
    "participants": list(puuids)  # Convert the set back to a list for JSON output
}

# Save the participants to a new JSON file
with open('participants.json', 'w') as outfile:  # Replace with your desired output file name
    json.dump(output_data, outfile, indent=4)

# Print a confirmation message
print("Unique participants saved to 'participants.json'")

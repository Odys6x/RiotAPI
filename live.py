import requests
import time
import json
import warnings
import threading

# Suppress SSL certificate warnings
warnings.filterwarnings("ignore", message=".*unverified HTTPS request.*")

# URLs for player stats and game events
player_url = "https://127.0.0.1:2999/liveclientdata/playerlist"
event_url = "https://127.0.0.1:2999/liveclientdata/eventdata"

player_output_file = "player_data.json"  # Output file to save player data
event_output_file = "event_data.json"  # Output file to save event data

# Initialize lists to hold game data
player_data = []
event_data = []

# Function to fetch player data and save to file
def fetch_player_data():
    while True:
        try:
            response = requests.get(player_url, verify=False)  # Disable SSL verification for localhost
            response.raise_for_status()  # Raise an error for bad responses
            data = response.json()  # Parse JSON response
            print("Player Data:", data)

            # Append the current data to the list
            player_data.append(data)

            # Update the JSON file with the current data
            with open(player_output_file, 'w') as f:
                json.dump(player_data, f, indent=4)  # Save data with pretty formatting

        except requests.exceptions.RequestException as e:
            print(f"An error occurred while fetching player data: {e}")

        time.sleep(1)  # Wait for 1 second before the next request

# Function to fetch event data and save to file
def fetch_event_data():
    while True:
        try:
            response = requests.get(event_url, verify=False)  # Disable SSL verification for localhost
            response.raise_for_status()  # Raise an error for bad responses
            data = response.json()  # Parse JSON response
            print("Event Data:", data)

            # Append the current data to the list
            event_data.append(data)

            # Update the JSON file with the current data
            with open(event_output_file, 'w') as f:
                json.dump(event_data, f, indent=4)  # Save data with pretty formatting

        except requests.exceptions.RequestException as e:
            print(f"An error occurred while fetching event data: {e}")

        time.sleep(1)  # Wait for 1 second before the next request

# Create and start two threads: one for player data and one for event data
player_thread = threading.Thread(target=fetch_player_data)
event_thread = threading.Thread(target=fetch_event_data)

player_thread.start()
event_thread.start()

# Wait for both threads to complete (they will run indefinitely)
player_thread.join()
event_thread.join()

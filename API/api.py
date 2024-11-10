import sys
import requests
from PyQt5.QtWidgets import QApplication, QWidget, QLabel
from PyQt5.QtCore import Qt, QTimer

# Replace with your Riot API Key
API_KEY = 'RGAPI-a7989b51-3943-4f64-aa72-6f53a77df708'
GAME_NAME = 'Odys6x'  # Replace with your summoner name
TAG_LINE = '6969'  # Replace with your summoner tag line

class Overlay(QWidget):
    def __init__(self):
        super().__init__()

        # Make the window transparent
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)

        # Create a label to display stats
        self.stats_label = QLabel(self)
        self.stats_label.setStyleSheet("color: white; font-size: 20px;")
        self.stats_label.setAlignment(Qt.AlignCenter)

        # Set a timer to refresh data
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_data)
        self.timer.start(5000)  # Refresh every 5 seconds

        # Initial call to populate data
        self.update_data()

    def update_data(self):
        try:
            # Get the PUUID using game name and tag line
            puuid = self.get_puuid(GAME_NAME, TAG_LINE)
            if puuid:
                # Get match IDs for the player
                match_ids = self.get_match_ids(puuid, count=1)
                if match_ids:
                    # Get details for the latest match
                    match_details = self.get_match_details(match_ids[0])
                    if match_details:
                        self.display_game_data(match_details)
                    else:
                        self.stats_label.setText("Match details not found.")
                else:
                    self.stats_label.setText("No matches found.")
            else:
                self.stats_label.setText("Summoner not found.")
        except Exception as e:
            self.stats_label.setText(f"Error: {str(e)}")

    def get_puuid(self, game_name, tag_line):
        url = f"https://asia.api.riotgames.com/riot/account/v1/accounts/by-riot-id/{game_name}/{tag_line}?api_key={API_KEY}"
        response = requests.get(url)
        if response.status_code == 200:
            return response.json().get('puuid')
        else:
            print(f"Error fetching PUUID for {game_name}#{tag_line}: {response.status_code}")
            return None

    def get_match_ids(self, puuid, count=1):
        url = f"https://sea.api.riotgames.com/lol/match/v5/matches/by-puuid/{puuid}/ids?start=0&count={count}&api_key={API_KEY}"
        response = requests.get(url)
        if response.status_code == 200:
            return response.json()
        else:
            print(f"Error fetching match IDs for PUUID {puuid}: {response.status_code}")
            return []

    def get_match_details(self, match_id):
        url = f"https://sea.api.riotgames.com/lol/match/v5/matches/{match_id}?api_key={API_KEY}"
        response = requests.get(url)
        if response.status_code == 200:
            return response.json()
        else:
            print(f"Error fetching match details for match ID {match_id}: {response.status_code}")
            return None

    def display_game_data(self, match_data):
        player_stats = []
        participants = match_data['info']['participants']
        for player in participants:
            stats = f"{player['summonerName']}: {player['kills']} kills, {player['deaths']} deaths, {player['assists']} assists"
            player_stats.append(stats)
        self.stats_label.setText("\n".join(player_stats))

    def paintEvent(self, event):
        # Optional: Custom painting code can go here
        pass

if __name__ == '__main__':
    app = QApplication(sys.argv)
    overlay = Overlay()
    overlay.setGeometry(100, 100, 800, 600)  # Set the size of the overlay
    overlay.showFullScreen()  # Show full screen or set a specific size
    sys.exit(app.exec_())

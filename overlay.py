import sys
import json
import requests
import time
from PyQt5.QtWidgets import QApplication, QWidget, QLabel
from PyQt5.QtCore import Qt, QTimer

player_url = "https://127.0.0.1:2999/liveclientdata/playerlist"
event_url = "https://127.0.0.1:2999/liveclientdata/eventdata"

player_output_file = "player_data.json"
event_output_file = "event_data.json"


class Overlay(QWidget):
    def __init__(self):
        super().__init__()

        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.WindowTransparentForInput)
        self.setStyleSheet("background-color: rgba(0, 0, 0, 50);")

        self.stats_label = QLabel(self)
        self.stats_label.setStyleSheet("color: white; font-size: 20px;")
        self.stats_label.setAlignment(Qt.AlignCenter)
        self.stats_label.setGeometry(50, 50, 1100, 75)
        self.stats_label.setText("Overlay Loaded!")
        self.stats_label.show()

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_data)
        self.timer.start(1000)

    def update_data(self):
        try:
            player_data = self.fetch_player_data()
            if player_data:
                self.display_game_data(player_data)
            else:
                self.stats_label.setText("No player data found.")
        except Exception as e:
            self.stats_label.setText(f"Error: {str(e)}")

    def fetch_player_data(self):
        try:
            response = requests.get(player_url, verify=False)
            response.raise_for_status()
            data = response.json()

            with open(player_output_file, 'w') as f:
                json.dump(data, f, indent=4)

            return data
        except requests.exceptions.RequestException as e:
            print(f"An error occurred while fetching player data: {e}")
            return None

    def fetch_event_data(self):
        try:
            response = requests.get(event_url, verify=False)
            response.raise_for_status()
            data = response.json()

            with open(event_output_file, 'w') as f:
                json.dump(data, f, indent=4)

            return data
        except requests.exceptions.RequestException as e:
            print(f"An error occurred while fetching event data: {e}")
            return None

    def display_game_data(self, player_data):
        player_stats = []
        for player in player_data:
            kills = player['scores'].get('kills', 0)
            deaths = player['scores'].get('deaths', 0)
            assists = player['scores'].get('assists', 0)
            ward = player['scores'].get('wardScore', 0)
            kda = (kills + assists) / (deaths if deaths > 0 else 1)

            stats = f"{player['summonerName']}: {kills}/{deaths}/{assists}, {ward:.2f} ward score, current KDA: {kda:.2f}"
            print(stats)
            player_stats.append(stats)

        self.stats_label.setText("\n".join(player_stats))

    def paintEvent(self, event):
        pass


if __name__ == '__main__':
    app = QApplication(sys.argv)
    overlay = Overlay()

    overlay.setGeometry(400, 0, 1200, 800)
    overlay.stats_label.setGeometry(50, 50, 1100, 205)

    overlay.show()  # Ensure the overlay is shown
    sys.exit(app.exec_())
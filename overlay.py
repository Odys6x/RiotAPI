import sys
import json
import requests
import time
from PyQt5.QtWidgets import QApplication, QWidget, QLabel
from PyQt5.QtCore import Qt, QTimer

player_url = "https://127.0.0.1:2999/liveclientdata/playerlist"
event_url = "https://127.0.0.1:2999/liveclientdata/eventdata"
game_stats_url = "https://127.0.0.1:2999/liveclientdata/gamestats"

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

        self.team_switch_timer = QTimer(self)
        self.team_switch_timer.timeout.connect(self.switch_teams)
        self.team_switch_timer.start(15000)  # Switch teams every 15 seconds

        self.current_team = 0  # 0 for Team A, 1 for Team B
        self.player_data = []  # Store player data

    def update_data(self):
        try:
            self.player_data = self.fetch_player_data()
            game_stats = self.fetch_game_stats()  # Get game stats and log to file

            if self.player_data:
                game_time = game_stats.get("gameTime", 0)  # Extract gameTime for duration
                self.display_game_data(self.player_data, game_time)
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

    def fetch_game_stats(self):
        try:
            response = requests.get(game_stats_url, verify=False)
            response.raise_for_status()
            game_stats = response.json()

            # Save game stats to event_output_file
            with open(event_output_file, 'w') as f:
                json.dump(game_stats, f, indent=4)

            return game_stats
        except requests.exceptions.RequestException as e:
            print(f"An error occurred while fetching game stats: {e}")
            return {}

    def display_game_data(self, player_data, game_time):
        if not player_data:
            return

        # Separate players into teams
        team_a = [p for p in player_data if p['team'] == "ORDER"]  # Assuming team ORDER is Team A
        team_b = [p for p in player_data if p['team'] == "CHAOS"]  # Assuming team CHAOS is Team B

        # Display stats for the current team
        if self.current_team == 0:
            self.show_team_stats(team_a, "Team ORDER", game_time)
        else:
            self.show_team_stats(team_b, "Team CHAOS", game_time)

    def show_team_stats(self, team, team_name, game_time):
        player_stats = [f"{team_name}:"]
        for player in team:
            kills = player['scores'].get('kills', 0)
            deaths = player['scores'].get('deaths', 0)
            assists = player['scores'].get('assists', 0)
            ward = player['scores'].get('wardScore', 0)
            tower_kills = player['scores'].get('towerKills', 0)
            minions_killed = player['scores'].get('minionsKilled', 0)
            kda = (kills + assists) / (deaths if deaths > 0 else 1)

            # Estimate gold for the player using the game time
            estimated_gold = int(self.estimate_gold(kills, assists, tower_kills, minions_killed, ward, game_time))

            stats = (f"{player['championName']} ({player['summonerName']}): KDA {kills}/{deaths}/{assists}, Current KDA: {kda:.2f} "
                     f"Ward Score: {ward:.2f}, Estimated Gold: {estimated_gold}")
            player_stats.append(stats)

        self.stats_label.setText("\n".join(player_stats))

    def estimate_gold(self, kills, assists, tower_kills, minions_killed, wards_killed, game_time):
        # Passive gold income parameters
        passive_gold_per_10_seconds = 20.4  # Gold earned every 10 seconds after 1:50
        starting_gold = 500  # Starting gold for each player

        # Calculate elapsed time in seconds since the passive gold starts
        if game_time >= 110:  # Only start calculating passive gold after 1:50
            elapsed_passive_time = game_time - 110  # Time after 1:50
            passive_gold = (elapsed_passive_time // 10) * passive_gold_per_10_seconds
        else:
            passive_gold = 0  # No passive gold before 1:50

        # Calculate estimated gold based on the stats
        gold_from_kills = kills * 300  # Adjust according to actual game mechanics
        gold_from_assists = assists * 150  # Adjust according to actual game mechanics
        gold_from_tower_kills = tower_kills * 1000  # Adjust according to actual game mechanics
        gold_from_minions = minions_killed * 14  # Average minion gold
        gold_from_ward_kills = wards_killed * 30  # if you want to include ward kills

        total_gold = (starting_gold + passive_gold +
                      gold_from_kills + gold_from_assists +
                      gold_from_tower_kills + gold_from_minions +
                      gold_from_ward_kills)
        return total_gold

    def switch_teams(self):
        self.current_team = 1 - self.current_team  # Toggle between 0 and 1

    def paintEvent(self, event):
        pass

if __name__ == '__main__':
    app = QApplication(sys.argv)
    overlay = Overlay()

    overlay.setGeometry(400, 0, 1200, 800)
    overlay.stats_label.setGeometry(50, 50, 1100, 205)

    overlay.show()  # Ensure the overlay is shown
    sys.exit(app.exec_())

import sys
import json
import requests
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
        self.team_switch_timer.start(15000)

        self.current_team = 0
        self.player_data = []
        self.event_data = []

    def update_data(self):
        try:
            self.player_data = self.fetch_player_data()
            game_stats = self.fetch_game_stats()
            self.event_data = self.fetch_event_data()  # Fetch event data

            if self.player_data:
                game_time = game_stats.get("gameTime", 0)
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

            with open(event_output_file, 'w') as f:
                json.dump(game_stats, f, indent=4)

            return game_stats
        except requests.exceptions.RequestException as e:
            print(f"An error occurred while fetching game stats: {e}")
            return {}

    def fetch_event_data(self):
        try:
            response = requests.get(event_url, verify=False)
            response.raise_for_status()
            data = response.json()
            events = data["Events"]

            print("Fetched Events:", json.dumps(events, indent=4))

            return events
        except requests.exceptions.RequestException as e:
            print(f"An error occurred while fetching event data: {e}")
            return []

    def display_game_data(self, player_data, game_time):
        if not player_data:
            return

        team_a = [p for p in player_data if p['team'] == "ORDER"]
        team_b = [p for p in player_data if p['team'] == "CHAOS"]

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
            minions_killed = player['scores'].get('minionsKilled', 0)
            kda = (kills + assists) / (deaths if deaths > 0 else 1)

            estimated_gold = int(self.estimate_gold(player['summonerName'],minions_killed, ward, game_time))
            stats = (f"{player['championName']} ({player['summonerName']}): KDA {kills}/{deaths}/{assists}, Current KDA: {kda:.2f} "
                     f"Ward Score: {ward:.2f}, Estimated Gold: {estimated_gold}")
            player_stats.append(stats)

        self.stats_label.setText("\n".join(player_stats))

    def estimate_gold(self, player_name, minions_killed, wards_killed, game_time):
        passive_gold_per_10_seconds = 20.4
        starting_gold = 500

        if game_time >= 110:
            elapsed_passive_time = game_time - 110
            passive_gold = (elapsed_passive_time // 10) * passive_gold_per_10_seconds
        else:
            passive_gold = 0

        gold_from_minions = minions_killed * 14
        gold_from_ward_kills = wards_killed * 30

        gold_from_events = self.calculate_event_gold(player_name)

        total_gold = (starting_gold + passive_gold +
                      gold_from_minions +
                      gold_from_ward_kills + gold_from_events)
        return total_gold

    def calculate_event_gold(self, player_name):
        base_player_name = player_name.split("#")[0]
        event_gold = 0

        for event in self.event_data:
            print(f"Processing EventID {event['EventID']}: {event['EventName']} at {event['EventTime']}")

            if event.get("Acer") == base_player_name and event["EventName"] == "Ace":
                print(f"Player {base_player_name} was the Acer in EventID {event['EventID']} (Ace)")
                event_gold += 150
                continue

            if event.get("KillerName") == base_player_name:
                print(f"Player {base_player_name} was the killer in EventID {event['EventID']}")
                if event["EventName"] == "DragonKill":
                    event_gold += 300
                elif event["EventName"] == "BaronKill":
                    event_gold += 500
                elif event["EventName"] == "TurretKilled":
                    event_gold += 250
                elif event["EventName"] == "InhibKilled":
                    event_gold += 400
                elif event["EventName"] == "ChampionKill":
                    event_gold += 300
                elif event["EventName"] == "FirstBlood":
                    event_gold += 400

            elif base_player_name in event.get("Assisters", []):
                print(f"Player {base_player_name} assisted in EventID {event['EventID']}")
                if event["EventName"] == "DragonKill":
                    event_gold += 100
                elif event["EventName"] == "BaronKill":
                    event_gold += 200

        print(f"Calculated event gold for {player_name}: {event_gold}")
        return event_gold

    def switch_teams(self):
        self.current_team = 1 - self.current_team

    def paintEvent(self, event):
        pass


if __name__ == '__main__':
    app = QApplication(sys.argv)
    overlay = Overlay()

    overlay.setGeometry(400, 0, 1200, 800)
    overlay.stats_label.setGeometry(50, 50, 1100, 205)

    overlay.show()
    sys.exit(app.exec_())

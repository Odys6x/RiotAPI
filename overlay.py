import sys
import json
import requests
import torch
import joblib
from PyQt5.QtWidgets import QApplication, QWidget, QLabel
from PyQt5.QtCore import Qt, QTimer

# URLs for fetching live data
player_url = "https://127.0.0.1:2999/liveclientdata/playerlist"
event_url = "https://127.0.0.1:2999/liveclientdata/eventdata"
game_stats_url = "https://127.0.0.1:2999/liveclientdata/gamestats"

# File paths for saving data
player_output_file = "API/player_data.json"
event_output_file = "API/event_data.json"

# Load your trained model and scaler here
from model import ComplexTabularModel  # Your model import (update if necessary)
from train import input_dim  # Input dimension for the model

class Overlay(QWidget):
    def __init__(self):
        super().__init__()
        self.views = ["order_stats", "chaos_stats", "gold_diff", "win_percentage", "team_stats"]  # Added team_stats view
        self.current_view_index = 0

        # Set up the transparent window for the overlay
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.WindowTransparentForInput)
        self.setStyleSheet("background-color: rgba(0, 0, 0, 50);")

        # Stats label to show text info
        self.stats_label = QLabel(self)
        self.stats_label.setStyleSheet("color: white; font-size: 20px;")
        self.stats_label.setAlignment(Qt.AlignCenter)
        self.stats_label.setGeometry(50, 50, 1100, 75)
        self.stats_label.setText("Overlay Loaded!")
        self.stats_label.show()

        # Timer to fetch data every second
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_data)
        self.timer.start(1000)

        # Timer to switch between views every 15 seconds
        self.switch_view_timer = QTimer(self)
        self.switch_view_timer.timeout.connect(self.switch_view)
        self.switch_view_timer.start(15000)

        self.player_data = []
        self.event_data = []
        self.ally_gold = 0
        self.enemy_gold = 0
        self.gold_difference = 0

        # Load the trained model and scaler
        self.model = ComplexTabularModel(input_dim=input_dim)
        self.model.load_state_dict(torch.load("model/model.pth"))  # Update the model path
        self.model.eval()  # Set model to evaluation mode
        self.scaler = joblib.load("model/scaler.pkl")  # Load the scaler

    def update_data(self):
        try:
            self.player_data = self.fetch_player_data()
            game_stats = self.fetch_game_stats()
            self.event_data = self.fetch_event_data()

            if self.player_data:
                game_time = game_stats.get("gameTime", 0)
                current_view = self.views[self.current_view_index]

                if current_view == "order_stats":
                    self.display_game_data(self.player_data, game_time, "ORDER", "Team ORDER")
                elif current_view == "chaos_stats":
                    self.display_game_data(self.player_data, game_time, "CHAOS", "Team CHAOS")
                elif current_view == "gold_diff":
                    self.display_gold_difference()
                elif current_view == "win_percentage":
                    self.display_win_percentage()  # Ensure this triggers model evaluation
                elif current_view == "team_stats":
                    self.display_team_stats()  # New view for team stats
            else:
                self.stats_label.setText("No player data found.")
        except Exception as e:
            self.stats_label.setText(f"Error: {str(e)}")

    def display_team_stats(self):
        if self.current_view_index == 0:  # Ally is ORDER
            team_order_gold = self.ally_gold
            team_chaos_gold = self.enemy_gold
        else:  # Ally is CHAOS
            team_order_gold = self.enemy_gold
            team_chaos_gold = self.ally_gold
        team_order_kills = sum(
            player['scores'].get('kills', 0) for player in self.player_data if player['team'] == 'ORDER')
        team_order_deaths = sum(
            player['scores'].get('deaths', 0) for player in self.player_data if player['team'] == 'ORDER')
        team_order_assists = sum(
            player['scores'].get('assists', 0) for player in self.player_data if player['team'] == 'ORDER')
        team_order_cs = sum(
            player['scores'].get('creepScore', 0) for player in self.player_data if player['team'] == 'ORDER')
        team_order_kda = team_order_kills / (
            team_order_deaths if team_order_deaths > 0 else 1)  # Avoid division by zero

        # Calculate team CHAOS stats
        team_chaos_kills = sum(
            player['scores'].get('kills', 0) for player in self.player_data if player['team'] == 'CHAOS')
        team_chaos_deaths = sum(
            player['scores'].get('deaths', 0) for player in self.player_data if player['team'] == 'CHAOS')
        team_chaos_assists = sum(
            player['scores'].get('assists', 0) for player in self.player_data if player['team'] == 'CHAOS')
        team_chaos_cs = sum(
            player['scores'].get('creepScore', 0) for player in self.player_data if player['team'] == 'CHAOS')
        team_chaos_kda = team_chaos_kills / (
            team_chaos_deaths if team_chaos_deaths > 0 else 1)  # Avoid division by zero

        # Display stats for Team ORDER
        team_order_stats = (
            f"Team ORDER Stats:\n"
            f"Kills: {team_order_kills}, Deaths: {team_order_deaths}, Assists: {team_order_assists},\n"
            f"Gold: {team_order_gold}, CS: {team_order_cs}, KDA: {team_order_kda:.2f}"
        )

        # Display stats for Team CHAOS
        team_chaos_stats = (
            f"Team CHAOS Stats:\n"
            f"Kills: {team_chaos_kills}, Deaths: {team_chaos_deaths}, Assists: {team_chaos_assists},\n"
            f"Gold: {team_chaos_gold}, CS: {team_chaos_cs}, KDA: {team_chaos_kda:.2f}"
        )

        # Update the label with both team stats
        self.stats_label.setText(f"{team_order_stats}\n\n{team_chaos_stats}")

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

            return events
        except requests.exceptions.RequestException as e:
            print(f"An error occurred while fetching event data: {e}")
            return []
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

        total_gold = starting_gold + passive_gold + gold_from_minions + gold_from_ward_kills + gold_from_events
        return total_gold

    def calculate_event_gold(self, player_name):
        base_player_name = player_name.split("#")[0]
        event_gold = 0

        for event in self.event_data:
            if event.get("Acer") == base_player_name and event["EventName"] == "Ace":
                event_gold += 150
                continue

            if event.get("KillerName") == base_player_name:
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
                if event["EventName"] == "DragonKill":
                    event_gold += 100
                elif event["EventName"] == "BaronKill":
                    event_gold += 200

        return event_gold

    def display_game_data(self, player_data, game_time, team_name, display_team_name):
        # Identify team and opposing team players
        team = [p for p in player_data if p['team'] == team_name]
        opposing_team = [p for p in player_data if p['team'] != team_name]

        # Calculate total gold for both teams
        self.ally_gold = int(sum(self.estimate_gold(player['summonerName'], player['scores'].get('creepScore', 0),
                                                    player['scores'].get('wardScore', 0), game_time) for player in
                                 team))
        self.enemy_gold = int(sum(self.estimate_gold(player['summonerName'], player['scores'].get('creepScore', 0),
                                                     player['scores'].get('wardScore', 0), game_time) for player in
                                  opposing_team))

        # Display stats for the selected team
        player_stats = [f"{display_team_name}: Total Gold: {self.ally_gold}"]
        for player in team:
            # Calculate estimated gold for each player
            estimated_gold = int(self.estimate_gold(player['summonerName'], player['scores'].get('creepScore', 0),
                                                    player['scores'].get('wardScore', 0), game_time))

            # Retrieve KDA stats
            kills = player['scores'].get('kills', 0)
            deaths = player['scores'].get('deaths', 0)
            assists = player['scores'].get('assists', 0)
            kda_score = f"{kills}/{deaths}/{assists}"

            # Format player stats
            stats = (f"{player['championName']} ({player['summonerName']}): "
                     f"KDA: {kda_score}, Estimated Gold: {estimated_gold}")
            player_stats.append(stats)

        # Determine gold difference and leading team
        self.gold_difference = abs(self.ally_gold - self.enemy_gold)
        self.leading_team = display_team_name if self.ally_gold > self.enemy_gold else (
            "Team CHAOS" if display_team_name == "Team ORDER" else "Team ORDER")

        # Update stats label with player stats
        self.stats_label.setText("\n".join(player_stats))

    def display_gold_difference(self):
        ally_team_name = "Team ORDER" if self.current_view_index == 0 else "Team CHAOS"
        enemy_team_name = "Team CHAOS" if ally_team_name == "Team ORDER" else "Team ORDER"

        if self.gold_difference == 0:
            gold_diff_text = (
                f"Gold Difference: {int(self.gold_difference)}\n"
                f"{ally_team_name} Gold: {int(self.ally_gold)}\n"
                f"{enemy_team_name} Gold: {int(self.enemy_gold)}"
            )
        else:
            gold_diff_text = (
                f"Gold Difference: {int(self.gold_difference)}\n"
                f"Leading Team: {self.leading_team}\n"
                f"{ally_team_name} Gold: {int(self.ally_gold)}\n"
                f"{enemy_team_name} Gold: {int(self.enemy_gold)}"
            )

        self.stats_label.setText(gold_diff_text)

    def display_win_percentage(self):
        # Prepare the input data for the model
        sample_input = self.prepare_model_input()

        # Scale the input data using the scaler
        sample_input_scaled = self.scaler.transform([sample_input])

        # Convert to tensor
        sample_input_tensor = torch.tensor(sample_input_scaled, dtype=torch.float32)

        # Predict the win percentage
        with torch.no_grad():
            prediction = self.model(sample_input_tensor)
            temperature = 3.0  # Adjust as needed
            predicted_probs = torch.softmax(prediction / temperature, dim=1)

        # Extract the win probabilities for Team ORDER and Team CHAOS
        team_100_prob = predicted_probs[0][1].item()  # Team ORDER win probability
        team_200_prob = predicted_probs[0][0].item()  # Team CHAOS win probability

        win_percentage_text = (
            f"Team ORDER Win: {team_100_prob * 100:.2f}%\n"
            f"Team CHAOS Win: {team_200_prob * 100:.2f}%"
        )

        self.stats_label.setText(win_percentage_text)



    def prepare_model_input(self):
        # Calculate statistics for Team ORDE
        if self.current_view_index == 0:  # Ally is ORDER
            team_order_gold = self.ally_gold
            team_chaos_gold = self.enemy_gold
        else:  # Ally is CHAOS
            team_order_gold = self.enemy_gold
            team_chaos_gold = self.ally_gold
        team_order_kills = sum(
            player['scores'].get('kills', 0) for player in self.player_data if player['team'] == 'ORDER')
        team_order_deaths = sum(
            player['scores'].get('deaths', 0) for player in self.player_data if player['team'] == 'ORDER')
        team_order_assists = sum(
            player['scores'].get('assists', 0) for player in self.player_data if player['team'] == 'ORDER')
        print(team_order_gold)
        team_order_cs = sum(
            player['scores'].get('creepScore', 0) for player in self.player_data if player['team'] == 'ORDER')
        team_order_kda = team_order_kills / (
            team_order_deaths if team_order_deaths > 0 else 1)  # Avoid division by zero

        team_chaos_kills = sum(
            player['scores'].get('kills', 0) for player in self.player_data if player['team'] == 'CHAOS')
        team_chaos_deaths = sum(
            player['scores'].get('deaths', 0) for player in self.player_data if player['team'] == 'CHAOS')
        team_chaos_assists = sum(
            player['scores'].get('assists', 0) for player in self.player_data if player['team'] == 'CHAOS')
        print(team_chaos_gold)
        team_chaos_cs = sum(
            player['scores'].get('creepScore', 0) for player in self.player_data if player['team'] == 'CHAOS')
        team_chaos_kda = team_chaos_kills / (
            team_chaos_deaths if team_chaos_deaths > 0 else 1)  # Avoid division by zero


        # Combine all the features into a single vector
        sample_input = [
            team_order_kills,
            team_order_deaths,
            team_order_assists,
            team_order_gold,
            team_order_cs,
            team_order_kda,
            team_chaos_kills,
            team_chaos_deaths,
            team_chaos_assists,
            team_chaos_gold,
            team_chaos_cs,
            team_chaos_kda
        ]

        return sample_input

    def switch_view(self):
        self.current_view_index = (self.current_view_index + 1) % len(self.views)

        # If switching to win_percentage view, force model evaluation
        if self.views[self.current_view_index] == "win_percentage":
            self.display_win_percentage()  # Re-trigger win percentage display

    def paintEvent(self, event):
        pass


if __name__ == '__main__':
    app = QApplication(sys.argv)
    overlay = Overlay()

    overlay.setGeometry(400, 0, 1200, 800)
    overlay.stats_label.setGeometry(50, 50, 1100, 205)

    overlay.show()
    sys.exit(app.exec_())

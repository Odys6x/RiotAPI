import sys
import json
import requests
import torch
import joblib
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import Qt, QTimer, QUrl
from PyQt5.QtWebEngineWidgets import QWebEngineView
from http.server import HTTPServer, SimpleHTTPRequestHandler
import threading


class DataHandler(SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/api/game-data':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()

            data = self.server.overlay_instance.get_current_game_data()
            self.wfile.write(json.dumps(data).encode())
            return

        # Serve your React build files
        if self.path == '/':
            self.path = '/build/index.html'
        elif not self.path.startswith('/build/'):
            self.path = f'/build{self.path}'

        return super().do_GET()


class Overlay(QWebEngineView):
    def __init__(self):
        super().__init__()

        # Set up window properties
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.WindowTransparentForInput)
        self.setAttribute(Qt.WA_TranslucentBackground)

        # URLs for fetching live data
        self.player_url = "https://127.0.0.1:2999/liveclientdata/playerlist"
        self.event_url = "https://127.0.0.1:2999/liveclientdata/eventdata"
        self.game_stats_url = "https://127.0.0.1:2999/liveclientdata/gamestats"

        # Initialize data storage
        self.player_data = []
        self.event_data = []
        self.ally_gold = 0
        self.enemy_gold = 0

        # Load ML model and scaler
        self.load_model()

        # Set up local server to serve React app
        self.setup_local_server()

        # Load the React application
        self.load_react_app()

        # Set up data update timer
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_data)
        self.timer.start(1000)  # Update every second

    def process_game_data(self, player_data, game_stats):
        """Process the game data for React component consumption"""
        if not player_data:
            return {}

        order_team = [p for p in player_data if p['team'] == 'ORDER']
        chaos_team = [p for p in player_data if p['team'] == 'CHAOS']

        # Calculate team stats
        order_stats = self.calculate_team_stats(order_team)
        chaos_stats = self.calculate_team_stats(chaos_team)

        # Calculate win probability if model is available
        win_probability = self.calculate_win_probability(order_stats, chaos_stats)

        game_time = game_stats.get('gameTime', 0)

        return {
            'orderTeam': {
                'gold': order_stats['total_gold'],
                'kills': order_stats['kills'],
                'deaths': order_stats['deaths'],
                'assists': order_stats['assists'],
                'cs': order_stats['cs'],
                'players': [{
                    'name': p['summonerName'],
                    'champion': p['championName'],
                    'kills': p['scores']['kills'],
                    'deaths': p['scores']['deaths'],
                    'assists': p['scores']['assists'],
                    'gold': self.estimate_gold(p['summonerName'],
                                               p['scores'].get('minionsKilled', 0),
                                               p['scores'].get('wardScore', 0),
                                               game_time),
                    'cs': p['scores'].get('minionsKilled', 0)
                } for p in order_team]
            },
            'chaosTeam': {
                'gold': chaos_stats['total_gold'],
                'kills': chaos_stats['kills'],
                'deaths': chaos_stats['deaths'],
                'assists': chaos_stats['assists'],
                'cs': chaos_stats['cs'],
                'players': [{
                    'name': p['summonerName'],
                    'champion': p['championName'],
                    'kills': p['scores']['kills'],
                    'deaths': p['scores']['deaths'],
                    'assists': p['scores']['assists'],
                    'gold': self.estimate_gold(p['summonerName'],
                                               p['scores'].get('minionsKilled', 0),
                                               p['scores'].get('wardScore', 0),
                                               game_time),
                    'cs': p['scores'].get('minionsKilled', 0)
                } for p in chaos_team]
            },
            'winProbability': win_probability,
            'gameTime': game_time
        }

    def calculate_team_stats(self, team):
        """Calculate aggregate stats for a team"""
        game_time = 0  # You might want to pass this from game_stats
        total_gold = sum(self.estimate_gold(p['summonerName'],
                                            p['scores'].get('minionsKilled', 0),
                                            p['scores'].get('wardScore', 0),
                                            game_time) for p in team)
        return {
            'total_gold': total_gold,
            'kills': sum(p['scores'].get('kills', 0) for p in team),
            'deaths': sum(p['scores'].get('deaths', 0) for p in team),
            'assists': sum(p['scores'].get('assists', 0) for p in team),
            'cs': sum(p['scores'].get('minionsKilled', 0) for p in team)
        }

    def calculate_win_probability(self, order_stats, chaos_stats):
        """Calculate win probability using the ML model"""
        if not self.model or not self.scaler:
            return {'order': 50, 'chaos': 50}

        input_data = [
            order_stats['kills'],
            order_stats['deaths'],
            order_stats['assists'],
            order_stats['total_gold'],
            order_stats['cs'],
            order_stats['kills'] / max(order_stats['deaths'], 1),  # KDA
            chaos_stats['kills'],
            chaos_stats['deaths'],
            chaos_stats['assists'],
            chaos_stats['total_gold'],
            chaos_stats['cs'],
            chaos_stats['kills'] / max(chaos_stats['deaths'], 1)  # KDA
        ]

        try:
            input_scaled = self.scaler.transform([input_data])
            input_tensor = torch.tensor(input_scaled, dtype=torch.float32)

            with torch.no_grad():
                prediction = self.model(input_tensor)
                probs = torch.softmax(prediction / 3.0, dim=1)  # Temperature scaling

            order_prob = probs[0][1].item() * 100
            chaos_prob = probs[0][0].item() * 100

            return {
                'order': round(order_prob, 1),
                'chaos': round(chaos_prob, 1)
            }
        except Exception as e:
            print(f"Error calculating win probability: {e}")
            return {'order': 50, 'chaos': 50}

    # Your existing methods remain the same...
    def load_model(self):
        try:
            state_dict = torch.load("model/model.pth", weights_only=True)
            from model import ComplexTabularModel
            self.model = ComplexTabularModel(input_dim=12)
            self.model.load_state_dict(state_dict)
            self.model.eval()
            self.scaler = joblib.load("model/scaler.pkl")
        except Exception as e:
            print(f"Error loading model: {e}")
            self.model = None
            self.scaler = None

    def setup_local_server(self):
        try:
            server = HTTPServer(('localhost', 8000), DataHandler)
            server.overlay_instance = self
            server_thread = threading.Thread(target=server.serve_forever)
            server_thread.daemon = True
            server_thread.start()
        except Exception as e:
            print(f"Error setting up server: {e}")

    def load_react_app(self):
        try:
            self.setUrl(QUrl("http://localhost:8000"))
            self.setGeometry(400, 0, 1200, 300)
        except Exception as e:
            print(f"Error loading React app: {e}")

    def update_data(self):
        try:
            self.player_data = self.fetch_player_data()
            game_stats = self.fetch_game_stats()
            self.event_data = self.fetch_event_data()

            if self.player_data and game_stats:
                processed_data = self.process_game_data(self.player_data, game_stats)
                self.page().runJavaScript(f"window.updateGameData({json.dumps(processed_data)})")

        except Exception as e:
            print(f"Error updating data: {e}")

    def fetch_player_data(self):
        try:
            response = requests.get(self.player_url, verify=False)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error fetching player data: {e}")
            return None

    def fetch_event_data(self):
        try:
            response = requests.get(self.event_url, verify=False)
            response.raise_for_status()
            data = response.json()
            return data.get("Events", [])
        except requests.exceptions.RequestException as e:
            print(f"Error fetching event data: {e}")
            return []

    def fetch_game_stats(self):
        try:
            response = requests.get(self.game_stats_url, verify=False)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error fetching game stats: {e}")
            return {}

    def estimate_gold(self, player_name, minions_killed, wards_killed, game_time):
        """Estimate player gold based on various factors"""
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
        return int(total_gold)

    def calculate_event_gold(self, player_name):
        """Calculate gold from game events"""
        base_player_name = player_name.split("#")[0]
        event_gold = 0

        for event in self.event_data:
            if event.get("Acer") == base_player_name and event["EventName"] == "Ace":
                event_gold += 150
            elif event.get("KillerName") == base_player_name:
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


if __name__ == '__main__':
    import urllib3

    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    app = QApplication(sys.argv)
    overlay = Overlay()
    overlay.show()
    sys.exit(app.exec_())
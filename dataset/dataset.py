import pandas as pd
import torch
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler, LabelEncoder


class LeaguePredictionPreprocessor:
    def __init__(self, match_data_path):
        """
        Initialize preprocessor for League win prediction

        Parameters:
        match_data_path (str): Path to match data CSV
        """
        self.match_data_path = match_data_path
        self.scaler = StandardScaler()
        self.label_encoder = LabelEncoder()

        # Features available during live game
        self.live_features = [
            'kills', 'deaths', 'assists',
            'total_damage_dealt', 'gold_earned',
            'cs', 'wards_placed', 'wards_killed',
            'dragon_kills', 'baron_kills', 'tower_kills'
        ]

    def load_data(self):
        """Load and prepare data, focusing on features available during live game"""
        df = pd.read_csv(self.match_data_path)

        # Select only features available during live game
        X = df[self.live_features]
        y = df['outcome']

        return X, y

    def preprocess(self, test_size=0.2, random_state=42):
        """Preprocess data for training"""
        X, y = self.load_data()

        # Encode target
        y_encoded = self.label_encoder.fit_transform(y)

        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X, y_encoded, test_size=test_size, random_state=random_state
        )

        # Scale features
        X_train_scaled = self.scaler.fit_transform(X_train)
        X_test_scaled = self.scaler.transform(X_test)

        # Convert to tensors
        X_train_tensor = torch.tensor(X_train_scaled, dtype=torch.float32)
        X_test_tensor = torch.tensor(X_test_scaled, dtype=torch.float32)
        y_train_tensor = torch.tensor(y_train, dtype=torch.float32)
        y_test_tensor = torch.tensor(y_test, dtype=torch.float32)

        return {
            'X_train': X_train_tensor,
            'X_test': X_test_tensor,
            'y_train': y_train_tensor,
            'y_test': y_test_tensor
        }

    def preprocess_live_data(self, live_stats):
        """
        Preprocess live game data for prediction

        Parameters:
        live_stats (dict): Dictionary containing current game stats
        """
        # Create DataFrame with same structure as training data
        live_df = pd.DataFrame([live_stats])[self.live_features]

        # Scale using same scaler as training data
        live_scaled = self.scaler.transform(live_df)

        # Convert to tensor
        return torch.tensor(live_scaled, dtype=torch.float32)

    def get_feature_names(self):
        """Return features used in the model"""
        return self.live_features



# # Example usage:
# if __name__ == "__main__":
#     preprocessor = LeaguePredictionPreprocessor("cleaned_match_results.csv.csv")
#
#     # Get processed training data
#     train_data = preprocessor.preprocess()
#
#     # Example of processing live data
#     live_game_stats = {
#         'kills': 5,
#         'deaths': 3,
#         'assists': 7,
#         'total_damage_dealt': 15000,
#         'gold_earned': 8000,
#         'cs': 150,
#         'wards_placed': 10,
#         'wards_killed': 2,
#         'dragon_kills': 1,
#         'baron_kills': 0,
#         'tower_kills': 2
#     }
#
#     live_tensor = preprocessor.preprocess_live_data(live_game_stats)

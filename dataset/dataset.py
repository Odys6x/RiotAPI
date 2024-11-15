import torch
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler, LabelEncoder


class AggregatedDataPreprocessor:
    def __init__(self, file_path):
        self.file_path = file_path
        self.scaler = StandardScaler()
        self.label_encoder = LabelEncoder()

        # Features from aggregated data
        self.features = [
            'kills', 'deaths', 'assists',
            'total_damage_dealt', 'gold_earned',
            'cs', 'KDA', 'Kill Participation'
        ]

    def prepare_data(self):
        # Load aggregated data
        df = pd.read_csv(self.file_path)

        # Separate features and target
        X = df[self.features]
        y = df['outcome']

        # Encode win/loss
        y_encoded = self.label_encoder.fit_transform(y)

        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X, y_encoded,
            test_size=0.2,
            random_state=42
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

    def get_feature_names(self):
        return self.features



preprocessor = AggregatedDataPreprocessor("team_aggregated_stats.csv")

processed_data = preprocessor.prepare_data()

# Extract the training and testing tensors
X_train = processed_data['X_train']
X_test = processed_data['X_test']
y_train = processed_data['y_train']
y_test = processed_data['y_test']

# Print the shapes
print(f"X_train shape: {X_train.shape}")
print(f"y_train shape: {y_train.shape}")
print(f"X_test shape: {X_test.shape}")
print(f"y_test shape: {y_test.shape}")


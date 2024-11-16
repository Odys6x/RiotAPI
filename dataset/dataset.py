import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler


class Preprocessor:
    def __init__(self, scaling=True):
        """
        Initialize the preprocessor with optional scaling.
        Args:
            scaling (bool): Whether to scale numerical features.
        """
        self.scaling = scaling
        self.scaler = StandardScaler() if scaling else None

    def load_data(self, file_path):
        """
        Load the data from a CSV file.
        Args:
            file_path (str): Path to the CSV file.
        Returns:
            pd.DataFrame: Loaded data.
        """
        self.data = pd.read_csv(file_path)
        return self.data

    def combine_team_stats(self):
        """
        Combine stats of both teams into one row per match.
        Returns:
            pd.DataFrame: Data with combined team stats.
        """
        combined_rows = []
        grouped = self.data.groupby("match_id")

        for match_id, group in grouped:
            # Check if both teams are present
            if not ((group['team_id'] == 100).any() and (group['team_id'] == 200).any()):
                print(f"Skipping match {match_id} due to missing teams")
                continue

            # Get rows for Team 100 and Team 200
            try:
                team_100 = group[group['team_id'] == 100].iloc[0]
                team_200 = group[group['team_id'] == 200].iloc[0]
            except IndexError as e:
                print(f"Skipping match {match_id}: {e}")
                continue

            # Combine into one row
            combined_row = {
                "match_id": match_id,
                # Team 100 stats
                "team_100_kills": team_100["kills"],
                "team_100_deaths": team_100["deaths"],
                "team_100_assists": team_100["assists"],
                "team_100_gold": team_100["gold_earned"],
                "team_100_cs": team_100["cs"],
                "team_100_kda": team_100["KDA"],
                "team_100_kp": team_100["Kill Participation"],
                # Team 200 stats
                "team_200_kills": team_200["kills"],
                "team_200_deaths": team_200["deaths"],
                "team_200_assists": team_200["assists"],
                "team_200_gold": team_200["gold_earned"],
                "team_200_cs": team_200["cs"],
                "team_200_kda": team_200["KDA"],
                "team_200_kp": team_200["Kill Participation"],
                # Outcome (1 if Team 100 wins, else 0)
                "outcome": 1 if team_100["outcome"] == "win" else 0,
            }
            combined_rows.append(combined_row)

        self.combined_data = pd.DataFrame(combined_rows)
        return self.combined_data

    def add_features(self):
        """
        Add custom features such as differences in stats between teams.
        Returns:
            pd.DataFrame: Data with added features.
        """
        self.combined_data["gold_diff"] = self.combined_data["team_100_gold"] - self.combined_data["team_200_gold"]
        self.combined_data["cs_diff"] = self.combined_data["team_100_cs"] - self.combined_data["team_200_cs"]
        self.combined_data["kda_diff"] = self.combined_data["team_100_kda"] - self.combined_data["team_200_kda"]
        return self.combined_data

    def split_data(self, test_size=0.15, val_size=0.15, random_state=42):
        """
        Split the data into train, validation, and test sets.
        Args:
            test_size (float): Proportion of data for testing.
            val_size (float): Proportion of training data for validation.
            random_state (int): Seed for reproducibility.
        Returns:
            Tuple: Train, validation, and test sets (X_train, X_val, X_test, y_train, y_val, y_test).
        """
        X = self.combined_data.drop(columns=["match_id", "outcome"])
        y = self.combined_data["outcome"]

        # Split into train/test
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=test_size, random_state=random_state)

        # Further split train into train/validation
        X_train, X_val, y_train, y_val = train_test_split(X_train, y_train, test_size=val_size,
                                                          random_state=random_state)

        # Scale features if enabled
        if self.scaling:
            X_train = self.scaler.fit_transform(X_train)
            X_val = self.scaler.transform(X_val)
            X_test = self.scaler.transform(X_test)

        return X_train, X_val, X_test, y_train, y_val, y_test

# Usage Example
# preprocessor = Preprocessor(scaling=True)
# raw_data = preprocessor.load_data("data.csv")
# combined_data = preprocessor.combine_team_stats()
# combined_data = preprocessor.add_features()
# X_train, X_val, X_test, y_train, y_val, y_test = preprocessor.split_data()

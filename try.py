import joblib
import numpy as np
import torch
from model import ComplexTabularModel
from train import input_dim

sample_team_100_stats = {
    "team_100_kills": 10,
    "team_100_deaths": 20,
    "team_100_assists": 25,
    "team_100_gold": 35000,
    "team_100_cs": 250,
    "team_100_kda": 1.75
}

sample_team_200_stats = {
    "team_200_kills": 20,
    "team_200_deaths": 10,
    "team_200_assists": 40,
    "team_200_gold": 48000,
    "team_200_cs": 300,
    "team_200_kda": 6
}


sample_input = np.array([[
    sample_team_100_stats["team_100_kills"],
    sample_team_100_stats["team_100_deaths"],
    sample_team_100_stats["team_100_assists"],
    sample_team_100_stats["team_100_gold"],
    sample_team_100_stats["team_100_cs"],
    sample_team_100_stats["team_100_kda"],
    sample_team_200_stats["team_200_kills"],
    sample_team_200_stats["team_200_deaths"],
    sample_team_200_stats["team_200_assists"],
    sample_team_200_stats["team_200_gold"],
    sample_team_200_stats["team_200_cs"],
    sample_team_200_stats["team_200_kda"]
]])

def time_based_temperature(game_time, max_temp=3.0, min_temp=1.0, max_time=10):
    if game_time >= max_time:
        return min_temp
    else:
        decay_ratio = game_time / max_time
        return max_temp - decay_ratio * (max_temp - min_temp)

try:
    scaler = joblib.load("model/scaler.pkl")
    sample_input_scaled = scaler.transform(sample_input)

    model = ComplexTabularModel(input_dim=input_dim)
    model.load_state_dict(torch.load("model/model.pth"))
    model.eval()

    sample_input_tensor = torch.tensor(sample_input_scaled, dtype=torch.float32)

    game_time = 25

    temperature = time_based_temperature(game_time)

    with torch.no_grad():
        prediction = model(sample_input_tensor)

        predicted_probs = torch.softmax(prediction / temperature, dim=1)
        predicted_label = torch.argmax(predicted_probs, dim=1).item()

    # Print results
    print("Prediction Results:")
    print(f"Predicted Winner: {'Team 100' if predicted_label == 1 else 'Team 200'}")
    print(f"Prediction Confidence: {predicted_probs[0][predicted_label]:.4f}")
    print(f"Full Probabilities: Team 200: {predicted_probs[0][0]:.4f}, Team 100: {predicted_probs[0][1]:.4f}")
    print(f"Current Temperature: {temperature:.2f}")

except Exception as e:
    print(f"Error during prediction: {e}")

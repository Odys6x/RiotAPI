import joblib
import numpy as np
import torch
from model import ComplexTabularModel
from train import input_dim

sample_team_100_stats = {
    "team_100_kills": 29,
    "team_100_deaths": 13,
    "team_100_assists": 20,
    "team_100_gold": 17720,
    "team_100_cs": 210,
    "team_100_kda": 2.23
}

sample_team_200_stats = {
    "team_200_kills": 13,
    "team_200_deaths": 30,
    "team_200_assists": 9,
    "team_200_gold": 17789,
    "team_200_cs": 110,
    "team_200_kda": 0.43
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

try:
    # Scale the input using the saved scaler
    scaler = joblib.load("model/scaler.pkl")  # Ensure scaler.pkl exists
    sample_input_scaled = scaler.transform(sample_input)

    # Load the trained model
    model = ComplexTabularModel(input_dim=input_dim)
    model.load_state_dict(torch.load("model/model.pth"))  # Ensure model.pth exists
    model.eval()  # Switch to evaluation mode

    # Convert to PyTorch tensor
    sample_input_tensor = torch.tensor(sample_input_scaled, dtype=torch.float32)

    # Make prediction with temperature scaling
    with torch.no_grad():
        prediction = model(sample_input_tensor)

        temperature = 3.0  # Adjust as needed
        predicted_probs = torch.softmax(prediction / temperature, dim=1)

        # Get predicted label
        predicted_label = torch.argmax(predicted_probs, dim=1).item()

    # Print results
    print("Prediction Results:")
    print(f"Predicted Winner: {'Team 100' if predicted_label == 1 else 'Team 200'}")
    print(f"Prediction Confidence: {predicted_probs[0][predicted_label]:.4f}")
    print(f"Full Probabilities: Team 200: {predicted_probs[0][0]:.4f}, Team 100: {predicted_probs[0][1]:.4f}")

except Exception as e:
    print(f"Error during prediction: {e}")

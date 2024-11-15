import torch.nn as nn
import torch
from config import Training, EPOCH, LR
from dataset.dataset import X_train, y_train, X_test, y_test
from model import SimpleTabularModel

# Initialize model
input_dim = X_train.shape[1]
model = SimpleTabularModel(input_dim)

if Training:
    # Loss and optimizer
    criterion = nn.CrossEntropyLoss()
    optimizer = torch.optim.Adam(model.parameters(), lr=LR)

    # Training loop
    for epoch in range(EPOCH):
        model.train()
        optimizer.zero_grad()

        # Forward pass
        y_pred = model(X_train).squeeze()
        loss = criterion(y_pred, y_train)

        # Backward pass
        loss.backward()
        optimizer.step()

        print(f"Epoch {epoch + 1}, Loss: {loss.item()}")

    # Save model after training
    torch.save(model.state_dict(), "model.pth")

else:
    # Load trained model for evaluation
    model.load_state_dict(torch.load("model.pth"))
    model.eval()

    # Evaluation
    with torch.no_grad():
        y_pred_test = model(X_test).squeeze()
        y_pred_labels = (y_pred_test > 0.5).float()  # Convert probabilities to binary labels

        accuracy = (y_pred_labels == y_test).float().mean()
        print(f"Test Accuracy: {accuracy.item() * 100:.2f}%")

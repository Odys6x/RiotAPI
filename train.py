from model import DeepModel,X_train_tensor,train_loader,test_loader,X_test_tensor,y_test_tensor
import torch.nn as nn
import torch
import torch.optim as optim
from config import Training

if Training == True:
    model = DeepModel(input_dim=X_train_tensor.shape[1])
    criterion = nn.BCELoss()
    optimizer = optim.Adam(model.parameters(), lr=0.001)


    num_epochs = 20
    for epoch in range(num_epochs):
        model.train()
        for X_batch, y_batch in train_loader:
            optimizer.zero_grad()
            y_pred = model(X_batch).squeeze()
            loss = criterion(y_pred, y_batch)
            loss.backward()
            optimizer.step()

        # Validation
        model.eval()
        with torch.no_grad():
            val_loss = sum(criterion(model(X_test_tensor).squeeze(), y_test_tensor) for _ in test_loader)
        print(f"Epoch {epoch + 1}/{num_epochs}, Loss: {loss.item()}, Validation Loss: {val_loss.item()}")

    print("Training complete.")

else:
    model = DeepModel(input_dim=X_train_tensor.shape[1])
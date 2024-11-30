import joblib
import torch
import torch.nn as nn
from torch.utils.data import DataLoader, TensorDataset
from sklearn.metrics import classification_report
from config import Training, EPOCH, LR, BATCH_SIZE
from dataset.dataset import Preprocessor
from model import ComplexTabularModel
from torch.optim.lr_scheduler import LambdaLR
from torch.cuda.amp import autocast, GradScaler
import torch_optimizer as optim

class FocalLoss(nn.Module):
    def __init__(self, alpha=1.0, gamma=2.0, reduction='mean'):
        super(FocalLoss, self).__init__()
        self.alpha = alpha
        self.gamma = gamma
        self.reduction = reduction

    def forward(self, inputs, targets):
        CE_loss = nn.CrossEntropyLoss(reduction='none')(inputs, targets)
        pt = torch.exp(-CE_loss)
        focal_loss = self.alpha * ((1 - pt) ** self.gamma) * CE_loss
        return focal_loss.mean() if self.reduction == 'mean' else focal_loss.sum()

preprocessor = Preprocessor(scaling=True)
raw_data = preprocessor.load_data("dataset/match_results_with_objectives.csv")
combined_data = preprocessor.combine_team_stats()
X_train, X_val, X_test, y_train, y_val, y_test = preprocessor.split_data()

X_train = torch.tensor(X_train, dtype=torch.float32)
y_train = torch.tensor(y_train.values, dtype=torch.long)
X_val = torch.tensor(X_val, dtype=torch.float32)
y_val = torch.tensor(y_val.values, dtype=torch.long)
X_test = torch.tensor(X_test, dtype=torch.float32)
y_test = torch.tensor(y_test.values, dtype=torch.long)

train_dataset = TensorDataset(X_train, y_train)
val_dataset = TensorDataset(X_val, y_val)
test_dataset = TensorDataset(X_test, y_test)

train_loader = DataLoader(train_dataset, batch_size=BATCH_SIZE, shuffle=True)
val_loader = DataLoader(val_dataset, batch_size=BATCH_SIZE)
test_loader = DataLoader(test_dataset, batch_size=BATCH_SIZE)

input_dim = X_train.shape[1]
model = ComplexTabularModel(input_dim)

criterion = FocalLoss(alpha=1.0, gamma=2.0)

optimizer = optim.RAdam(model.parameters(), lr=LR, weight_decay=1e-4)

scaler = GradScaler()

def warmup_lambda(epoch):
    if epoch < 5:
        return epoch / 5
    return 0.1 ** ((epoch - 5) // 10)

scheduler = LambdaLR(optimizer, lr_lambda=warmup_lambda)

if Training:
    patience = 5
    best_val_accuracy = 0
    early_stop_counter = 0

    for epoch in range(EPOCH):
        model.train()
        epoch_loss = 0
        for batch_X, batch_y in train_loader:
            optimizer.zero_grad()
            with autocast():
                y_pred = model(batch_X)
                loss = criterion(y_pred, batch_y)
            scaler.scale(loss).backward()
            scaler.step(optimizer)
            scaler.update()
            epoch_loss += loss.item()

        print(f"Epoch {epoch + 1}/{EPOCH}, Loss: {epoch_loss:.4f}")

        scheduler.step()
        print(f"Current Learning Rate: {scheduler.get_last_lr()}")

        model.eval()
        correct = 0
        total = 0
        with torch.no_grad():
            for batch_X, batch_y in val_loader:
                y_pred_eval = model(batch_X)
                y_pred_labels = torch.argmax(y_pred_eval, dim=1)
                correct += (y_pred_labels == batch_y).sum().item()
                total += batch_y.size(0)

        val_accuracy = correct / total * 100
        print(f"Validation Accuracy: {val_accuracy:.2f}%")

        if val_accuracy > best_val_accuracy:
            best_val_accuracy = val_accuracy
            early_stop_counter = 0
            torch.save(model.state_dict(), "model/best_model.pth")
            print("New best model saved.")
        else:
            early_stop_counter += 1
            print(f"No improvement. Early stopping counter: {early_stop_counter}/{patience}")

        if early_stop_counter >= patience:
            print("Early stopping triggered. Training stopped.")
            break

    joblib.dump(preprocessor.scaler, 'model/scaler.pkl')
    torch.save(model.state_dict(), "model/model.pth")
    print("Final model saved!")

else:
    model = ComplexTabularModel(input_dim=input_dim)
    model.load_state_dict(torch.load("model/model.pth"))
    model.eval()

    correct = 0
    total = 0
    y_pred_all = []
    y_test_all = []
    with torch.no_grad():
        for batch_X, batch_y in test_loader:
            y_pred_test = model(batch_X)
            y_pred_labels = torch.argmax(y_pred_test, dim=1)

            correct += (y_pred_labels == batch_y).sum().item()
            total += batch_y.size(0)
            y_pred_all.extend(y_pred_labels.cpu().numpy())
            y_test_all.extend(batch_y.cpu().numpy())

    test_accuracy = correct / total * 100
    print(f"Test Accuracy: {test_accuracy:.2f}%")

    print("\nClassification Report:")
    print(classification_report(y_test_all, y_pred_all, target_names=['Team 200 Wins', 'Team 100 Wins']))

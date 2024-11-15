import torch
import torch.nn as nn
from dataset.dataset import preprocessor
import torch.nn.functional as F


class SimpleTabularModel(nn.Module):
    def __init__(self, input_dim):
        super(SimpleTabularModel, self).__init__()
        self.fc1 = nn.Linear(input_dim, 64)
        self.fc2 = nn.Linear(64, 32)
        self.fc3 = nn.Linear(32, 2)


    def forward(self, x):
        x = F.relu(self.fc1(x))
        x = F.relu(self.fc2(x))
        x = F.softmax(self.fc3(x), dim=1)
        return x

input_dim = len(preprocessor.get_feature_names())
model = SimpleTabularModel(input_dim)


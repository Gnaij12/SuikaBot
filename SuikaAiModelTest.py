import torch
import torch.nn as nn
import torch.optim as optim
import torch.nn.functional as F
import os

from SuikAimodel import BATCH_SIZE

class Linear_QNet(nn.Module):
    def __init__(self, input_size, hidden_size, next_layer,output_size):
        super().__init__()
        self.linear1 = nn.Linear(input_size, hidden_size)
        self.linear2 = nn.Linear(hidden_size, next_layer)
        self.linear3 = nn.Linear(next_layer, output_size)
        #matrix nn initialization.
    def forward(self, x):
        x = F.relu(self.linear1(x))
        # x = self.linear2(x)
        x = F.relu(self.linear2(x))
        x = self.linear3(x)

        return x
        #return result of the nn
    def save(self, file_name='model.pth'):
        model_folder_path = './model'
        if not os.path.exists(model_folder_path):
            os.makedirs(model_folder_path)

        file_name = os.path.join(model_folder_path, file_name)
        torch.save(self.state_dict(), file_name)
    def load1(self, file_name='model.pth'):
        model_folder_path = './model'
        file_name = os.path.join(model_folder_path, file_name)
        # self = torch.load(file_name)
        self.load_state_dict(torch.load(file_name))
        # self = TheModelClass(*args, **kwargs)
        # self.load_state_dict(torch.load(file_name))
        # self.eval()

class QTrainer:
    def __init__(self, model, target, lr, gamma):
        self.lr = lr
        self.gamma = gamma
        self.model = model
        self.target = target
        self.optimizer = optim.Adam(model.parameters(), lr=self.lr)
        self.criterion = nn.MSELoss()

    def train_step(self, state, action, reward, next_state, done):
        state = torch.tensor(state, dtype=torch.float)
        next_state = torch.tensor(next_state, dtype=torch.float)
        action = torch.tensor(action, dtype=torch.long)
        reward = torch.tensor(reward, dtype=torch.float)
        # (n, x)

        if len(state.shape) == 1:
            # (1, x)
            state = torch.unsqueeze(state, 0)
            next_state = torch.unsqueeze(next_state, 0)
            action = torch.unsqueeze(action, 0)
            reward = torch.unsqueeze(reward, 0)
            done = (done, )

        # 1: predicted Q values with current state
        # pred = self.model(state)
        state_action_values = self.model(state).gather(1, action)


        # target = pred.clone()
        # for idx in range(len(done)):
        #     Q_new = reward[idx]
        #     if not done[idx]:
        #         Q_new = reward[idx] + self.gamma * torch.max(self.model(next_state[idx]))

        #     target[idx][torch.argmax(action[idx]).item()] = Q_new

        non_final_mask = torch.tensor(tuple(map(lambda s: s is not None,
                                        batch.next_state)), device=device, dtype=torch.bool)
        non_final_next_states = torch.cat([s for s in batch.next_state
                                                if s is not None])
        next_state_values = torch.zeros(BATCH_SIZE)
        with torch.no_grad():
            next_state_values[non_final_mask] = self.target(non_final_next_states).max(1).values
        # Compute the expected Q values
        expected_state_action_values = (next_state_values * self.gamma) + reward

        # Compute Huber loss
        # criterion = nn.SmoothL1Loss()
        loss = self.criterion(state_action_values, expected_state_action_values.unsqueeze(1))


        # 2: Q_new = r + y * max(next_predicted Q value) -> only do this if not done
        # pred.clone()
        # preds[argmax(action)] = Q_new
        self.optimizer.zero_grad()
        # loss = self.criterion(target, pred)
        loss.backward()

        self.optimizer.step()
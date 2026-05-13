"""DQN Agent for inventory optimization (lightweight numpy implementation)."""
import numpy as np
import json
import os
from collections import deque


class DQNAgent:
    """
    Deep Q-Network agent using a simple 2-layer neural network (numpy only).
    No PyTorch/TensorFlow dependency required.
    """

    def __init__(self, state_dim, action_dim, lr=0.0005, gamma=0.95, epsilon=1.0,
                 epsilon_min=0.02, epsilon_decay=0.99, batch_size=64, memory_size=10000):
        self.state_dim = state_dim
        self.action_dim = action_dim
        self.lr = lr
        self.gamma = gamma
        self.epsilon = epsilon
        self.epsilon_min = epsilon_min
        self.epsilon_decay = epsilon_decay
        self.batch_size = batch_size
        self.memory = deque(maxlen=memory_size)

        # Xavier initialization for better gradient flow
        # state_dim -> 128 -> 64 -> action_dim
        self.W1 = np.random.randn(state_dim, 128) * np.sqrt(2.0 / state_dim)
        self.b1 = np.zeros(128)
        self.W2 = np.random.randn(128, 64) * np.sqrt(2.0 / 128)
        self.b2 = np.zeros(64)
        self.W3 = np.random.randn(64, action_dim) * np.sqrt(2.0 / 64)
        self.b3 = np.zeros(action_dim)

    def _relu(self, x):
        return np.maximum(0, x)

    def _forward(self, state):
        """Forward pass through the Q-network."""
        h1 = self._relu(state @ self.W1 + self.b1)
        h2 = self._relu(h1 @ self.W2 + self.b2)
        q_values = h2 @ self.W3 + self.b3
        return q_values, h1, h2

    def select_action(self, state):
        """Epsilon-greedy action selection."""
        if np.random.random() < self.epsilon:
            return np.random.randint(self.action_dim)
        q_values, _, _ = self._forward(state)
        return int(np.argmax(q_values))

    def store(self, state, action, reward, next_state, done):
        """Store experience in replay memory."""
        self.memory.append((state, action, reward, next_state, done))

    def train_step(self):
        """Sample a batch and update the network."""
        if len(self.memory) < self.batch_size:
            return 0.0

        # Sample batch
        indices = np.random.choice(len(self.memory), self.batch_size, replace=False)
        batch = [self.memory[i] for i in indices]

        states = np.array([b[0] for b in batch])
        actions = np.array([b[1] for b in batch])
        rewards = np.array([b[2] for b in batch])
        next_states = np.array([b[3] for b in batch])
        dones = np.array([b[4] for b in batch], dtype=float)

        # Compute target Q-values
        next_q, _, _ = self._forward(next_states)
        targets = rewards + self.gamma * np.max(next_q, axis=1) * (1 - dones)

        # Compute current Q-values
        q_values, h1, h2 = self._forward(states)
        q_actions = q_values[np.arange(self.batch_size), actions]

        # TD error
        td_error = targets - q_actions
        loss = np.mean(td_error ** 2)

        # Backprop through network (manual gradient descent)
        # Gradient of loss w.r.t. output
        dq = np.zeros_like(q_values)
        dq[np.arange(self.batch_size), actions] = -2 * td_error / self.batch_size

        # Layer 3
        dW3 = h2.T @ dq
        db3 = np.sum(dq, axis=0)

        # Layer 2
        dh2 = dq @ self.W3.T
        dh2[h2 <= 0] = 0  # ReLU gradient

        dW2 = h1.T @ dh2
        db2 = np.sum(dh2, axis=0)

        # Layer 1
        dh1 = dh2 @ self.W2.T
        dh1[h1 <= 0] = 0

        dW1 = states.T @ dh1
        db1 = np.sum(dh1, axis=0)

        # Gradient clipping
        for g in [dW1, db1, dW2, db2, dW3, db3]:
            np.clip(g, -1.0, 1.0, out=g)

        # Update weights
        self.W1 -= self.lr * dW1
        self.b1 -= self.lr * db1
        self.W2 -= self.lr * dW2
        self.b2 -= self.lr * db2
        self.W3 -= self.lr * dW3
        self.b3 -= self.lr * db3

        # Decay epsilon
        self.epsilon = max(self.epsilon_min, self.epsilon * self.epsilon_decay)

        return loss

    def save(self, path):
        """Save model weights to a JSON file."""
        data = {
            "W1": self.W1.tolist(), "b1": self.b1.tolist(),
            "W2": self.W2.tolist(), "b2": self.b2.tolist(),
            "W3": self.W3.tolist(), "b3": self.b3.tolist(),
            "epsilon": self.epsilon,
        }
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w") as f:
            json.dump(data, f)

    def load(self, path):
        """Load model weights from a JSON file."""
        with open(path) as f:
            data = json.load(f)
        self.W1 = np.array(data["W1"])
        self.b1 = np.array(data["b1"])
        self.W2 = np.array(data["W2"])
        self.b2 = np.array(data["b2"])
        self.W3 = np.array(data["W3"])
        self.b3 = np.array(data["b3"])
        self.epsilon = data.get("epsilon", self.epsilon_min)

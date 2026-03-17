import torch
import torch.nn as nn
from torch.distributions.categorical import Categorical
import numpy as np


def layer_init(layer, std=np.sqrt(2), bias_const=0.0):
    torch.nn.init.orthogonal_(layer.weight, std)
    torch.nn.init.constant_(layer.bias, bias_const)
    return layer


class ResidualBlock(nn.Module):
    """Pre-norm residual block: x + MLP(LayerNorm(x))"""
    def __init__(self, hidden_dim: int):
        super().__init__()
        self.net = nn.Sequential(
            nn.LayerNorm(hidden_dim),
            layer_init(nn.Linear(hidden_dim, hidden_dim)),
            nn.ReLU(),
            layer_init(nn.Linear(hidden_dim, hidden_dim)),
            nn.ReLU(),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return x + self.net(x)


class Agent(nn.Module):
    """
    PPO Actor-Critic with shared ResidualMLP trunk.
    Architecture: Embed(LayerNorm+ReLU) -> 3x ResidualBlock -> separate Actor/Critic heads.
    """
    def __init__(self, obs_dim: int, action_dim: int = 200, hidden_dim: int = 512, num_res_blocks: int = 3):
        super(Agent, self).__init__()

        # Embedding layer normalizes raw observations of different scales
        self.embed = nn.Sequential(
            layer_init(nn.Linear(obs_dim, hidden_dim)),
            nn.LayerNorm(hidden_dim),
            nn.ReLU(),
        )

        # Shared trunk with residual connections for stable deep gradient flow
        self.shared_trunk = nn.Sequential(
            *[ResidualBlock(hidden_dim) for _ in range(num_res_blocks)]
        )

        # Separate heads — actor uses small init std for initial uniform-ish policy
        self.actor_head = nn.Sequential(
            nn.LayerNorm(hidden_dim),
            layer_init(nn.Linear(hidden_dim, hidden_dim)),
            nn.ReLU(),
            layer_init(nn.Linear(hidden_dim, action_dim), std=0.01),
        )

        self.critic_head = nn.Sequential(
            nn.LayerNorm(hidden_dim),
            layer_init(nn.Linear(hidden_dim, hidden_dim)),
            nn.ReLU(),
            layer_init(nn.Linear(hidden_dim, 1), std=1.0),
        )

    def _shared_features(self, x: torch.Tensor) -> torch.Tensor:
        return self.shared_trunk(self.embed(x))

    def get_value(self, x: torch.Tensor) -> torch.Tensor:
        return self.critic_head(self._shared_features(x))

    def get_action_and_value(self, x: torch.Tensor, action_mask: torch.Tensor, action: torch.Tensor = None):
        features = self._shared_features(x)
        logits = self.actor_head(features)

        # Invalid actions get logits of -1e8 so softmax drives their probability to ~0
        huge_negative = torch.tensor(-1e8, dtype=logits.dtype, device=logits.device)
        masked_logits = torch.where(action_mask > 0.5, logits, huge_negative)

        probs = Categorical(logits=masked_logits)

        if action is None:
            action = probs.sample()

        return action, probs.log_prob(action), probs.entropy(), self.critic_head(features)

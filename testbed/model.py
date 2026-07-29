"""GPU QoE ensemble trained on the published subjective dataset."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import torch
from torch import nn


class QoENet(nn.Module):
    def __init__(self, width: int = 96):
        super().__init__()
        self.network = nn.Sequential(
            nn.Linear(13, width),
            nn.SiLU(),
            nn.Dropout(0.08),
            nn.Linear(width, width),
            nn.SiLU(),
            nn.Linear(width, 2),
        )

    def forward(self, x: torch.Tensor) -> tuple[torch.Tensor, torch.Tensor]:
        output = self.network(x)
        mean = 1.0 + 4.0 * torch.sigmoid(output[:, 0])
        log_variance = torch.clamp(output[:, 1], -5.0, 2.0)
        return mean, log_variance


@dataclass
class Standardizer:
    mean: np.ndarray
    scale: np.ndarray

    @classmethod
    def fit(cls, x: np.ndarray) -> "Standardizer":
        scale = x.std(axis=0)
        scale[scale < 1e-8] = 1.0
        return cls(x.mean(axis=0), scale)

    def transform(self, x: np.ndarray) -> np.ndarray:
        return (x - self.mean) / self.scale


class DeepEnsemble:
    def __init__(self, models: list[QoENet], scaler: Standardizer, device: str):
        self.models = models
        self.scaler = scaler
        self.device = device

    @torch.inference_mode()
    def predict(self, x: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
        tensor = torch.as_tensor(
            self.scaler.transform(np.asarray(x)),
            dtype=torch.float32,
            device=self.device,
        )
        means = []
        aleatoric = []
        for model in self.models:
            model.eval()
            mean, log_variance = model(tensor)
            means.append(mean)
            aleatoric.append(torch.exp(log_variance))
        stacked = torch.stack(means)
        predictive_mean = stacked.mean(dim=0)
        predictive_variance = stacked.var(dim=0, unbiased=False)
        predictive_variance += torch.stack(aleatoric).mean(dim=0)
        return (
            predictive_mean.cpu().numpy(),
            torch.sqrt(predictive_variance).cpu().numpy(),
        )


def train_ensemble(
    x_train: np.ndarray,
    y_train: np.ndarray,
    y_variance: np.ndarray,
    *,
    ensemble_size: int,
    epochs: int,
    width: int,
    learning_rate: float,
    weight_decay: float,
    seed: int,
    device: str,
) -> DeepEnsemble:
    scaler = Standardizer.fit(x_train)
    x_tensor = torch.as_tensor(
        scaler.transform(x_train), dtype=torch.float32, device=device
    )
    y_tensor = torch.as_tensor(y_train, dtype=torch.float32, device=device)
    variance_tensor = torch.as_tensor(
        np.maximum(y_variance, 0.02), dtype=torch.float32, device=device
    )
    models = []
    for member in range(ensemble_size):
        torch.manual_seed(seed + member)
        np.random.seed(seed + member)
        model = QoENet(width).to(device)
        optimizer = torch.optim.AdamW(
            model.parameters(), lr=learning_rate, weight_decay=weight_decay
        )
        generator = torch.Generator(device=device).manual_seed(seed + 10_000 + member)
        for _ in range(epochs):
            indices = torch.randint(
                0, len(x_tensor), (len(x_tensor),), generator=generator, device=device
            )
            mean, log_variance = model(x_tensor[indices])
            # The subjective variance prevents overconfidence on disputed stimuli.
            target_variance = variance_tensor[indices]
            effective_variance = torch.exp(log_variance) + target_variance
            loss = 0.5 * (
                torch.log(effective_variance)
                + (y_tensor[indices] - mean).square() / effective_variance
            ).mean()
            optimizer.zero_grad(set_to_none=True)
            loss.backward()
            optimizer.step()
        models.append(model)
    return DeepEnsemble(models, scaler, device)


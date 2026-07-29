"""Static and online regime-conditional conformal lower bounds."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np


def conformal_quantile(residuals: np.ndarray, alpha: float) -> float:
    values = np.sort(np.asarray(residuals, dtype=float))
    if len(values) == 0:
        return 0.5
    rank = int(np.ceil((len(values) + 1) * (1 - alpha))) - 1
    return float(values[np.clip(rank, 0, len(values) - 1)])


@dataclass
class AdaptiveConformal:
    buckets: dict[int, list[float]]
    alpha: float = 0.10
    window: int = 120
    adaptive: bool = True
    alpha_state: dict[int, float] | None = None
    gamma: float = 0.02

    @classmethod
    def fit(
        cls,
        residuals: np.ndarray,
        groups: np.ndarray,
        *,
        alpha: float,
        window: int,
        adaptive: bool = True,
    ) -> "AdaptiveConformal":
        buckets = {
                int(group): list(np.asarray(residuals)[groups == group])
                for group in np.unique(groups)
            }
        return cls(
            buckets=buckets,
            alpha=alpha,
            window=window,
            adaptive=adaptive,
            alpha_state={group: alpha for group in buckets},
        )

    def radius(self, groups: np.ndarray) -> np.ndarray:
        fallback = np.concatenate(
            [np.asarray(values) for values in self.buckets.values() if values]
        )
        radii = []
        for group in groups:
            values = np.asarray(self.buckets.get(int(group), fallback.tolist()))
            level = (self.alpha_state or {}).get(int(group), self.alpha)
            radii.append(conformal_quantile(values, level))
        return np.asarray(radii)

    def update(self, groups: np.ndarray, residuals: np.ndarray) -> None:
        if not self.adaptive:
            return
        for group, residual in zip(groups, residuals):
            key = int(group)
            if key not in self.buckets:
                # Hierarchical cold start: a new operational regime inherits
                # the pooled calibration history rather than forming a
                # spuriously narrow interval from its first observation.
                pooled = [
                    value
                    for values in self.buckets.values()
                    for value in values
                ]
                self.buckets[key] = pooled[-self.window :]
                if self.alpha_state is not None:
                    self.alpha_state[key] = self.alpha
            values = self.buckets[key]
            level = (self.alpha_state or {}).get(key, self.alpha)
            radius = conformal_quantile(np.asarray(values), level)
            error = float(residual > radius)
            if self.alpha_state is not None:
                # Practical, clipped ACI feedback. The clipping is useful for
                # finite replay but means we report empirical coverage rather
                # than transferring the unmodified ACI theorem.
                self.alpha_state[key] = float(
                    np.clip(level + self.gamma * (self.alpha - error), 0.005, 0.50)
                )
            values.append(float(residual))
            if len(values) > self.window:
                del values[:-self.window]

"""Finite-catalogue objective calibration and exact recovery allocation.

No legacy subjective model is loaded. Test labels are kept outside the policy
interface. The joint score controls catalogue-wide quality and ordered-pair
shortfall-gain errors at the source-ID-panel level, under exchangeability.
"""

from __future__ import annotations

import csv
import hashlib
import itertools
import math
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

import numpy as np

CONTROLLERS = (
    "quality_nash", "bounded_nash", "quality_debt", "bounded_quality_debt",
    "uncertified_recovery", "certified_recovery", "memoryless_recovery", "max_min",
)
LADDER = np.array([0.045373, 0.088482, 0.252988, 0.368912, 0.987061, 3.792491])


def quality_index(psnr: np.ndarray) -> np.ndarray:
    return 1 + 4 * np.clip((np.asarray(psnr) - 18) / 24, 0, 1)


def shortfall(quality: np.ndarray, target: float = 4.0) -> np.ndarray:
    return np.maximum(target - np.asarray(quality), 0)


def subject_partition(subjects: list[int]) -> dict[str, list[int]]:
    if len(set(subjects)) != 28:
        raise ValueError("v1 protocol requires exactly 28 distinct source IDs")
    ordered = sorted(set(subjects), key=lambda sid: hashlib.sha256(f"recovery-v1-{sid}".encode()).digest())
    return {"train": ordered[:10], "calibration": ordered[10:19], "test": ordered[19:]}


def finite_quantile(scores: np.ndarray, alpha: float = 0.1) -> tuple[float, int, bool]:
    values = np.asarray(scores, dtype=float)
    if values.ndim != 1 or not len(values) or not np.all(np.isfinite(values)) or np.any(values < 0):
        raise ValueError("finite nonnegative calibration scores required")
    if not 0 < alpha < 1:
        raise ValueError("alpha must be between zero and one")
    rank = math.ceil((len(values) + 1) * (1 - alpha))
    if rank > len(values):
        # Quality error <=4; ordered H-gain error <=2*(target-1)=6.
        return 6.0, rank, True
    return float(np.sort(values)[rank - 1]), rank, False


@dataclass
class Catalogue:
    subjects: list[int]
    contexts: list[tuple[str, int]]
    quality: np.ndarray  # source ID x content/segment x representation
    psnr: np.ndarray
    ssim: np.ndarray
    sizes: np.ndarray  # content/segment x representation

    @classmethod
    def load(cls, root: Path) -> "Catalogue":
        with (root / "viewport_quality.csv").open(encoding="utf-8") as handle:
            rows = list(csv.DictReader(handle))
        subjects = sorted({int(row["subject"]) for row in rows})
        contexts = sorted({(row["content"], int(row["segment"])) for row in rows})
        shape = (len(subjects), len(contexts), len(LADDER))
        psnr, ssim = np.full(shape, np.nan), np.full(shape, np.nan)
        subject_lookup = {sid: i for i, sid in enumerate(subjects)}
        context_lookup = {key: i for i, key in enumerate(contexts)}
        for row in rows:
            key = (subject_lookup[int(row["subject"])], context_lookup[(row["content"], int(row["segment"]))], int(row["ladder_index"]))
            if np.isfinite(psnr[key]):
                raise ValueError(f"duplicate quality key: {key}")
            psnr[key], ssim[key] = float(row["vw_psnr_db"]), float(row["vw_ssim"])
        sizes = np.full(shape[1:], np.nan)
        with (root / "segment_sizes.csv").open(encoding="utf-8") as handle:
            for row in csv.DictReader(handle):
                key = (context_lookup[(row["content"], int(row["segment"]))], int(row["ladder_index"]))
                if np.isfinite(sizes[key]):
                    raise ValueError(f"duplicate size key: {key}")
                sizes[key] = int(row["bytes"])
        if (not np.all(np.isfinite(psnr)) or not np.all(np.isfinite(ssim))
                or not np.all(np.isfinite(sizes)) or np.any(sizes <= 0)):
            raise ValueError("incomplete or invalid catalogue")
        return cls(subjects, contexts, quality_index(psnr), psnr, ssim, sizes)


@dataclass
class ObjectiveModel:
    mean: np.ndarray
    radius: float
    partition: dict[str, list[int]]
    scores: list[float]
    rank: int
    trivial_bound: bool
    target: float = 4.0

    @classmethod
    def fit(cls, catalogue: Catalogue, alpha: float = 0.1) -> "ObjectiveModel":
        partition = subject_partition(catalogue.subjects)
        lookup = {sid: i for i, sid in enumerate(catalogue.subjects)}
        train = catalogue.quality[[lookup[sid] for sid in partition["train"]]]
        calibration = catalogue.quality[[lookup[sid] for sid in partition["calibration"]]]
        mean = train.mean(axis=0)
        quality_score = np.max(np.abs(calibration - mean), axis=(1, 2))
        errors = shortfall(mean)[None, :, :] - shortfall(calibration)
        gain_score = np.max(np.ptp(errors, axis=2), axis=1)
        scores = np.maximum(quality_score, gain_score)
        radius, rank, trivial = finite_quantile(scores, alpha)
        return cls(mean, radius, partition, scores.tolist(), rank, trivial)

    def panel_coverage(self, catalogue: Catalogue) -> list[dict]:
        results = []
        for sid in self.partition["test"]:
            actual = catalogue.quality[catalogue.subjects.index(sid)]
            q_error = float(np.max(np.abs(actual - self.mean)))
            h_error = shortfall(self.mean) - shortfall(actual)
            g_error = float(np.max(np.ptp(h_error, axis=1)))
            results.append({"subject": sid, "quality_max_error": q_error,
                            "gain_max_error": g_error, "covered": max(q_error, g_error) <= self.radius + 1e-12})
        return results


@lru_cache(maxsize=8)
def all_actions(users: int, levels: int = 6) -> np.ndarray:
    if not 1 <= users <= 6:
        raise ValueError("exact pilot enumeration supports 1--6 users only")
    actions = np.asarray(list(itertools.product(range(levels), repeat=users)), dtype=np.int16)
    actions.flags.writeable = False
    return actions


def recovery_terms(mean: np.ndarray, radius: float, debt: np.ndarray, target: float = 4.0) -> tuple[np.ndarray, np.ndarray]:
    predicted_gain = shortfall(mean[:, :1], target) - shortfall(mean, target)
    lower_gain = predicted_gain - radius
    # Only strictly positive values certify improvement; zero is abstention.
    credit = np.minimum(np.asarray(debt)[:, None], np.maximum(lower_gain, 0))
    return lower_gain, credit


def select_action(
    controller: str, mean: np.ndarray, radius: float, costs: np.ndarray,
    budget_bytes: float, debt: np.ndarray, last_shortfall: np.ndarray,
    previous: np.ndarray, switch_weight: float = 0.08,
) -> tuple[np.ndarray, dict]:
    """Policy inputs contain predictions/state only, never held-out labels."""
    if controller not in CONTROLLERS:
        raise ValueError(controller)
    mean, costs = np.asarray(mean, float), np.asarray(costs, float)
    users, levels = mean.shape
    if (costs.shape != mean.shape or levels != len(LADDER) or not np.all(np.isfinite(mean))
            or not np.all(np.isfinite(costs)) or np.any(costs <= 0)
            or np.any(mean < 1) or np.any(mean > 5) or not np.isfinite(radius) or radius < 0):
        raise ValueError("invalid policy table")
    actions = all_actions(users, levels)
    total_bytes = costs[np.arange(users), actions].sum(axis=1)
    keep = total_bytes <= budget_bytes + 1e-8
    actions, total_bytes = actions[keep], total_bytes[keep]
    if not len(actions):
        raise ValueError("no feasible allocation: explicit admission failure")
    state = np.asarray(last_shortfall if controller == "memoryless_recovery" else debt, float)
    if state.shape != (users,) or np.any(state < 0) or not np.all(np.isfinite(state)):
        raise ValueError("invalid debt state")
    lower = np.maximum(1, mean - radius)
    base = mean if controller in {"quality_nash", "quality_debt", "max_min"} else lower
    scores_per_user = np.log(base)
    weights = state / (1 + state.mean())
    lower_gain, credit = recovery_terms(mean, radius, state)
    if controller in {"quality_debt", "bounded_quality_debt"}:
        scores_per_user += weights[:, None] * base
    elif controller in {"uncertified_recovery", "certified_recovery", "memoryless_recovery"}:
        if controller == "uncertified_recovery":
            lower_gain, credit = recovery_terms(mean, 0.0, state)
        scores_per_user += weights[:, None] * credit
    score = scores_per_user[np.arange(users), actions].sum(axis=1)
    switch = np.abs(np.log((LADDER[actions] + 0.05) / (LADDER[np.asarray(previous)] + 0.05))).mean(axis=1)
    score -= switch_weight * switch
    if controller == "max_min":
        qualities = mean[np.arange(users), actions]
        selected = np.lexsort((np.arange(len(actions)), total_bytes, -qualities.mean(axis=1), -qualities.min(axis=1)))[0]
    else:
        ties = np.flatnonzero(np.abs(score - score.max()) <= 1e-12)
        selected = ties[np.argmin(total_bytes[ties])]
    chosen = actions[selected].copy()
    return chosen, {
        "objective": float(score[selected]), "candidate_count": len(actions),
        "total_bytes": float(total_bytes[selected]),
        "lower": lower[np.arange(users), chosen],
        "mean": mean[np.arange(users), chosen],
        "gain_lower": lower_gain[np.arange(users), chosen],
        "credit": credit[np.arange(users), chosen],
    }

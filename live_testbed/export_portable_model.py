"""Train the published-data QoE ensemble and export NumPy-compatible weights.

The exported artifact is intentionally framework-neutral.  Training uses the
RTX through PyTorch; Mininet inference uses only NumPy inside WSL.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import torch
import yaml

TESTBED = Path(__file__).resolve().parents[1] / "testbed"
sys.path.insert(0, str(TESTBED))

from model import train_ensemble  # noqa: E402
from run_experiment import load_dataset, split_dataset  # noqa: E402


def _linear_layers(model):
    return [layer for layer in model.network if isinstance(layer, torch.nn.Linear)]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, default=TESTBED / "config.yaml")
    parser.add_argument(
        "--data", type=Path, default=TESTBED / "data" / "published_qoe.csv"
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path(__file__).resolve().parent / "artifacts" / "qoe_ensemble.json",
    )
    args = parser.parse_args()

    config = yaml.safe_load(args.config.read_text(encoding="utf-8"))
    seed = int(config["seed"])
    x, y, y_var, groups = load_dataset(args.data)
    train, calibration, test = split_dataset(x, y, y_var, groups, seed)
    device = "cuda" if torch.cuda.is_available() else "cpu"
    predictor_cfg = config["predictor"]

    ensemble = train_ensemble(
        x[train],
        y[train],
        y_var[train],
        ensemble_size=int(predictor_cfg["ensemble_size"]),
        epochs=int(predictor_cfg["epochs"]),
        width=int(predictor_cfg["hidden_width"]),
        learning_rate=float(predictor_cfg["learning_rate"]),
        weight_decay=float(predictor_cfg["weight_decay"]),
        seed=seed,
        device=device,
    )
    cal_prediction, _ = ensemble.predict(x[calibration])
    residuals = np.maximum(cal_prediction - y[calibration], 0.0)

    members = []
    for model in ensemble.models:
        layers = _linear_layers(model)
        members.append(
            {
                "weights": [layer.weight.detach().cpu().tolist() for layer in layers],
                "biases": [layer.bias.detach().cpu().tolist() for layer in layers],
            }
        )

    sample = x[test[: min(16, len(test))]]
    sample_mean, sample_std = ensemble.predict(sample)
    payload = {
        "format": "credo360-portable-ensemble-v1",
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "training_device": device,
        "cuda_device": torch.cuda.get_device_name(0) if device == "cuda" else None,
        "seed": seed,
        "software": {
            "python": sys.version.split()[0],
            "torch": torch.__version__,
            "numpy": np.__version__,
        },
        "inputs": {
            "dataset": str(args.data.resolve()),
            "dataset_sha256": hashlib.sha256(args.data.read_bytes()).hexdigest(),
            "config": str(args.config.resolve()),
            "config_sha256": hashlib.sha256(args.config.read_bytes()).hexdigest(),
        },
        "feature_count": int(x.shape[1]),
        "scaler_mean": ensemble.scaler.mean.tolist(),
        "scaler_scale": ensemble.scaler.scale.tolist(),
        "members": members,
        "calibration": {
            "alpha": float(config["experiment"]["conformal_alpha"]),
            "one_sided_residuals": residuals.tolist(),
        },
        "template_median": np.median(x[train], axis=0).tolist(),
        "ladder_mbps": config["experiment"]["bitrate_ladder_mbps"],
        "self_check": {
            "features": sample.tolist(),
            "mean": sample_mean.tolist(),
            "std": sample_std.tolist(),
            "max_tolerance": 2e-5,
        },
        "split_sizes": {
            "train": int(len(train)),
            "calibration": int(len(calibration)),
            "held_out": int(len(test)),
        },
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload), encoding="utf-8")
    print(
        json.dumps(
            {
                "output": str(args.output),
                "device": device,
                "cuda_device": payload["cuda_device"],
                "members": len(members),
                "bytes": args.output.stat().st_size,
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()

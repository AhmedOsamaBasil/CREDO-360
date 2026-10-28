"""Deterministic scalar metric mappings of already exposed quality labels."""
import csv
from decimal import Decimal, localcontext, ROUND_HALF_UP
import gzip
import json
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
FOLDERS = {"v2": "feasibility_recovery/data/v2", "v3": "horizon_recovery/data/v3"}
METRICS = ("index", "fine_index", "psnr_db", "negative_mse")
SCALES = (1000, 1000000, 1000000, 1000000)
INPUTS = tuple(f"{f}/{n}" for f in FOLDERS.values()
               for n in ("calibration_quality.csv", "heldout_quality.csv")) + (
    "causal_playback/data/media_manifest.json",
    "early_commitment/results/development_v1/results.json.gz",
    "feedback_opportunity/results/audit_v1/results.json.gz",
)


def metric_values(value):
    with localcontext() as context:
        context.prec = 40
        q = Decimal(value)
        if not q.is_finite():
            raise ValueError("Finite PSNR required")
        bounded = min(Decimal(5), max(Decimal(1), 1 + (q - 18) / 6))
        raw = (bounded, bounded, q, -Decimal(65025) * Decimal(10) ** (-q / 10))
        return tuple(int((v * s).to_integral_value(rounding=ROUND_HALF_UP))
                     for v, s in zip(raw, SCALES))


def load(root=ROOT):
    labels = {}
    for cohort, folder in FOLDERS.items():
        for name in ("calibration_quality.csv", "heldout_quality.csv"):
            with (root / folder / name).open(newline="", encoding="utf-8") as stream:
                for row in csv.DictReader(stream):
                    key = (cohort, row["content"], int(row["subject"]), int(row["segment"]), int(row["ladder_index"]))
                    if key in labels:
                        raise ValueError("Duplicate metric label")
                    labels[key] = metric_values(row["vw_psnr_db"])
    if len(labels) != 6 * 28 * 6 * 6:
        raise ValueError("Unexpected exposed label count")
    manifest = json.loads((root / INPUTS[4]).read_text(encoding="utf-8"))
    sizes = {(r["cohort"], r["scene"], r["segment"], r["rung"]): r["bytes"] for r in manifest["files"]}
    with gzip.open(root / INPUTS[5], "rt", encoding="utf-8") as stream:
        saved = json.load(stream)
    with gzip.open(root / INPUTS[6], "rt", encoding="utf-8") as stream:
        old = json.load(stream)
    paths = {}
    for row in saved["rows"]:
        if row["delay"] == .08:
            paths.setdefault(row["key"], {})[row["policy"]] = row
    records = []
    for key, policies in sorted(paths.items()):
        cohort, scene, recipient, donor = key.split(":")
        quality = np.array([[[labels[cohort, scene, int(u), t, r] for r in range(6)]
                             for u in (recipient, donor)] for t in range(6)], dtype=np.int64)
        quality = np.moveaxis(quality, -1, 0)  # metric, segment, user, rung
        costs = np.array([[sizes[cohort, scene, t, r] for r in range(6)] for t in range(6)], dtype=np.int64)
        if len(policies) != 8:
            raise ValueError("Eight frozen primary policies required")
        records.append({"key": key, "cohort": cohort, "scene": scene,
                        "quality": quality, "costs": costs, "policies": policies,
                        "reserve": int(2 * costs[2:, 2].sum())})
    if len(records) != 168:
        raise ValueError("168 exposed directed episodes required")
    return records, {r["key"]: r for r in old["frontier"]}

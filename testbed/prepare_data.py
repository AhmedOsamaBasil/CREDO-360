"""Prepare published subjective QoE data and PCAP-derived replay traces.

The script reads the public artefacts from Ahmed Osama Basil's PhD repository.
It does not redistribute video or packet captures. Only compact, derived CSV
files and provenance hashes are written to this testbed.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path

import numpy as np
from scipy.io import loadmat
from scapy.utils import PcapReader


FEATURE_NAMES = [
    "BufferLength",
    "BitrateDownloading",
    "IndexDownloading",
    "CurrentIndex",
    "MaxIndex",
    "DropedFrames",  # Source spelling retained for provenance.
    "MinimumLatency",
    "AverageLatency",
    "MaxLatency",
    "MinimumDownload",
    "AverageDownload",
    "MaxDownload",
    "Resolution",
]


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def prepare_qoe(mat_path: Path, output_dir: Path) -> dict:
    data = loadmat(mat_path)
    features = np.asarray(data["input"], dtype=np.float64)
    ratings = np.asarray(data["target"][:, 13:], dtype=np.float64)
    keep = ratings.sum(axis=1) > 0
    features = features[keep]
    ratings = ratings[keep]
    if features.shape != (170, 13) or ratings.shape != (170, 36):
        raise ValueError(
            f"Unexpected published-data shapes: {features.shape}, {ratings.shape}"
        )
    # Unique response vectors identify the subjective stimulus/question profile.
    _, stimulus_group = np.unique(ratings, axis=0, return_inverse=True)

    output_dir.mkdir(parents=True, exist_ok=True)
    qoe_csv = output_dir / "published_qoe.csv"
    fieldnames = (
        ["row_id", "stimulus_group", "mos_mean", "mos_std"]
        + FEATURE_NAMES
        + [f"rater_{index + 1:02d}" for index in range(ratings.shape[1])]
    )
    with qoe_csv.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for index, (row, scores) in enumerate(zip(features, ratings)):
            record = {
                "row_id": index,
                "stimulus_group": int(stimulus_group[index]),
                "mos_mean": float(scores.mean()),
                "mos_std": float(scores.std(ddof=1)),
            }
            record.update(dict(zip(FEATURE_NAMES, map(float, row))))
            record.update(
                {
                    f"rater_{rater + 1:02d}": int(score)
                    for rater, score in enumerate(scores)
                }
            )
            writer.writerow(record)
    return {
        "source": str(mat_path),
        "source_sha256": sha256(mat_path),
        "output": str(qoe_csv),
        "rows": len(features),
        "features": features.shape[1],
        "raters": ratings.shape[1],
        "stimulus_groups": int(stimulus_group.max() + 1),
        "feature_name_note": (
            "Names were recovered from the exported MATLAB classifiers' "
            "RequiredVariables, the paper's Table 6, DASH player metric order, "
            "and numeric range/correlation checks. Source spelling "
            "'DropedFrames' is retained. Resolution stores the selected "
            "representation bandwidth in bps in this workspace."
        ),
    }


def pcap_to_trace(path: Path, bin_seconds: float = 1.0) -> tuple[np.ndarray, np.ndarray]:
    """Return elapsed seconds and observed traffic Mbps for non-empty bins."""
    first_time = None
    bins: dict[int, int] = {}
    with PcapReader(str(path)) as reader:
        for packet in reader:
            timestamp = float(packet.time)
            if first_time is None:
                first_time = timestamp
            index = int((timestamp - first_time) // bin_seconds)
            bins[index] = bins.get(index, 0) + len(packet)
    if not bins:
        return np.empty(0), np.empty(0)
    last = max(bins)
    seconds = np.arange(last + 1, dtype=float) * bin_seconds
    mbps = np.array([bins.get(i, 0) * 8 / bin_seconds / 1e6 for i in range(last + 1)])
    return seconds, mbps


def prepare_traces(repo_root: Path, output_dir: Path) -> list[dict]:
    trace_dir = output_dir / "traces"
    trace_dir.mkdir(parents=True, exist_ok=True)
    metadata = []
    candidates = sorted(repo_root.rglob("*_out.pcap"))
    for index, source in enumerate(candidates):
        seconds, mbps = pcap_to_trace(source)
        active = mbps[mbps > 0]
        if len(seconds) < 20 or len(active) < 10:
            continue
        safe_name = f"trace_{index:03d}.csv"
        destination = trace_dir / safe_name
        with destination.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.writer(handle)
            writer.writerow(["time_s", "observed_traffic_mbps"])
            writer.writerows(zip(seconds, mbps))
        metadata.append(
            {
                "trace": safe_name,
                "source_relative": str(source.relative_to(repo_root)),
                "source_sha256": sha256(source),
                "bins": len(seconds),
                "mean_active_mbps": float(active.mean()),
                "p10_active_mbps": float(np.quantile(active, 0.10)),
                "p90_active_mbps": float(np.quantile(active, 0.90)),
            }
        )
    (output_dir / "trace_metadata.json").write_text(
        json.dumps(metadata, indent=2), encoding="utf-8"
    )
    return metadata


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--phd-repo", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    mat_path = (
        args.phd_repo
        / "Collected Data (Used for Training and Validation)"
        / "matlab.mat"
    )
    qoe_meta = prepare_qoe(mat_path, args.output)
    traces_meta = prepare_traces(args.phd_repo, args.output)
    provenance = {
        "repository": "https://github.com/AhmedOsamaBasil/PhD",
        "qoe": qoe_meta,
        "pcap_traces": len(traces_meta),
        "trace_caveat": (
            "PCAP-derived series measure observed traffic on captured switch "
            "interfaces. They are replay signals, not direct estimates of latent "
            "link capacity. Final experiments should add independent public "
            "capacity traces and a live controlled network."
        ),
    }
    (args.output / "provenance.json").write_text(
        json.dumps(provenance, indent=2), encoding="utf-8"
    )
    print(json.dumps(provenance, indent=2))


if __name__ == "__main__":
    main()

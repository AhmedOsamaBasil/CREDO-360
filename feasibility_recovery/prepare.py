"""Prepare new content once; calibration and held-out HMD labels stay separate."""
from __future__ import annotations
import argparse
import json
import subprocess
from pathlib import Path
import numpy as np
from multimedia_testbed.prepare_qoevave import (
    download, load_traces, encode_rendition, decoded_frames, tile_mse, tile_ssim,
    viewport_scores, segment_sizes, write_csv, sha256, LADDER_MBPS,
)
from feasibility_recovery.core import partition

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(__doc__)
    parser.add_argument("--output", type=Path, default=ROOT / "feasibility_recovery/data/v2")
    parser.add_argument("--external", type=Path, default=ROOT / ".external/feasibility_v2")
    args = parser.parse_args()
    if args.output.exists() and any(args.output.iterdir()):
        parser.error("output nonempty; frozen data must not be overwritten")
    manifest_path = ROOT / "feasibility_recovery/manifest.json"
    manifest = json.loads(manifest_path.read_text())
    old = json.loads((ROOT / "multimedia_testbed/qoevave_manifest.json").read_text())
    if set(old["contents"]) & set(manifest["contents"]):
        raise ValueError("fresh scenes overlap historical six-scene catalogue")
    rows = {"calibration": [], "test": []}
    sender, sizes, provenance = [], [], []
    split = None
    # A failed partial run leaves no published derived directory; source cache is resumable.
    for content, spec in manifest["contents"].items():
        source = args.external / "media" / f"{content}.mp4"
        traces_path = args.external / "traces" / f"{content}.zip"
        download(spec["media_url"], source)
        download(spec["trace_url"], traces_path)
        traces = load_traces(traces_path)
        current_split = partition(list(traces))
        if split is not None and current_split != split:
            raise ValueError("source-ID panels differ between scenes")
        split = current_split
        reference = decoded_frames(source, 60)
        if len(reference) != 60:
            raise ValueError("requires 60 full one-second source samples")
        if any(t["time"][-1] < 59.5 for t in traces.values()):
            raise ValueError("trace does not span the full analysis window")
        area = np.cos(np.deg2rad(np.linspace(75, -75, 6)))[:, None] * np.ones((1, 12))
        area /= area.sum()
        entry = {"content": content, "source_sha256": sha256(source), "trace_sha256": sha256(traces_path),
                 "source_bytes": source.stat().st_size, "subjects": sorted(traces), "rendition_sha256": []}
        for level, rate in enumerate(LADDER_MBPS):
            rendition = args.external / "renditions" / content / f"rep_{level}.mp4"
            encode_rendition(source, rendition, float(rate), 60)
            distorted = decoded_frames(rendition, 60)
            if len(distorted) != 60:
                raise ValueError("incomplete encoded analysis window")
            mse, ssim = tile_mse(reference, distorted), tile_ssim(reference, distorted)
            global_mse = (mse * area).sum(axis=(1, 2)).reshape(6, 10).mean(axis=1)
            global_psnr = 10 * np.log10(255 ** 2 / np.maximum(global_mse, 1e-12))
            for segment, size in enumerate(segment_sizes(rendition, 60)):
                sizes.append({"content": content, "segment": segment, "ladder_index": level, "bytes": size})
                sender.append({"content": content, "segment": segment, "ladder_index": level,
                               "full_sphere_psnr_db": float(global_psnr[segment])})
            for sid, trace in traces.items():
                group = "calibration" if sid in split["calibration"] else "test"
                psnrs, ssims = viewport_scores(mse, ssim, trace, 60)
                for segment, (psnr, ssim_value) in enumerate(zip(psnrs, ssims)):
                    rows[group].append({"content": content, "subject": sid, "segment": segment,
                                        "ladder_index": level, "vw_psnr_db": psnr, "vw_ssim": ssim_value})
            entry["rendition_sha256"].append(sha256(rendition))
            print(f"prepared {content} representation {level + 1}/6 (outcomes not summarized)", flush=True)
        provenance.append(entry)
    args.output.mkdir(parents=True, exist_ok=False)
    for name, values in [("calibration_quality.csv", rows["calibration"]), ("heldout_quality.csv", rows["test"]),
                         ("sender_quality.csv", sender), ("segment_sizes.csv", sizes)]:
        write_csv(args.output / name, list(values[0]), values)
    (args.output / "split.json").write_text(json.dumps(split, indent=2) + "\n")
    metadata = {"format": "feasibility-data-v2", "content_holdout": True, "new_participants": False,
                "sources": provenance, "manifest_sha256": sha256(manifest_path),
                "preparation_sources_sha256": {p: sha256(ROOT / p) for p in
                    ["feasibility_recovery/prepare.py", "feasibility_recovery/core.py",
                     "multimedia_testbed/prepare_qoevave.py"]},
                "ffmpeg": subprocess.check_output(["ffmpeg", "-version"], text=True).splitlines()[0],
                "gpu": subprocess.check_output(["nvidia-smi", "--query-gpu=name,driver_version", "--format=csv,noheader"], text=True).strip(),
                "resolution_encode": [1920, 960], "resolution_analysis": [960, 480], "sample_fps": 1,
                "segment_seconds": 10, "segments": 6, "metric": "tile-center viewport approximation; objective, not MOS",
                "result_sha256": {p.name: sha256(p) for p in args.output.iterdir() if p.is_file()}}
    (args.output / "metadata.json").write_text(json.dumps(metadata, indent=2) + "\n")
    print(f"saved new derived data to {args.output}; held-out outcomes not summarized", flush=True)


if __name__ == "__main__":
    main()

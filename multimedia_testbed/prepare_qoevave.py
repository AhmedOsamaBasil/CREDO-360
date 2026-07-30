"""Prepare independent 360-degree content and held-out viewport outcomes.

The script deliberately keeps third-party media outside Git. It verifies the
source assets, creates six reproducible H.264 representations, measures
P.910-style spatial/temporal information, and combines tile-level distortion
with public HMD traces to produce viewport-weighted PSNR (VW-PSNR).
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import shutil
import subprocess
import urllib.request
import zipfile
from pathlib import Path

import numpy as np

LADDER_MBPS = np.array(
    [0.045373, 0.088482, 0.252988, 0.368912, 0.987061, 3.792491],
    dtype=float,
)
WIDTH, HEIGHT = 960, 480
TILE_COLUMNS, TILE_ROWS = 12, 6
SEGMENT_S = 10
SAMPLE_FPS = 1
FOV_WIDTH_DEG = 100.0
FOV_HEIGHT_DEG = 100.0


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def subject_split(subject: int) -> str:
    """Stable user-disjoint split; no trace from one user crosses the split."""
    token = hashlib.sha256(f"qoevave-subject-{subject}".encode()).digest()[0]
    return "calibration" if token < 85 else "test"


def run(command: list[str], *, capture: bool = False) -> str:
    result = subprocess.run(
        command,
        check=True,
        text=capture,
        stdout=subprocess.PIPE if capture else None,
    )
    return result.stdout if capture else ""


def download(url: str, path: Path) -> None:
    if path.exists():
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    partial = path.with_suffix(path.suffix + ".partial")
    urllib.request.urlretrieve(url, partial)
    partial.replace(path)


def load_traces(archive_path: Path) -> dict[int, dict[str, np.ndarray]]:
    traces: dict[int, dict[str, np.ndarray]] = {}
    with zipfile.ZipFile(archive_path) as archive:
        for name in archive.namelist():
            if not name.endswith(".json"):
                continue
            subject = int(Path(name).name.split("_", 1)[0])
            payload = json.loads(archive.read(name))
            series = payload["data"][0]["pitch_yaw_roll_data_hmd"]
            time = np.asarray([row["sec"] for row in series], dtype=float)
            time -= time[0]
            traces[subject] = {
                "time": time,
                "yaw": np.asarray([row["yaw"] for row in series], dtype=float),
                "pitch": np.asarray(
                    [row["pitch"] for row in series], dtype=float
                ),
            }
    if not traces:
        raise ValueError(f"No traces found in {archive_path}")
    return traces


def encode_rendition(
    source: Path, output: Path, bitrate_mbps: float, duration_s: int
) -> None:
    if output.exists():
        return
    output.parent.mkdir(parents=True, exist_ok=True)
    bitrate = max(20, int(round(1000 * bitrate_mbps)))
    run(
        [
            "ffmpeg",
            "-hide_banner",
            "-loglevel",
            "error",
            "-y",
            "-t",
            str(duration_s),
            "-i",
            str(source),
            "-an",
            "-vf",
            "scale=1920:960:flags=lanczos,fps=30",
            "-c:v",
            "h264_nvenc",
            "-preset",
            "p5",
            "-tune",
            "hq",
            "-rc",
            "vbr",
            "-b:v",
            f"{bitrate}k",
            "-maxrate",
            f"{2 * bitrate}k",
            "-bufsize",
            f"{4 * bitrate}k",
            "-g",
            "60",
            "-keyint_min",
            "60",
            "-pix_fmt",
            "yuv420p",
            "-movflags",
            "+faststart",
            str(output),
        ]
    )


def decoded_frames(path: Path, duration_s: int) -> np.ndarray:
    command = [
        "ffmpeg",
        "-hide_banner",
        "-loglevel",
        "error",
        "-t",
        str(duration_s),
        "-i",
        str(path),
        "-an",
        "-vf",
        f"fps={SAMPLE_FPS},scale={WIDTH}:{HEIGHT}:flags=lanczos,format=gray",
        "-f",
        "rawvideo",
        "-pix_fmt",
        "gray",
        "pipe:1",
    ]
    result = subprocess.run(command, check=True, stdout=subprocess.PIPE)
    pixels = np.frombuffer(result.stdout, dtype=np.uint8)
    frame_size = WIDTH * HEIGHT
    if len(pixels) % frame_size:
        raise RuntimeError(f"Incomplete raw frame stream from {path}")
    return pixels.reshape(-1, HEIGHT, WIDTH).astype(np.float32)


def si_ti(frames: np.ndarray) -> tuple[float, float]:
    """P.910-style maximum framewise Sobel SI and difference-frame TI."""
    spatial = []
    for frame in frames:
        gx = (
            frame[:-2, 2:]
            + 2 * frame[1:-1, 2:]
            + frame[2:, 2:]
            - frame[:-2, :-2]
            - 2 * frame[1:-1, :-2]
            - frame[2:, :-2]
        )
        gy = (
            frame[2:, :-2]
            + 2 * frame[2:, 1:-1]
            + frame[2:, 2:]
            - frame[:-2, :-2]
            - 2 * frame[:-2, 1:-1]
            - frame[:-2, 2:]
        )
        spatial.append(float(np.std(np.hypot(gx, gy))))
    temporal = [
        float(np.std(frames[index] - frames[index - 1]))
        for index in range(1, len(frames))
    ]
    return max(spatial), max(temporal)


def tile_mse(reference: np.ndarray, distorted: np.ndarray) -> np.ndarray:
    count = min(len(reference), len(distorted))
    squared = (reference[:count] - distorted[:count]) ** 2
    tile_height = HEIGHT // TILE_ROWS
    tile_width = WIDTH // TILE_COLUMNS
    return squared.reshape(
        count,
        TILE_ROWS,
        tile_height,
        TILE_COLUMNS,
        tile_width,
    ).mean(axis=(2, 4))


def viewport_weights(yaw: float, pitch: float) -> np.ndarray:
    yaw_centres = np.linspace(
        -180 + 180 / TILE_COLUMNS,
        180 - 180 / TILE_COLUMNS,
        TILE_COLUMNS,
    )
    pitch_centres = np.linspace(
        90 - 90 / TILE_ROWS,
        -90 + 90 / TILE_ROWS,
        TILE_ROWS,
    )
    yaw_distance = np.abs(
        ((yaw_centres[None, :] - yaw + 180) % 360) - 180
    )
    pitch_distance = np.abs(pitch_centres[:, None] - pitch)
    mask = (yaw_distance <= FOV_WIDTH_DEG / 2) & (
        pitch_distance <= FOV_HEIGHT_DEG / 2
    )
    weights = mask * np.cos(np.deg2rad(pitch_centres[:, None]))
    if not weights.any():
        weights.flat[
            np.argmin(yaw_distance + pitch_distance)
        ] = 1.0
    return weights / weights.sum()


def viewport_psnr(
    mse: np.ndarray, trace: dict[str, np.ndarray], duration_s: int
) -> list[float]:
    frame_times = np.arange(len(mse), dtype=float) + 0.5
    indices = np.searchsorted(trace["time"], frame_times, side="left")
    indices = np.clip(indices, 0, len(trace["time"]) - 1)
    weighted = []
    for frame_index, trace_index in enumerate(indices):
        weights = viewport_weights(
            float(trace["yaw"][trace_index]),
            float(trace["pitch"][trace_index]),
        )
        weighted.append(float(np.sum(mse[frame_index] * weights)))
    segment_scores = []
    for start in range(0, duration_s, SEGMENT_S):
        values = weighted[start : start + SEGMENT_S]
        mean_mse = max(float(np.mean(values)), 1e-12)
        segment_scores.append(10 * math.log10(255.0**2 / mean_mse))
    return segment_scores


def segment_sizes(path: Path, duration_s: int) -> list[int]:
    output = run(
        [
            "ffprobe",
            "-v",
            "error",
            "-select_streams",
            "v:0",
            "-show_entries",
            "packet=pts_time,size",
            "-of",
            "csv=p=0",
            str(path),
        ],
        capture=True,
    )
    sizes = [0] * math.ceil(duration_s / SEGMENT_S)
    for line in output.splitlines():
        values = line.split(",")
        if len(values) < 2:
            continue
        timestamp, size = float(values[0]), int(values[1])
        index = min(int(timestamp // SEGMENT_S), len(sizes) - 1)
        if index >= 0:
            sizes[index] += size
    return sizes


def write_csv(path: Path, fieldnames: list[str], rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--manifest",
        type=Path,
        default=Path(__file__).with_name("qoevave_manifest.json"),
    )
    parser.add_argument(
        "--external-root",
        type=Path,
        default=Path(".external/qoevave"),
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("multimedia_testbed/artifacts/qoevave"),
    )
    args = parser.parse_args()
    if not shutil.which("ffmpeg") or not shutil.which("ffprobe"):
        parser.error("ffmpeg and ffprobe are required")

    manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
    quality_rows, size_rows, content_rows, split_rows = [], [], [], []
    args.output.mkdir(parents=True, exist_ok=True)
    for content, specification in manifest["contents"].items():
        source = args.external_root / "media" / f"{content}.mp4"
        archive = args.external_root / "traces" / f"{content}.zip"
        download(specification["media_url"], source)
        download(specification["trace_url"], archive)
        duration_s = int(specification["duration_s"])
        traces = load_traces(archive)
        for subject in sorted(traces):
            split_rows.append(
                {
                    "content": content,
                    "subject": subject,
                    "split": subject_split(subject),
                }
            )

        reference = decoded_frames(source, duration_s)
        si, ti = si_ti(reference)
        content_rows.append(
            {
                "content": content,
                "spatial_information": si,
                "temporal_information": ti,
                "source_sha256": sha256(source),
                "trace_sha256": sha256(archive),
                "subjects": len(traces),
                "test_subjects": sum(
                    subject_split(subject) == "test" for subject in traces
                ),
            }
        )
        for ladder_index, bitrate in enumerate(LADDER_MBPS):
            rendition = (
                args.external_root
                / "renditions"
                / content
                / f"rep_{ladder_index}_{bitrate:.6f}mbps.mp4"
            )
            encode_rendition(source, rendition, float(bitrate), duration_s)
            distorted = decoded_frames(rendition, duration_s)
            mse = tile_mse(reference, distorted)
            for segment, size in enumerate(segment_sizes(rendition, duration_s)):
                size_rows.append(
                    {
                        "content": content,
                        "segment": segment,
                        "ladder_index": ladder_index,
                        "bitrate_mbps": bitrate,
                        "bytes": size,
                    }
                )
            for subject, trace in traces.items():
                scores = viewport_psnr(mse, trace, duration_s)
                for segment, score in enumerate(scores):
                    quality_rows.append(
                        {
                            "content": content,
                            "subject": subject,
                            "split": subject_split(subject),
                            "segment": segment,
                            "ladder_index": ladder_index,
                            "bitrate_mbps": bitrate,
                            "vw_psnr_db": score,
                        }
                    )
            print(
                f"prepared {content} representation {ladder_index + 1}/"
                f"{len(LADDER_MBPS)}",
                flush=True,
            )

    # Complexity labels are empirical ranks over the declared three-sequence set.
    si_values = np.asarray(
        [float(row["spatial_information"]) for row in content_rows]
    )
    ti_values = np.asarray(
        [float(row["temporal_information"]) for row in content_rows]
    )
    composite = (si_values - si_values.mean()) / max(si_values.std(), 1e-9)
    composite += (ti_values - ti_values.mean()) / max(ti_values.std(), 1e-9)
    labels = ["low", "medium", "high"]
    for rank, index in enumerate(np.argsort(composite)):
        content_rows[int(index)]["relative_complexity"] = labels[rank]
        content_rows[int(index)]["complexity_score"] = float(composite[index])

    write_csv(
        args.output / "content_metrics.csv",
        list(content_rows[0]),
        content_rows,
    )
    write_csv(
        args.output / "subject_split.csv",
        list(split_rows[0]),
        split_rows,
    )
    write_csv(
        args.output / "segment_sizes.csv",
        list(size_rows[0]),
        size_rows,
    )
    write_csv(
        args.output / "viewport_quality.csv",
        list(quality_rows[0]),
        quality_rows,
    )
    metadata = {
        "format": "credo360-qoevave-v1",
        "manifest": args.manifest.name,
        "contents": list(manifest["contents"]),
        "ladder_mbps": LADDER_MBPS.tolist(),
        "analysis_resolution": [WIDTH, HEIGHT],
        "sample_fps": SAMPLE_FPS,
        "segment_duration_s": SEGMENT_S,
        "tile_grid": [TILE_COLUMNS, TILE_ROWS],
        "viewport_fov_degrees": [FOV_WIDTH_DEG, FOV_HEIGHT_DEG],
        "viewport_metric": (
            "luma PSNR from per-frame equirectangular tile MSE, weighted by "
            "the measured HMD viewport and spherical tile area"
        ),
        "split_rule": (
            "SHA-256(qoevave-subject-ID)[0] < 85 is calibration; all other "
            "subjects are held-out test"
        ),
        "perceptual_claim": "objective metric only; not subjective MOS",
    }
    (args.output / "metadata.json").write_text(
        json.dumps(metadata, indent=2), encoding="utf-8"
    )


if __name__ == "__main__":
    main()

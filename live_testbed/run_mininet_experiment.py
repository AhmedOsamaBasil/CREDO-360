"""Concurrent real-segment DASH experiment over a Mininet shared bottleneck."""

from __future__ import annotations

import argparse
import csv
import json
import os
import shlex
import signal
import time
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
from mininet.link import TCLink
from mininet.log import setLogLevel
from mininet.net import Mininet
from mininet.node import OVSBridge

from portable_qoe import (
    PortableEnsemble,
    build_features,
    conformal_radius,
    select_action,
)

LADDER_BPS = [45373, 88482, 252988, 368912, 987061, 3792491]
SEGMENT_DURATION_S = 10.0
DEFAULT_CONTROLLERS = [
    "mean_greedy",
    "proportional_fair",
    "uncertainty_nash",
    "conformal_nash",
    "conformal_debt_ungated",
    "risk_debt",
]
REGIMES = ("stable", "bursty", "shift")


def make_capacity_profile(
    regime: str, epochs: int, rng: np.random.Generator
) -> list[float]:
    """Generate a deterministic paired bottleneck profile for one seed."""
    if regime == "stable":
        noise = np.zeros(epochs)
        for index in range(epochs):
            innovation = rng.normal(0, 0.22)
            noise[index] = innovation if index == 0 else 0.65 * noise[index - 1] + innovation
        profile = 2.8 + noise
    elif regime == "bursty":
        low = rng.uniform(1.25, 1.85, epochs)
        high = rng.uniform(3.1, 4.4, epochs)
        state = rng.integers(0, 2)
        values = []
        for index in range(epochs):
            if index and rng.random() < 0.55:
                state = 1 - state
            values.append(high[index] if state else low[index])
        profile = np.asarray(values)
    elif regime == "shift":
        midpoint = max(1, epochs // 2)
        profile = np.concatenate(
            [
                rng.normal(3.45, 0.30, midpoint),
                rng.normal(1.55, 0.18, epochs - midpoint),
            ]
        )
    else:
        raise ValueError(f"Unknown capacity regime: {regime}")
    return np.round(np.clip(profile, 1.2, 4.5), 3).tolist()


def counterbalanced_order(controllers: list[str], index: int) -> list[str]:
    """Cyclic Latin-square order: each controller occupies every position."""
    if not controllers:
        return []
    shift = index % len(controllers)
    return controllers[shift:] + controllers[:shift]


def locate_media(explicit: Path | None) -> Path:
    candidates = [
        explicit,
        Path(__file__).resolve().parents[3]
        / "work"
        / "source-phd"
        / "PhD-main"
        / "Segments",
    ]
    for candidate in candidates:
        if candidate and (candidate / "bunny_45373bps").is_dir():
            return candidate.resolve()
    raise FileNotFoundError("DASH media root not found; pass --media-root")


def set_shared_rate(host, interface: str, capacity_mbps: float) -> None:
    # The interface lives in the server's network namespace, so tc must be
    # invoked through the Mininet host rather than the root WSL namespace.
    result = host.cmd(
        f"tc qdisc replace dev {shlex.quote(interface)} root "
        f"tbf rate {capacity_mbps:.3f}mbit burst 64kb latency 400ms; echo $?"
    ).strip()
    if result.splitlines()[-1] != "0":
        raise RuntimeError(f"Failed to shape {interface}: {result}")


def download_one(host, url: str):
    command = (
        "curl --silent --show-error --connect-timeout 5 --max-time 160 "
        "--output /dev/null "
        "--write-out '%{size_download},%{time_total},%{time_starttransfer},"
        "%{speed_download},%{http_code}' "
        + shlex.quote(url)
    )
    return host.popen(command, shell=True, text=True, stdout=-1, stderr=-1)


def main() -> None:
    if os.geteuid() != 0:
        raise SystemExit("Run with sudo; Mininet requires root.")
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", type=Path, required=True)
    parser.add_argument("--media-root", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument(
        "--controllers",
        nargs="+",
        default=DEFAULT_CONTROLLERS,
        choices=DEFAULT_CONTROLLERS,
    )
    parser.add_argument("--users", type=int, default=5)
    parser.add_argument("--epochs", type=int, default=8)
    parser.add_argument(
        "--warmup-epochs",
        type=int,
        default=1,
        help="Paired warm-up epochs retained in raw logs but excluded from inference.",
    )
    parser.add_argument("--seed", type=int, default=20260728)
    parser.add_argument(
        "--seeds",
        type=int,
        default=1,
        help="Number of consecutive paired seeds in the live campaign.",
    )
    parser.add_argument(
        "--regimes",
        nargs="+",
        default=list(REGIMES),
        choices=REGIMES,
        help="Capacity regimes assigned cyclically across paired seeds.",
    )
    parser.add_argument(
        "--fixed-order",
        action="store_true",
        help="Disable cyclic controller-order counterbalancing.",
    )
    parser.add_argument(
        "--resume",
        action="store_true",
        help="Retain complete seed/controller pairs and resume an interrupted campaign.",
    )
    parser.add_argument(
        "--target-qoe",
        type=float,
        default=4.0,
        help="Declared live operational-QoE floor used by the debt queue.",
    )
    parser.add_argument("--debt-weight", type=float, default=1.0)
    parser.add_argument("--debt-decay", type=float, default=0.90)
    parser.add_argument("--switch-weight", type=float, default=0.08)
    args = parser.parse_args()
    if args.users < 2:
        parser.error("--users must be at least 2")
    if args.epochs < 1 or args.warmup_epochs < 0 or args.seeds < 1:
        parser.error("--epochs/--seeds must be positive and warm-up non-negative")

    media = locate_media(args.media_root)
    model = PortableEnsemble(args.model)
    export_error = model.verify_export()
    payload = model.payload
    template = np.asarray(payload["template_median"], dtype=float)
    ladder = np.asarray(payload["ladder_mbps"], dtype=float)
    radius = conformal_radius(
        payload["calibration"]["one_sided_residuals"],
        float(payload["calibration"]["alpha"]),
    )
    args.output.mkdir(parents=True, exist_ok=True)
    csv_path = args.output / "live_measurements.csv"
    expected_pair_rows = args.users * (args.warmup_epochs + args.epochs)
    completed_pairs: set[tuple[int, str]] = set()
    if args.resume and csv_path.exists():
        with csv_path.open(encoding="utf-8") as handle:
            existing_rows = list(csv.DictReader(handle))
        counts: dict[tuple[int, str], int] = {}
        for row in existing_rows:
            key = (int(row["seed"]), row["controller"])
            counts[key] = counts.get(key, 0) + 1
        completed_pairs = {
            key for key, count in counts.items() if count == expected_pair_rows
        }
        retained = [
            row
            for row in existing_rows
            if (int(row["seed"]), row["controller"]) in completed_pairs
        ]
        if retained:
            with csv_path.open("w", newline="", encoding="utf-8") as handle:
                writer = csv.DictWriter(handle, fieldnames=list(retained[0]))
                writer.writeheader()
                writer.writerows(retained)
        else:
            csv_path.unlink(missing_ok=True)
    elif csv_path.exists():
        csv_path.unlink()

    total_epochs = args.warmup_epochs + args.epochs
    campaign_plan = []
    for seed_index in range(args.seeds):
        seed = args.seed + seed_index
        rng = np.random.default_rng(seed)
        regime = args.regimes[seed_index % len(args.regimes)]
        profile = make_capacity_profile(regime, total_epochs, rng)
        segments = rng.integers(1, 61, size=total_epochs).tolist()
        order = (
            list(args.controllers)
            if args.fixed_order
            else counterbalanced_order(list(args.controllers), seed_index)
        )
        campaign_plan.append(
            {
                "seed": seed,
                "seed_index": seed_index,
                "regime": regime,
                "capacity_profile_mbps": profile,
                "segment_numbers": segments,
                "controller_order": order,
            }
        )
    (args.output / "campaign_plan.json").write_text(
        json.dumps(campaign_plan, indent=2), encoding="utf-8"
    )

    net = Mininet(controller=None, switch=OVSBridge, link=TCLink, build=False)
    server = net.addHost("server", ip="10.0.0.1/24")
    switch = net.addSwitch("s1")
    server_link = net.addLink(server, switch, bw=100, delay="4ms")
    clients = []
    for index in range(args.users):
        client = net.addHost(f"c{index + 1}", ip=f"10.0.0.{index + 2}/24")
        net.addLink(client, switch, bw=100, delay=f"{6 + index * 3}ms")
        clients.append(client)
    fieldnames = [
        "seed",
        "regime",
        "controller",
        "controller_position",
        "controller_order",
        "run_epoch",
        "epoch",
        "warmup",
        "segment_number",
        "user",
        "capacity_mbps",
        "allocated_mbps",
        "capacity_slack_mbps",
        "bytes",
        "download_s",
        "ttfb_s",
        "throughput_mbps",
        "buffer_before_s",
        "buffer_after_s",
        "stall_s",
        "decision_predicted_qoe",
        "decision_predicted_std",
        "decision_lower_qoe",
        "opportunity_gain",
        "predicted_qoe",
        "predicted_std",
        "operational_qoe",
        "debt_before",
        "debt_after",
        "switched",
        "candidate_count",
        "objective",
        "debt_term",
        "switching_term",
        "decision_ms",
        "epoch_wall_s",
    ]
    rows_written = 0
    server_process = None
    csv_handle = None
    try:
        net.build()
        net.start()
        server_interface = server_link.intf1.name
        server_process = server.popen(
            [
                "python3",
                "-m",
                "http.server",
                "8000",
                "--bind",
                "10.0.0.1",
                "--directory",
                str(media),
            ],
            stdout=-1,
            stderr=-1,
        )
        time.sleep(0.7)
        if any(client.cmd("ping -c1 -W1 10.0.0.1 >/dev/null; echo $?").strip() != "0" for client in clients):
            raise RuntimeError("Client-to-server connectivity check failed")

        file_exists = csv_path.exists() and csv_path.stat().st_size > 0
        csv_handle = csv_path.open("a", newline="", encoding="utf-8")
        writer = csv.DictWriter(csv_handle, fieldnames=fieldnames)
        if not file_exists:
            writer.writeheader()
            csv_handle.flush()

        for plan in campaign_plan:
            seed = int(plan["seed"])
            regime = str(plan["regime"])
            capacity_profile = plan["capacity_profile_mbps"]
            segments = plan["segment_numbers"]
            controller_order = plan["controller_order"]
            order_text = "|".join(controller_order)
            for controller_position, controller in enumerate(controller_order):
                pair = (seed, controller)
                if pair in completed_pairs:
                    print(f"skip complete seed={seed} controller={controller}")
                    continue
                buffer_s = np.full(args.users, 4.0)
                previous = np.full(args.users, ladder[1])
                throughput = np.full(
                    args.users, capacity_profile[0] / args.users
                )
                latency = np.array(
                    [0.010 + 0.006 * i for i in range(args.users)]
                )
                debt = np.zeros(args.users)
                for run_epoch, (capacity, segment_number) in enumerate(
                    zip(capacity_profile, segments)
                ):
                    set_shared_rate(server, server_interface, capacity)
                    decision_started = time.perf_counter()
                    action, decision = select_action(
                        controller,
                        model,
                        template,
                        ladder,
                        capacity,
                        throughput,
                        buffer_s,
                        previous,
                        latency,
                        debt,
                        radius,
                        debt_weight=args.debt_weight,
                        switch_weight=args.switch_weight,
                    )
                    decision_ms = 1000 * (
                        time.perf_counter() - decision_started
                    )
                    processes = []
                    started = time.perf_counter()
                    for user, (client, rate) in enumerate(zip(clients, action)):
                        ladder_index = int(np.abs(ladder - rate).argmin())
                        bitrate = LADDER_BPS[ladder_index]
                        url = (
                            f"http://10.0.0.1:8000/bunny_{bitrate}bps/"
                            f"BigBuckBunny_10s{segment_number}.m4s"
                        )
                        processes.append(
                            (user, rate, url, download_one(client, url))
                        )
                    measurements = []
                    for user, rate, url, process in processes:
                        output, error = process.communicate(timeout=180)
                        if process.returncode != 0:
                            raise RuntimeError(
                                f"curl failed for c{user + 1}: {error}"
                            )
                        size, total, ttfb, speed, status = (
                            output.strip().split(",")
                        )
                        if status != "200":
                            raise RuntimeError(f"HTTP {status} for {url}")
                        measurements.append(
                            (
                                float(size),
                                float(total),
                                float(ttfb),
                                float(speed),
                            )
                        )
                    wall_s = time.perf_counter() - started
                    size_bytes = np.array([m[0] for m in measurements])
                    download_s = np.array([m[1] for m in measurements])
                    ttfb_s = np.array([m[2] for m in measurements])
                    throughput = (
                        8.0
                        * size_bytes
                        / np.maximum(download_s, 1e-6)
                        / 1e6
                    )
                    stall_s = np.maximum(download_s - buffer_s, 0)
                    buffer_before = buffer_s.copy()
                    buffer_s = np.clip(
                        np.maximum(buffer_s - download_s, 0)
                        + SEGMENT_DURATION_S,
                        0,
                        30,
                    )
                    actual_features = build_features(
                        template,
                        action,
                        throughput,
                        buffer_before,
                        previous,
                        ttfb_s,
                    )
                    predicted_qoe, predicted_std = model.predict(
                        actual_features
                    )
                    operational_qoe = np.clip(
                        predicted_qoe
                        - 0.30 * stall_s
                        - 0.08
                        * np.abs(
                            np.log(
                                (action + 0.05) / (previous + 0.05)
                            )
                        ),
                        1,
                        5,
                    )
                    debt_before = debt.copy()
                    debt = np.maximum(
                        args.debt_decay * debt
                        + args.target_qoe
                        - operational_qoe,
                        0,
                    )
                    is_warmup = run_epoch < args.warmup_epochs
                    epoch = run_epoch - args.warmup_epochs
                    for user in range(args.users):
                        writer.writerow(
                            {
                                "seed": seed,
                                "regime": regime,
                                "controller": controller,
                                "controller_position": controller_position,
                                "controller_order": order_text,
                                "run_epoch": run_epoch,
                                "epoch": epoch,
                                "warmup": int(is_warmup),
                                "segment_number": segment_number,
                                "user": user + 1,
                                "capacity_mbps": capacity,
                                "allocated_mbps": action[user],
                                "capacity_slack_mbps": decision[
                                    "capacity_slack_mbps"
                                ],
                                "bytes": int(size_bytes[user]),
                                "download_s": download_s[user],
                                "ttfb_s": ttfb_s[user],
                                "throughput_mbps": throughput[user],
                                "buffer_before_s": buffer_before[user],
                                "buffer_after_s": buffer_s[user],
                                "stall_s": stall_s[user],
                                "decision_predicted_qoe": decision[
                                    "selected_mean"
                                ][user],
                                "decision_predicted_std": decision[
                                    "selected_uncertainty"
                                ][user],
                                "decision_lower_qoe": decision[
                                    "selected_lower"
                                ][user],
                                "opportunity_gain": decision[
                                    "selected_opportunity"
                                ][user],
                                "predicted_qoe": predicted_qoe[user],
                                "predicted_std": predicted_std[user],
                                "operational_qoe": operational_qoe[user],
                                "debt_before": debt_before[user],
                                "debt_after": debt[user],
                                "switched": int(
                                    action[user] != previous[user]
                                ),
                                "candidate_count": decision[
                                    "candidate_count"
                                ],
                                "objective": decision["objective"],
                                "debt_term": decision["debt_term"],
                                "switching_term": decision[
                                    "switching_term"
                                ],
                                "decision_ms": decision_ms,
                                "epoch_wall_s": wall_s,
                            }
                        )
                        rows_written += 1
                    csv_handle.flush()
                    previous = action
                    print(
                        f"seed={seed} regime={regime} "
                        f"order={controller_position + 1}/{len(controller_order)} "
                        f"controller={controller} epoch={epoch} "
                        f"capacity={capacity:.3f} "
                        f"mean_qoe={operational_qoe.mean():.3f} "
                        f"decision={decision_ms:.1f}ms wall={wall_s:.2f}s",
                        flush=True,
                    )
    finally:
        if csv_handle is not None:
            csv_handle.close()
        if server_process is not None:
            server_process.send_signal(signal.SIGTERM)
            server_process.wait(timeout=5)
        net.stop()
        os.system("mn -c >/dev/null 2>&1")

    metadata = {
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "media_root_name": media.name,
        "model_name": args.model.name,
        "portable_max_abs_error": export_error,
        "controllers": args.controllers,
        "users": args.users,
        "epochs": args.epochs,
        "warmup_epochs": args.warmup_epochs,
        "first_seed": args.seed,
        "seeds": args.seeds,
        "regimes": args.regimes,
        "counterbalanced_order": not args.fixed_order,
        "campaign_plan": "campaign_plan.json",
        "segment_duration_s": SEGMENT_DURATION_S,
        "target_operational_qoe": args.target_qoe,
        "debt_weight": args.debt_weight,
        "debt_decay": args.debt_decay,
        "switch_weight": args.switch_weight,
        "shared_bottleneck": "server-s1 egress TBF",
        "qoe_semantics": (
            "model-estimated operational QoE from measured transport features; "
            "not a new subjective human score"
        ),
    }
    (args.output / "run_metadata.json").write_text(
        json.dumps(metadata, indent=2), encoding="utf-8"
    )
    print(f"Wrote {rows_written} new measurements to {csv_path}")


if __name__ == "__main__":
    setLogLevel("warning")
    main()

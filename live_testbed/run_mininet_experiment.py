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
        "curl --silent --show-error --output /dev/null "
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
        default=["conformal_nash", "risk_debt"],
        choices=["uncertainty_nash", "conformal_nash", "risk_debt"],
    )
    parser.add_argument("--users", type=int, default=5)
    parser.add_argument("--epochs", type=int, default=8)
    parser.add_argument("--seed", type=int, default=20260728)
    parser.add_argument(
        "--target-qoe",
        type=float,
        default=4.0,
        help="Declared live operational-QoE floor used by the debt queue.",
    )
    args = parser.parse_args()

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
    capacity_profile = [2.0, 3.5, 1.4, 2.6, 1.8, 4.2, 1.3, 3.0]
    args.output.mkdir(parents=True, exist_ok=True)

    net = Mininet(controller=None, switch=OVSBridge, link=TCLink, build=False)
    server = net.addHost("server", ip="10.0.0.1/24")
    switch = net.addSwitch("s1")
    server_link = net.addLink(server, switch, bw=100, delay="4ms")
    clients = []
    for index in range(args.users):
        client = net.addHost(f"c{index + 1}", ip=f"10.0.0.{index + 2}/24")
        net.addLink(client, switch, bw=100, delay=f"{6 + index * 3}ms")
        clients.append(client)
    rows = []
    server_process = None
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

        for controller in args.controllers:
            rng = np.random.default_rng(args.seed)
            buffer_s = np.full(args.users, 4.0)
            previous = np.full(args.users, ladder[1])
            throughput = np.full(args.users, capacity_profile[0] / args.users)
            latency = np.array([0.010 + 0.006 * i for i in range(args.users)])
            debt = np.zeros(args.users)
            for epoch in range(args.epochs):
                capacity = capacity_profile[epoch % len(capacity_profile)]
                set_shared_rate(server, server_interface, capacity)
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
                )
                segment_number = 1 + (epoch % 60)
                processes = []
                started = time.perf_counter()
                for user, (client, rate) in enumerate(zip(clients, action)):
                    ladder_index = int(np.abs(ladder - rate).argmin())
                    bitrate = LADDER_BPS[ladder_index]
                    url = (
                        f"http://10.0.0.1:8000/bunny_{bitrate}bps/"
                        f"BigBuckBunny_10s{segment_number}.m4s"
                    )
                    processes.append((user, rate, url, download_one(client, url)))
                measurements = []
                for user, rate, url, process in processes:
                    output, error = process.communicate(timeout=90)
                    if process.returncode != 0:
                        raise RuntimeError(f"curl failed for c{user + 1}: {error}")
                    size, total, ttfb, speed, status = output.strip().split(",")
                    if status != "200":
                        raise RuntimeError(f"HTTP {status} for {url}")
                    measurements.append(
                        (float(size), float(total), float(ttfb), float(speed))
                    )
                wall_s = time.perf_counter() - started
                size_bytes = np.array([m[0] for m in measurements])
                download_s = np.array([m[1] for m in measurements])
                ttfb_s = np.array([m[2] for m in measurements])
                throughput = 8.0 * size_bytes / np.maximum(download_s, 1e-6) / 1e6
                stall_s = np.maximum(download_s - buffer_s, 0)
                buffer_before = buffer_s.copy()
                buffer_s = np.clip(
                    np.maximum(buffer_s - download_s, 0) + SEGMENT_DURATION_S,
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
                predicted_qoe, predicted_std = model.predict(actual_features)
                operational_qoe = np.clip(
                    predicted_qoe
                    - 0.30 * stall_s
                    - 0.08 * np.abs(np.log((action + 0.05) / (previous + 0.05))),
                    1,
                    5,
                )
                debt_before = debt.copy()
                debt = np.maximum(
                    0.90 * debt + args.target_qoe - operational_qoe, 0
                )
                for user in range(args.users):
                    rows.append(
                        {
                            "controller": controller,
                            "epoch": epoch,
                            "user": user + 1,
                            "capacity_mbps": capacity,
                            "allocated_mbps": action[user],
                            "bytes": int(size_bytes[user]),
                            "download_s": download_s[user],
                            "ttfb_s": ttfb_s[user],
                            "throughput_mbps": throughput[user],
                            "buffer_before_s": buffer_before[user],
                            "buffer_after_s": buffer_s[user],
                            "stall_s": stall_s[user],
                            "predicted_qoe": predicted_qoe[user],
                            "predicted_std": predicted_std[user],
                            "operational_qoe": operational_qoe[user],
                            "debt_before": debt_before[user],
                            "debt_after": debt[user],
                            "switched": int(action[user] != previous[user]),
                            "candidate_count": decision["candidate_count"],
                            "objective": decision["objective"],
                            "epoch_wall_s": wall_s,
                        }
                    )
                previous = action
                print(
                    f"{controller} epoch={epoch} capacity={capacity:.1f} "
                    f"mean_qoe={operational_qoe.mean():.3f} "
                    f"wall={wall_s:.2f}s"
                )
    finally:
        if server_process is not None:
            server_process.send_signal(signal.SIGTERM)
            server_process.wait(timeout=5)
        net.stop()
        os.system("mn -c >/dev/null 2>&1")

    csv_path = args.output / "live_measurements.csv"
    with csv_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    metadata = {
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "media_root": str(media),
        "model": str(args.model.resolve()),
        "portable_max_abs_error": export_error,
        "controllers": args.controllers,
        "users": args.users,
        "epochs": args.epochs,
        "capacity_profile_mbps": capacity_profile[: args.epochs],
        "segment_duration_s": SEGMENT_DURATION_S,
        "target_operational_qoe": args.target_qoe,
        "shared_bottleneck": "server-s1 egress TBF",
        "qoe_semantics": (
            "model-estimated operational QoE from measured transport features; "
            "not a new subjective human score"
        ),
    }
    (args.output / "run_metadata.json").write_text(
        json.dumps(metadata, indent=2), encoding="utf-8"
    )
    print(f"Wrote {len(rows)} measurements to {csv_path}")


if __name__ == "__main__":
    setLogLevel("warning")
    main()

"""Post-batch resource, duration and repeated-frame consistency diagnostics."""
import argparse
from collections import defaultdict
import gzip
import hashlib
import json
from statistics import mean
from metric_contract.data import ROOT, load
from metric_contract.core import CAP, TICKS
from metric_contract.run import canonical, sha
from duration_contract.run import MEDIA

OUT = ROOT / "duration_contract/results/diagnostics_v1"
REPLAY = ROOT / "duration_contract/results/replay_v1/results.json.gz"
MEASURED = ROOT / "duration_contract/results/measured_audit_v1/results.json"
RAW = ROOT / "duration_contract/results/paced_v1"


def resource_ledger(record, choices):
    """Independent non-refilling byte ledger, including actual container bytes."""
    spent = 0
    for t, pair in zip(range(2, 6), choices):
        if len(pair) != 2 or any(r < 2 or r > 5 for r in pair):
            raise ValueError("Structural rung floor")
        size = sum(int(record["costs"][t, r]) for r in pair)
        if size > CAP:
            raise ValueError("Per-round byte cap")
        spent += max(0, size - 2 * int(record["costs"][t, 2]))
        if spent > record["reserve"]:
            raise ValueError("Cumulative extra-byte reserve")
    return spent


def analysis():
    with gzip.open(REPLAY, "rt") as f:
        replay = json.load(f)
    measured = json.loads(MEASURED.read_text())
    records, _ = load()
    bykey = {r["key"]: r for r in records}
    nominal = {(r["key"], r["policy"]): r for r in replay["rows"] if r["mode"] == "nominal"}
    changes = defaultdict(int)
    reductions = []
    for r in replay["rows"]:
        resource_ledger(bykey[r["key"]], r["choices"])
        if r["mode"] != "actual":
            continue
        old = nominal[r["key"], r["policy"]]
        if r["choices"] != old["choices"] or r["arrivals"] != old["arrivals"]:
            raise ValueError("Duration audit changed fixed behavior")
        for key in ("deadline_credit", "eventual_credit", "half_by_deadline", "protected_half_by_deadline",
                    "deadline_unpaid", "eventual_unpaid", "worst_eventual_psnr_db"):
            changes[key] += r[key] != old[key]
        for u in (0, 1):
            reduction = old["timing"]["finish_ticks"][u] - r["timing"]["finish_ticks"][u]
            reductions.append(reduction)
            expected = 5000 if r["scene"] == "River01" else 0
            if reduction != expected:
                raise ValueError("Unexpected actual-duration completion difference")

    # Repeated decoding of an identical encoded file must produce identical
    # frame hash sequences. This is consistency, not a source-reference VQA test.
    signatures = {}
    streams = repeats = 0
    for path in sorted(RAW.glob("session_*.json.gz")):
        with gzip.open(path, "rt") as f:
            session = json.load(f)
        for u in (0, 1):
            for j, segment in enumerate(session["segments"][u]):
                start = segment["first_frame_index"]
                frames = session["frames"][u][start:start + segment["frames"]]
                signature = [(x["pts_ticks"], x["duration_ticks"], x["md5"], x["decoded_bytes"]) for x in frames]
                key = session["decoders"][f"{j}:{u}"]["file_sha256"]
                if key in signatures:
                    repeats += 1
                    if signatures[key] != signature:
                        raise ValueError("Repeated file decode differs")
                signatures[key] = signature
                streams += 1

    nominal_sessions = [r for r in measured["rows"] if not r["negative_control"]]
    changes_measured = {key: sum(r[key] != r["ideal_account"][key] for r in nominal_sessions)
                        for key in ("deadline_credit", "half_by_deadline", "protected_half_by_deadline")}
    players = [p for r in nominal_sessions for p in r["player_stats"]]
    source = {}
    for name in ("diagnose.py", "test_validation.py"):
        p = ROOT / "duration_contract" / name
        source[p.relative_to(ROOT).as_posix()] = sha(p)
    with gzip.open(MEDIA, "rt") as f:
        media = json.load(f)
    if media["script_sha256"] != sha(ROOT / "duration_contract/prepare.py"):
        raise ValueError("Media preparation source changed")
    return {
        "posthoc": True, "controller_retuned": False,
        "replay_resource_paths": len(replay["rows"]), "fixed_actual_nominal_pairs": len(nominal),
        "actual_nominal_changed": dict(changes),
        "actual_finish_reduced_users": sum(x > 0 for x in reductions),
        "maximum_finish_reduction_seconds": max(reductions) / TICKS,
        "decoded_streams": streams, "unique_decoded_files": len(signatures), "repeated_streams_checked": repeats,
        "measured_vs_ideal_changed": changes_measured,
        "nominal_players": len(players),
        "mean_pacing_lateness_seconds": mean(p["pacing_late_ns"] for p in players) / 1e9,
        "max_player_pacing_lateness_seconds": max(p["pacing_late_ns"] for p in players) / 1e9,
        "max_frame_pacing_lateness_ms": max(r["max_frame_pacing_late_ms"] for r in nominal_sessions),
        "negative_control": next(r for r in measured["rows"] if r["negative_control"]),
        "source_sha256": source, "replay_sha256": sha(REPLAY), "measured_sha256": sha(MEASURED),
        "media_sha256": sha(MEDIA),
    }


def figure():
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    with gzip.open(REPLAY, "rt") as f:
        replay = json.load(f)
    measured = json.loads(MEASURED.read_text())
    names = ["prefix_mpc", "prefix_cost_greedy", "prefix_greedy", "prefix_nash", "prefix_maxmin"]
    labels = ["Primary", "Cost-greedy", "Greedy", "Rolling Nash", "Max-min"]
    rows = {r["policy"]: r for r in replay["summary"] if r["group"] == "all" and r["mode"] == "actual"}
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.3), layout="constrained")
    ax = axes[0]
    x = list(range(len(names)))
    ax.bar([i - .18 for i in x], [rows[n]["half_by_deadline"] for n in names], .36, label="Raw target", color="#9faebf")
    ax.bar([i + .18 for i in x], [rows[n]["protected_half"] for n in names], .36, label="With both-user floors", color="#256b8a")
    ax.axhline(27, ls="--", color="#ab4a36", label="Strict offline bound: 27")
    ax.set_xticks(x, labels, rotation=25, ha="right")
    ax.set_ylabel("Episodes attaining 50% by 40 s (out of 168)")
    ax.set_title("A. Frozen policies; actual durations")
    ax.legend(fontsize=8)
    ax = axes[1]
    for policy, label, color in zip(("prefix_mpc", "prefix_cost_greedy", "baseline"),
                                    ("Primary", "Cost-greedy", "Baseline"), ("#ab4a36", "#256b8a", "#66774c")):
        rs = sorted((r for r in measured["rows"] if r["policy"] == policy and not r["negative_control"]), key=lambda r:r["scene"])
        ax.plot(range(6), [r["mean_added_finish_vs_ideal_seconds"] for r in rs], "o-", label=label, color=color)
    ax.set_xticks(range(6), [r["scene"].replace("01", "").replace("02", "") for r in rs], rotation=30, ha="right", fontsize=8)
    ax.set_ylabel("Added completion time vs ideal replay (s/user)")
    ax.set_title("B. Decode + paced frame events; six fixed pairs")
    ax.legend(fontsize=8)
    fig.savefig(OUT / "contract_timing.png", dpi=180)
    fig.savefig(OUT / "contract_timing.svg", metadata={"Date": None})
    plt.close(fig)


if __name__ == "__main__":
    p = argparse.ArgumentParser(__doc__)
    p.add_argument("--verify", action="store_true")
    args = p.parse_args()
    result = analysis()
    digest = hashlib.sha256(canonical(result)).hexdigest()
    if args.verify:
        metadata = json.loads((OUT / "metadata.json").read_text())
        if json.loads((OUT / "results.json").read_text()) != result or metadata["scientific_sha256"] != digest:
            raise ValueError("Diagnostic replay mismatch")
        for name, value in metadata["figure_sha256"].items():
            if sha(OUT / name) != value:
                raise ValueError("Figure changed")
    else:
        OUT.mkdir(parents=True, exist_ok=False)
        (OUT / "results.json").write_text(json.dumps(result, indent=2) + "\n")
        figure()
        (OUT / "metadata.json").write_text(json.dumps({"scientific_sha256": digest,
            "figure_sha256": {p.name: sha(p) for p in sorted(OUT.glob("contract_timing.*"))}}, indent=2) + "\n")
    print(json.dumps({"verified": args.verify, "scientific_sha256": digest,
                      "duration_changed": result["actual_nominal_changed"], "measured_changed": result["measured_vs_ideal_changed"]}))

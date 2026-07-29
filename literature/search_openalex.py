"""Reproducible OpenAlex discovery and citation-metadata collection."""

from __future__ import annotations

import argparse
import csv
import json
import urllib.parse
import urllib.request
from pathlib import Path


SEARCHES = {
    "qoe_fairness": (
        "quality of experience fairness adaptive video streaming "
        "DASH resource allocation"
    ),
    "immersive_multiuser": (
        "360 video immersive VR QoE fairness multi-user viewport "
        "bitrate allocation"
    ),
    "conformal_network": (
        "conformal prediction uncertainty quantification streaming "
        "network resource allocation"
    ),
    "temporal_fairness": (
        "temporal fairness long-term fairness persistent deprivation "
        "network scheduling"
    ),
    "qoe_shift": (
        "QoE prediction distribution shift uncertainty adaptive streaming"
    ),
}

SEED_TITLES = [
    "Improving Fairness, Efficiency, and Stability in HTTP-based Adaptive Video Streaming with FESTIVE",
    "Neural Adaptive Video Streaming with Pensieve",
    "BOLA: Near-Optimal Bitrate Adaptation for Online Videos",
    "A Control-Theoretic Approach for Dynamic Adaptive Video Streaming over HTTP",
    "Learning to Predict Streaming Video QoE: Distortions, Rebuffering and Memory",
    "Streaming Video QoE Modeling and Prediction: A Long Short-Term Memory Approach",
    "Modeling the Time-Varying Subjective Quality of HTTP Video Streams With Rate Adaptations",
    "Flare: Practical Viewport-Adaptive 360-Degree Video Streaming for Mobile Devices",
    "Pano: Optimizing 360 Video Streaming with a Better Understanding of Quality Perception",
    "VAS360: QoE-Driven Viewport Adaptive Streaming for 360 Video",
    "Probabilistic Viewport Adaptive Streaming for 360-degree Videos",
    "Adaptive Conformal Inference Under Distribution Shift",
    "Conformalized Quantile Regression",
    "A Gentle Introduction to Conformal Prediction and Distribution-Free Uncertainty Quantification",
    "Fair Resource Allocation in Federated Learning",
    "Risk as a Resource: Personalized 360° Streaming via Adaptive Conformal Prediction",
    "FairEdge360: Distributed Multi-Agent Reinforcement Learning for QoE-Fair 360° Video Streaming with Uncertainty-Aware Edge Coordination",
]


def fetch_json(url: str) -> dict:
    request = urllib.request.Request(
        url,
        headers={"User-Agent": "qoe-fairness-systematic-review/0.1"},
    )
    with urllib.request.urlopen(request, timeout=60) as response:
        return json.load(response)


def abstract_text(inverted: dict | None) -> str:
    if not inverted:
        return ""
    positions = []
    for word, indices in inverted.items():
        positions.extend((index, word) for index in indices)
    return " ".join(word for _, word in sorted(positions))


def compact(work: dict, family: str) -> dict:
    primary = work.get("primary_location") or {}
    source = primary.get("source") or {}
    return {
        "search_family": family,
        "openalex_id": work.get("id"),
        "title": work.get("display_name"),
        "year": work.get("publication_year"),
        "doi": work.get("doi"),
        "type": work.get("type"),
        "venue": source.get("display_name"),
        "is_oa": (work.get("open_access") or {}).get("is_oa"),
        "cited_by_count": work.get("cited_by_count", 0),
        "publication_date": work.get("publication_date"),
        "primary_url": primary.get("landing_page_url"),
        "abstract": abstract_text(work.get("abstract_inverted_index")),
    }


def search(query: str, per_page: int = 100) -> list[dict]:
    params = urllib.parse.urlencode(
        {
            "search": query,
            "filter": "from_publication_date:2010-01-01,to_publication_date:2026-07-28",
            "per-page": per_page,
            "select": (
                "id,display_name,publication_year,doi,type,primary_location,"
                "open_access,cited_by_count,publication_date,abstract_inverted_index"
            ),
        }
    )
    return fetch_json(f"https://api.openalex.org/works?{params}")["results"]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)

    raw = {}
    records = []
    for family, query in SEARCHES.items():
        works = search(query)
        raw[family] = works
        records.extend(compact(work, family) for work in works)
    for index, title in enumerate(SEED_TITLES):
        works = search(title, per_page=5)
        raw[f"seed_{index:02d}"] = works
        if works:
            records.append(compact(works[0], "seed_title"))

    # Deduplicate by OpenAlex ID while retaining every discovery family.
    deduplicated = {}
    for record in records:
        identifier = record["openalex_id"] or record["doi"] or record["title"]
        if identifier in deduplicated:
            existing = deduplicated[identifier]
            families = set(existing["search_family"].split(";"))
            families.add(record["search_family"])
            existing["search_family"] = ";".join(sorted(families))
        else:
            deduplicated[identifier] = record
    candidates = sorted(
        deduplicated.values(),
        key=lambda item: (-int(item["cited_by_count"] or 0), item["title"] or ""),
    )

    (args.output / "openalex_raw.json").write_text(
        json.dumps(raw, indent=2), encoding="utf-8"
    )
    with (args.output / "candidates.csv").open(
        "w", newline="", encoding="utf-8"
    ) as handle:
        writer = csv.DictWriter(handle, fieldnames=list(candidates[0]))
        writer.writeheader()
        writer.writerows(candidates)
    (args.output / "search_log.json").write_text(
        json.dumps(
            {
                "search_date": "2026-07-28",
                "searches": SEARCHES,
                "seed_titles": SEED_TITLES,
                "raw_records": sum(len(value) for value in raw.values()),
                "deduplicated_records": len(candidates),
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    print(f"Wrote {len(candidates)} deduplicated candidates")


if __name__ == "__main__":
    main()


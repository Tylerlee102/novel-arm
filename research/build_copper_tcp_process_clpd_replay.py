#!/usr/bin/env python3
"""Build CLPD replay counts from TCP process-server COPPER counters."""

from __future__ import annotations

import csv
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "research" / "results"
TCP_DIR = RESULTS / "gem5_arm_ubuntu_fs_ossltlstcp_app"
SOURCE_CSVS = [
    TCP_DIR / "ossltlstcp_tcp_netns_process_key1_summary.csv",
    TCP_DIR / "ossltlstcp_tcp_netns_process_seed1_summary.csv",
    TCP_DIR / "ossltlstcp_tcp_netns_process_scale2_summary.csv",
    TCP_DIR / "ossltlstcp_tcp_netns_process_scale3_summary.csv",
]
OUT_JSON = RESULTS / "copper_clpd_tcp_process_replay_counts_20260620.json"
OUT_CSV = RESULTS / "copper_clpd_tcp_process_replay_counts_20260620.csv"
OUT_SVH = RESULTS / "copper_clpd_tcp_process_replay_counts_20260620.svh"
MAX_REPLAY_OPS = 300_000
POLICY = "spp_copper_slack"
DEFAULT_SEED = 12648431


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def as_int(row: dict[str, str], key: str) -> int:
    raw = row.get(key, "0") or "0"
    return int(float(raw))


def scaled_count(value: int, scale: float) -> int:
    if value <= 0:
        return 0
    return max(1, int(round(value * scale)))


def rel(path: Path) -> str:
    return str(path.relative_to(ROOT)).replace("\\", "/")


def main() -> None:
    rows: list[dict[str, str]] = []
    for source_csv in SOURCE_CSVS:
        rows.extend(read_csv(source_csv))

    selected = [row for row in rows if row["policy"] == POLICY]
    if len(selected) != len(SOURCE_CSVS):
        raise SystemExit(f"expected {len(SOURCE_CSVS)} rows for {POLICY}, found {len(selected)}")

    bad_rows = [
        row
        for row in selected
        if row.get("transport") != "tcp_loopback_netns_process"
        or as_int(row, "process_server") != 1
        or as_int(row, "child_failures") != 0
        or as_int(row, "fillPrefetchTranslationFault") != 0
    ]
    if bad_rows:
        raise SystemExit(f"invalid TCP process-server rows: {bad_rows}")

    raw = {
        "learned_proofs": sum(as_int(row, "learnedProofs") for row in selected),
        "allowed_candidates": sum(as_int(row, "allowedCandidates") for row in selected),
        "blocked_no_provenance": sum(as_int(row, "blockedNoProvenance") for row in selected),
        "target_line_witness_misses": sum(as_int(row, "targetLineWitnessMisses") for row in selected),
        "pointer_like_candidates": sum(as_int(row, "pointerLikeCandidates") for row in selected),
        "pf_issued": sum(as_int(row, "pfIssued") for row in selected),
        "pf_useful": sum(as_int(row, "pfUseful") for row in selected),
        "boundary_authority_entries_dropped": sum(
            as_int(row, "boundaryAuthorityEntriesDropped") for row in selected
        ),
        "process_pairs": sum(as_int(row, "process_pairs") for row in selected),
        "child_failures": sum(as_int(row, "child_failures") for row in selected),
        "translation_faults": sum(as_int(row, "fillPrefetchTranslationFault") for row in selected),
    }
    replay_raw_total = (
        raw["learned_proofs"]
        + raw["allowed_candidates"]
        + raw["blocked_no_provenance"]
        + raw["target_line_witness_misses"]
    )
    scale = min(1.0, MAX_REPLAY_OPS / replay_raw_total)
    replay = {
        "commit_ops": scaled_count(raw["learned_proofs"], scale),
        "allow_queries": scaled_count(raw["allowed_candidates"], scale),
        "block_queries": scaled_count(raw["blocked_no_provenance"], scale),
        "fault_queries": scaled_count(raw["target_line_witness_misses"], scale),
    }
    total = sum(replay.values())
    if total > MAX_REPLAY_OPS:
        largest = max(replay, key=replay.get)
        replay[largest] -= total - MAX_REPLAY_OPS

    payload = {
        "source_csvs": [rel(path) for path in SOURCE_CSVS],
        "policy": POLICY,
        "why_policy": "SPP+COPPER slack gates the larger candidate stream in the TCP process-server run, so it is the conservative CLPD activity replay mix.",
        "seed_points": len(selected),
        "max_replay_ops": MAX_REPLAY_OPS,
        "scale_factor": scale,
        "raw": raw,
        "replay": replay,
        "replay_total_ops": sum(replay.values()),
        "seeds": [
            {
                "seed": as_int(row, "seed"),
                "checksum": row["checksum"],
                "learned_proofs": as_int(row, "learnedProofs"),
                "allowed_candidates": as_int(row, "allowedCandidates"),
                "blocked_no_provenance": as_int(row, "blockedNoProvenance"),
                "target_line_witness_misses": as_int(row, "targetLineWitnessMisses"),
                "process_pairs": as_int(row, "process_pairs"),
            }
            for row in selected
        ],
    }
    OUT_JSON.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    with OUT_CSV.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.writer(fh)
        writer.writerow(["field", "raw_count", "replay_count", "scale_factor"])
        writer.writerow(["learned_proofs/commit_ops", raw["learned_proofs"], replay["commit_ops"], scale])
        writer.writerow(["allowed_candidates/allow_queries", raw["allowed_candidates"], replay["allow_queries"], scale])
        writer.writerow(["blocked_no_provenance/block_queries", raw["blocked_no_provenance"], replay["block_queries"], scale])
        writer.writerow(
            [
                "target_line_witness_misses/fault_queries",
                raw["target_line_witness_misses"],
                replay["fault_queries"],
                scale,
            ]
        )
        writer.writerow(["total_replay_driver_ops", replay_raw_total, sum(replay.values()), scale])

    OUT_SVH.write_text(
        "\n".join(
            [
                "// Generated by research/build_copper_tcp_process_clpd_replay.py",
                f"localparam int DEFAULT_COMMIT_OPS = {replay['commit_ops']};",
                f"localparam int DEFAULT_ALLOW_QUERIES = {replay['allow_queries']};",
                f"localparam int DEFAULT_BLOCK_QUERIES = {replay['block_queries']};",
                f"localparam int DEFAULT_FAULT_QUERIES = {replay['fault_queries']};",
                f"localparam int DEFAULT_SOURCE_ROWS = {len(selected)};",
                f"localparam int DEFAULT_RAW_TOTAL = {replay_raw_total};",
                f"localparam int DEFAULT_SCALED_TOTAL = {sum(replay.values())};",
                f"localparam int DEFAULT_REPLAY_SEED = {DEFAULT_SEED};",
                "",
            ]
        ),
        encoding="utf-8",
    )

    print(OUT_JSON)
    print(OUT_CSV)
    print(OUT_SVH)


if __name__ == "__main__":
    main()

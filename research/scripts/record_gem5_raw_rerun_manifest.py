#!/usr/bin/env python3
"""Record local raw gem5 rerun provenance without promoting broad claims."""

from __future__ import annotations

import csv
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
RESULTS = ROOT / "research" / "results"
OUT = RESULTS / "gem5_raw_rerun_manifest.csv"
SUMMARY = RESULTS / "gem5_arm_ubuntu_fs_cachesvc_app" / "cachesvc_codex_raw_smoke_summary.csv"
RUN_PREFIX = "gem5_arm_ubuntu_fs_cachesvc_codex_raw_smoke_"


FIELDS = [
    "tag",
    "policy",
    "status",
    "environment",
    "gem5_version",
    "gem5_started",
    "command_line",
    "output_dir",
    "stats_path",
    "terminal_path",
    "host_stdout",
    "host_stderr",
    "summary_path",
    "summary_checksum",
    "rc",
    "roi_ticks",
    "instructions",
    "l1d_demand_misses",
    "notes",
]


def rel(path: Path) -> str:
    return str(path.relative_to(ROOT)).replace("\\", "/")


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def first_match(pattern: str, text: str) -> str:
    match = re.search(pattern, text, re.MULTILINE)
    return match.group(1).strip() if match else ""


def terminal_info(path: Path) -> tuple[str, str]:
    text = path.read_text(encoding="utf-8", errors="replace") if path.exists() else ""
    result = re.search(
        r"CACHESVC_COPPER_RESULT\s+(?P<body>.*?)checksum=(?P<checksum>0x[0-9a-fA-F]+)",
        text,
    )
    checksum = result.group("checksum") if result else ""
    rc = first_match(r"COPPER_FS_NATIVE_A64_DONE rc=(\d+)", text)
    return checksum, rc


def row_for(policy: str, summary_by_policy: dict[str, dict[str, str]]) -> dict[str, str]:
    run_dir = RESULTS / f"{RUN_PREFIX}{policy}"
    host_stdout = run_dir.with_suffix(".host.out")
    host_stderr = run_dir.with_suffix(".host.err")
    stats = run_dir / "stats.txt"
    terminal = run_dir / "board.terminal"
    host_text = host_stdout.read_text(encoding="utf-8", errors="replace") if host_stdout.exists() else ""
    checksum, rc = terminal_info(terminal)
    summary = summary_by_policy.get(policy, {})
    status = "PASS" if stats.exists() and stats.stat().st_size > 0 and rc == "0" and checksum else "BLOCKED"
    return {
        "tag": "codex_raw_smoke",
        "policy": policy,
        "status": status,
        "environment": "local_windows",
        "gem5_version": first_match(r"gem5 version\s+([^\r\n]+)", host_text),
        "gem5_started": first_match(r"gem5 started\s+([^\r\n]+)", host_text),
        "command_line": first_match(r"command line:\s+([^\r\n]+)", host_text),
        "output_dir": rel(run_dir),
        "stats_path": rel(stats) if stats.exists() else "",
        "terminal_path": rel(terminal) if terminal.exists() else "",
        "host_stdout": rel(host_stdout) if host_stdout.exists() else "",
        "host_stderr": rel(host_stderr) if host_stderr.exists() else "",
        "summary_path": rel(SUMMARY) if SUMMARY.exists() else "",
        "summary_checksum": summary.get("checksum", checksum),
        "rc": summary.get("rc", rc),
        "roi_ticks": summary.get("roi_ticks", ""),
        "instructions": summary.get("insts_not_nop", ""),
        "l1d_demand_misses": summary.get("l1d_demand_misses", ""),
        "notes": (
            "Fresh local raw gem5 ARM full-system cache-service smoke rerun. "
            "This proves the smoke path is runnable in this local environment; "
            "it is not a full workload/config matrix or clone-local CI proof."
        ),
    }


def main() -> int:
    summary_by_policy = {row.get("policy", ""): row for row in read_csv(SUMMARY)}
    policies = ["none", "copper_clpd64k_peb"]
    rows = [row_for(policy, summary_by_policy) for policy in policies]
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(rows)
    print(f"wrote {rel(OUT)}")
    return 0 if all(row["status"] == "PASS" for row in rows) else 1


if __name__ == "__main__":
    raise SystemExit(main())

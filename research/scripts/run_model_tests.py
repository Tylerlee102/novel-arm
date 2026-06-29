#!/usr/bin/env python3
"""Run COPPER functional model checks and write model_tests.csv."""

from __future__ import annotations

import csv
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
RESEARCH = ROOT / "research"
RESULTS = RESEARCH / "results"
OUT = RESULTS / "model_tests.csv"
sys.path.insert(0, str(RESEARCH / "scripts"))

from copper_eval_model import Access, ModelSimulator, Workload  # noqa: E402


def row(
    name: str,
    status: str,
    expected: str,
    actual: str,
    notes: str = "",
    *,
    component: str = "copper_eval_model",
    seed: str = "deterministic",
    input_size: str = "tiny",
) -> dict[str, str]:
    return {
        "test_name": name,
        "component": component,
        "status": status,
        "seed": seed,
        "input_size": input_size,
        "expected": expected,
        "actual": actual,
        "notes": notes,
    }


def run(config: str, accesses: list[Access], **kwargs: int | bool):
    workload = Workload("model_test", "tiny", 0, "yes", "directed", tuple(accesses))
    return ModelSimulator(config=config, **kwargs).run(workload)


def main() -> int:
    RESULTS.mkdir(parents=True, exist_ok=True)
    rows: list[dict[str, str]] = []

    trained = [
        Access(addr=0x1040, source_addr=0x1000, candidate=None),
        Access(addr=0x9000, pointer_source=False),
        Access(addr=0x1000, candidate=0x1040),
    ]
    committed = run("copper", trained, cache_lines=1)
    rows.append(
        row(
            "committed-only provenance update",
            "PASS" if committed.prefetches_issued == 1 else "FAIL",
            "committed proof authorizes one prefetch",
            f"prefetches={committed.prefetches_issued}",
        )
    )

    wrong_path = [
        Access(addr=0x1040, source_addr=0x1000, candidate=None, committed=False),
        Access(addr=0x9000, pointer_source=False),
        Access(addr=0x1000, candidate=0x1040),
    ]
    copper_wrong = run("copper", wrong_path, cache_lines=1)
    speculative_wrong = run("A1_speculative_provenance", wrong_path, cache_lines=1)
    rows.append(
        row(
            "wrong-path/speculative update rejection",
            "PASS" if copper_wrong.prefetches_issued == 0 and speculative_wrong.prefetches_issued > 0 else "FAIL",
            "copper rejects uncommitted proof; speculative ablation exposes risk",
            f"copper={copper_wrong.prefetches_issued}, speculative={speculative_wrong.prefetches_issued}",
        )
    )

    non_pointer = [
        Access(addr=0x1040, source_addr=0x1000),
        Access(addr=0x1000, candidate=0x1040, pointer_source=False),
    ]
    non_pointer_result = run("copper", non_pointer)
    rows.append(
        row(
            "non-pointer load rejection",
            "PASS" if non_pointer_result.prefetches_issued == 0 else "FAIL",
            "non-pointer source does not prefetch",
            f"prefetches={non_pointer_result.prefetches_issued}",
        )
    )

    chain = [
        Access(addr=0x1040, source_addr=0x1000),
        Access(addr=0x1080, source_addr=0x1040),
        Access(addr=0x9000, pointer_source=False),
        Access(addr=0x1000, candidate=0x1040),
        Access(addr=0x1040, candidate=0x1080),
    ]
    chain_result = run("copper", chain, cache_lines=1)
    rows.append(
        row(
            "pointer-chain detection",
            "PASS" if chain_result.prefetches_issued >= 2 else "FAIL",
            "reused committed chain sources issue prefetches",
            f"prefetches={chain_result.prefetches_issued}",
        )
    )

    duplicate = [
        Access(addr=0x1040, source_addr=0x1000),
        Access(addr=0x1000, candidate=0x1040, gap_after=0),
        Access(addr=0x1000, candidate=0x1040, gap_after=0),
        Access(addr=0x1000, candidate=0x1040, gap_after=0),
    ]
    duplicate_result = run("copper", duplicate, prefetch_latency=100)
    rows.append(
        row(
            "duplicate prefetch suppression",
            "PASS" if duplicate_result.duplicate_suppressed > 0 else "FAIL",
            "duplicate candidate is suppressed while queued or cached",
            f"duplicate_suppressed={duplicate_result.duplicate_suppressed}",
        )
    )

    overflow = [
        Access(addr=0x2000, source_addr=0x1000),
        Access(addr=0x3000, source_addr=0x1100),
        Access(addr=0x4000, source_addr=0x1200),
        Access(addr=0x9000, pointer_source=False),
        Access(addr=0x1000, candidate=0x2000, gap_after=0),
        Access(addr=0x1100, candidate=0x3000, gap_after=0),
        Access(addr=0x1200, candidate=0x4000, gap_after=0),
    ]
    overflow_result = run("copper", overflow, cache_lines=1, queue_size=1, prefetch_latency=1000)
    rows.append(
        row(
            "queue-capacity behavior",
            "PASS" if overflow_result.queue_drops > 0 else "FAIL",
            "queue full causes drops",
            f"queue_drops={overflow_result.queue_drops}",
        )
    )
    rows.append(
        row(
            "queue overflow/drop accounting",
            "PASS" if overflow_result.prefetches_issued == 1 and overflow_result.queue_drops == 2 else "FAIL",
            "one queued request and two drops with queue_size=1",
            f"issued={overflow_result.prefetches_issued}, drops={overflow_result.queue_drops}",
        )
    )

    disabled_accesses = [
        Access(addr=0x1040, source_addr=0x1000),
        Access(addr=0x1000, candidate=0x1040),
    ]
    disabled = run("no_prefetch", disabled_accesses)
    enabled = run("copper", disabled_accesses)
    rows.append(
        row(
            "disabled-COPPER behavior",
            "PASS" if disabled.prefetches_issued == 0 and disabled.checksum == enabled.checksum else "FAIL",
            "no prefetches and same architectural checksum",
            f"disabled_prefetches={disabled.prefetches_issued}, checksum_match={disabled.checksum == enabled.checksum}",
        )
    )

    table_overflow = [
        Access(addr=0x2000, source_addr=0x1000),
        Access(addr=0x3000, source_addr=0x1100),
        Access(addr=0x1000, candidate=0x2000),
    ]
    table_result = run("copper", table_overflow, table_size=1)
    rows.append(
        row(
            "boundary/overflow cases",
            "PASS" if table_result.prefetches_issued == 0 else "FAIL",
            "old proof evicted from bounded table",
            f"prefetches={table_result.prefetches_issued}",
        )
    )

    with OUT.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(
            fh,
            fieldnames=["test_name", "component", "status", "seed", "input_size", "expected", "actual", "notes"],
        )
        writer.writeheader()
        writer.writerows(rows)
    failing = [r for r in rows if r["status"] == "FAIL"]
    print(f"wrote {OUT.relative_to(ROOT)}")
    return 1 if failing else 0


if __name__ == "__main__":
    raise SystemExit(main())

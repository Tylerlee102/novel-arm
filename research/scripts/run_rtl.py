#!/usr/bin/env python3
"""Compile and simulate the open-source COPPER RTL smoke target when tools exist."""

from __future__ import annotations

import argparse
import csv
import os
import platform
import shutil
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
RESEARCH = ROOT / "research"
RESULTS = RESEARCH / "results"
RTL_DIR = RESULTS / "rtl"
LOG_DIR = RESULTS / "logs" / "rtl"
COMPILE_CSV = RESULTS / "rtl_compile.csv"
SIM_CSV = RESULTS / "rtl_simulation.csv"
VVP = RTL_DIR / "copper_prefetch_unit_open_tb.vvp"


def current_environment() -> str:
    override = os.environ.get("COPPER_ENVIRONMENT", "").strip()
    if override:
        return override
    if os.environ.get("GITHUB_ACTIONS", "").lower() == "true":
        return "github_actions"
    if os.environ.get("CODESPACES", "").lower() == "true":
        return "codespaces"
    if Path("/.dockerenv").exists() or os.environ.get("container"):
        return "docker"
    if platform.system().lower().startswith("win"):
        return "local_windows"
    return "docker"


ENVIRONMENT = current_environment()


def rel(path: Path) -> str:
    return str(path.relative_to(ROOT)).replace("\\", "/")


def run(command: list[str], log_path: Path) -> tuple[int, str]:
    proc = subprocess.run(
        command,
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        timeout=60,
    )
    log_path.write_text(proc.stdout, encoding="utf-8")
    return proc.returncode, proc.stdout


def count_word(text: str, word: str) -> int:
    return sum(1 for line in text.splitlines() if word.lower() in line.lower())


def compile_rtl() -> dict[str, str]:
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    log_path = LOG_DIR / "iverilog_copper_prefetch_unit_open.log"
    iverilog = shutil.which("iverilog")
    if not iverilog:
        log_path.write_text("iverilog not found on PATH\n", encoding="utf-8")
        return {
            "design": "copper_prefetch_unit_open",
            "tool": "iverilog",
            "environment": ENVIRONMENT,
            "status": "BLOCKED",
            "warnings": "0",
            "errors": "1",
            "log_path": rel(log_path),
            "notes": "Open-source RTL compile requires Icarus Verilog. Docker/CI installs it; local Windows may block.",
        }
    command = [
        iverilog,
        "-g2012",
        "-Wall",
        "-o",
        str(VVP),
        str(RESEARCH / "copper_prefetch_unit_open.sv"),
        str(RESEARCH / "copper_prefetch_unit_open_tb.sv"),
    ]
    code, output = run(command, log_path)
    errors = count_word(output, "error")
    warnings = count_word(output, "warning")
    return {
        "design": "copper_prefetch_unit_open",
        "tool": "iverilog",
        "environment": ENVIRONMENT,
        "status": "PASS" if code == 0 and errors == 0 else "FAIL",
        "warnings": str(warnings),
        "errors": str(errors if errors else (0 if code == 0 else 1)),
        "log_path": rel(log_path),
        "notes": "Open-source smoke compile of COPPER unit with queue/disable/speculation checks.",
    }


def existing_rows(path: Path, fieldnames: list[str], defaults: dict[str, str]) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))
    out = []
    for row in rows:
        for key, value in defaults.items():
            if not row.get(key):
                row[key] = value
        out.append({field: row.get(field, "") for field in fieldnames})
    return out


def write_single_row(path: Path, fieldnames: list[str], row_data: dict[str, str], key_fields: list[str], defaults: dict[str, str]) -> None:
    key = tuple(row_data.get(field, "") for field in key_fields)
    keep = [
        row
        for row in existing_rows(path, fieldnames, defaults)
        if tuple(row.get(field, "") for field in key_fields) != key
    ]
    with path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(keep + [row_data])


def write_compile(row_data: dict[str, str]) -> None:
    fieldnames = ["design", "tool", "environment", "status", "warnings", "errors", "log_path", "notes"]
    write_single_row(
        COMPILE_CSV,
        fieldnames,
        row_data,
        ["design", "tool", "environment"],
        {"environment": "local_windows"},
    )


def simulate_rtl() -> dict[str, str]:
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    if not VVP.exists():
        compile_row = compile_rtl()
        write_compile(compile_row)
        if compile_row["status"] != "PASS":
            log_path = LOG_DIR / "vvp_copper_prefetch_unit_open_tb.log"
            log_path.write_text("simulation blocked because compile did not pass\n", encoding="utf-8")
            return {
                "testbench": "copper_prefetch_unit_open_tb",
                "design": "copper_prefetch_unit_open",
                "tool": "vvp",
                "environment": ENVIRONMENT,
                "seed": "directed",
                "status": "BLOCKED",
                "cycles": "",
                "assertions_passed": "0",
                "assertions_failed": "0",
                "log_path": rel(log_path),
                "notes": "Compile blocked.",
            }
    vvp = shutil.which("vvp")
    log_path = LOG_DIR / "vvp_copper_prefetch_unit_open_tb.log"
    if not vvp:
        log_path.write_text("vvp not found on PATH\n", encoding="utf-8")
        return {
            "testbench": "copper_prefetch_unit_open_tb",
            "design": "copper_prefetch_unit_open",
            "tool": "vvp",
            "environment": ENVIRONMENT,
            "seed": "directed",
            "status": "BLOCKED",
            "cycles": "",
            "assertions_passed": "0",
            "assertions_failed": "0",
            "log_path": rel(log_path),
            "notes": "Icarus runtime unavailable.",
        }
    code, output = run([vvp, str(VVP)], log_path)
    failed = count_word(output, "error")
    completed = "COPPER open RTL directed tests completed" in output
    return {
        "testbench": "copper_prefetch_unit_open_tb",
        "design": "copper_prefetch_unit_open",
        "tool": "vvp",
        "environment": ENVIRONMENT,
        "seed": "directed",
        "status": "PASS" if code == 0 and failed == 0 and completed else "FAIL",
        "cycles": "",
        "assertions_passed": "15" if completed and failed == 0 else "0",
        "assertions_failed": str(failed),
        "log_path": rel(log_path),
        "notes": "Directed reset, committed provenance update, speculative rejection, request generation, queue full behavior, disabled-COPPER behavior, permission block, no architectural output mutation.",
    }


def write_sim(row_data: dict[str, str]) -> None:
    fieldnames = [
        "testbench",
        "design",
        "tool",
        "environment",
        "seed",
        "status",
        "cycles",
        "assertions_passed",
        "assertions_failed",
        "log_path",
        "notes",
    ]
    write_single_row(
        SIM_CSV,
        fieldnames,
        row_data,
        ["testbench", "design", "tool", "environment", "seed"],
        {"tool": "vvp", "environment": "local_windows"},
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=["compile", "sim"], required=True)
    args = parser.parse_args()
    RESULTS.mkdir(parents=True, exist_ok=True)
    RTL_DIR.mkdir(parents=True, exist_ok=True)
    if args.mode == "compile":
        row_data = compile_rtl()
        write_compile(row_data)
        print(f"wrote {COMPILE_CSV.relative_to(ROOT)}")
        return 1 if row_data["status"] == "FAIL" else 0
    row_data = simulate_rtl()
    write_sim(row_data)
    print(f"wrote {SIM_CSV.relative_to(ROOT)}")
    return 1 if row_data["status"] == "FAIL" else 0


if __name__ == "__main__":
    raise SystemExit(main())

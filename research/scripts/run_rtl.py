#!/usr/bin/env python3
"""Compile and simulate the open-source COPPER RTL smoke target when tools exist."""

from __future__ import annotations

import argparse
import csv
import os
import platform
import re
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
ASSERTION_PASSED = re.compile(r"COPPER_ASSERTIONS_PASSED=(\d+)")
ASSERTION_FAILED = re.compile(r"COPPER_ASSERTIONS_FAILED=(\d+)")


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


def text_or_empty(value: str | bytes | None) -> str:
    if value is None:
        return ""
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace")
    return value


def run(command: list[str], log_path: Path) -> tuple[int, str]:
    try:
        proc = subprocess.run(
            command,
            cwd=ROOT,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            timeout=60,
        )
        output = proc.stdout
        code = proc.returncode
    except subprocess.TimeoutExpired as exc:
        output = text_or_empty(exc.stdout) + text_or_empty(exc.stderr)
        output += "\nCOPPER_RUNNER_ERROR command timed out after 60 seconds\n"
        code = 124
    except Exception as exc:  # pragma: no cover - defensive CI evidence path
        output = f"COPPER_RUNNER_ERROR {type(exc).__name__}: {exc}\n"
        code = 125
    log_path.write_text(output, encoding="utf-8")
    return code, output


def count_word(text: str, word: str) -> int:
    return sum(1 for line in text.splitlines() if word.lower() in line.lower())


def first_error_line(text: str) -> str:
    for line in text.splitlines():
        lowered = line.lower()
        if line.startswith("COPPER_ASSERTION_FAIL") or line.startswith("COPPER_RUNNER_ERROR"):
            return line.strip()
        if " error:" in lowered or lowered.startswith("error"):
            return line.strip()
    return ""


def parse_assertion_count(pattern: re.Pattern[str], text: str, default: str) -> str:
    match = pattern.search(text)
    return match.group(1) if match else default


def github_escape(text: str) -> str:
    return text.replace("%", "%25").replace("\r", "%0D").replace("\n", "%0A")


def emit_github_error(title: str, file_path: str, message: str) -> None:
    if os.environ.get("GITHUB_ACTIONS", "").lower() == "true":
        print(f"::error file={file_path},title={github_escape(title)}::{github_escape(message)}")


def compile_rtl() -> dict[str, str]:
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    RTL_DIR.mkdir(parents=True, exist_ok=True)
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
    if VVP.exists():
        VVP.unlink()
    command = [
        iverilog,
        "-g2012",
        "-Wall",
        "-s",
        "copper_prefetch_unit_open_tb",
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
        "status": "PASS" if code == 0 and errors == 0 and VVP.exists() else "FAIL",
        "warnings": str(warnings),
        "errors": str(errors if errors else (0 if code == 0 else 1)),
        "log_path": rel(log_path),
        "notes": first_error_line(output) or "Open-source smoke compile of COPPER unit with queue/disable/speculation checks.",
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
    failed = int(parse_assertion_count(ASSERTION_FAILED, output, "0"))
    failed_lines = sum(1 for line in output.splitlines() if line.startswith("COPPER_ASSERTION_FAIL"))
    failed = max(failed, failed_lines)
    completed = "COPPER open RTL directed tests completed" in output
    passed = parse_assertion_count(ASSERTION_PASSED, output, "0")
    if code != 0 and failed == 0:
        failed = 1
    return {
        "testbench": "copper_prefetch_unit_open_tb",
        "design": "copper_prefetch_unit_open",
        "tool": "vvp",
        "environment": ENVIRONMENT,
        "seed": "directed",
        "status": "PASS" if code == 0 and failed == 0 and completed else "FAIL",
        "cycles": "",
        "assertions_passed": passed if completed and failed == 0 else "0",
        "assertions_failed": str(failed),
        "log_path": rel(log_path),
        "notes": first_error_line(output) or "Directed reset, committed provenance update, speculative rejection, request generation, queue full behavior, disabled-COPPER behavior, permission block, no architectural output mutation.",
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
        if row_data["status"] == "FAIL":
            emit_github_error("COPPER RTL compile failed", row_data["log_path"], row_data["notes"])
        return 1 if row_data["status"] == "FAIL" else 0
    row_data = simulate_rtl()
    write_sim(row_data)
    print(f"wrote {SIM_CSV.relative_to(ROOT)}")
    if row_data["status"] == "FAIL":
        emit_github_error("COPPER RTL simulation failed", row_data["log_path"], row_data["notes"])
    return 1 if row_data["status"] == "FAIL" else 0


if __name__ == "__main__":
    raise SystemExit(main())

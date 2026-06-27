#!/usr/bin/env python3
"""Detect the COPPER reviewer toolchain and write a CSV status file."""

from __future__ import annotations

import csv
import importlib.metadata
import os
import platform
import shutil
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
RESULTS = ROOT / "research" / "results"
OUT = RESULTS / "toolchain_status.csv"


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


def run_version(command: list[str]) -> str:
    try:
        proc = subprocess.run(
            command,
            cwd=ROOT,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            timeout=8,
        )
    except Exception as exc:  # pragma: no cover - defensive
        return f"error: {exc}"
    text = proc.stdout.strip().splitlines()
    return scrub_text(text[0]) if text else f"exit={proc.returncode}"


def scrub_text(text: str) -> str:
    home = str(Path.home())
    root = str(ROOT)
    out = text.replace(home, "<home>").replace(root, "<repo>")
    return out.replace("\\", "/")


def source_label(value: str) -> str:
    if not value:
        return "PATH"
    return scrub_text(value)


def package_version(name: str) -> tuple[bool, str]:
    try:
        return True, importlib.metadata.version(name)
    except importlib.metadata.PackageNotFoundError:
        return False, ""


def tool_row(
    tool: str,
    required_for: str,
    required: str,
    command: list[str] | None = None,
    package: str | None = None,
    notes: str = "",
) -> dict[str, str]:
    if package:
        available, version = package_version(package)
        source = "python package"
    elif tool == "python3":
        available = True
        version = sys.version.split()[0]
        source = source_label(sys.executable)
    elif command:
        exe = shutil.which(command[0])
        available = exe is not None
        version = run_version([exe, *command[1:]]) if exe else ""
        source = source_label(exe or "")
    else:
        available = False
        version = ""
        source = "PATH"
    return {
        "environment": ENVIRONMENT,
        "tool": tool,
        "required_for": required_for,
        "available": "yes" if available else "no",
        "version": version,
        "required": required,
        "source": source,
        "notes": notes,
    }


def existing_rows(fieldnames: list[str]) -> list[dict[str, str]]:
    if not OUT.exists():
        return []
    with OUT.open(newline="", encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))
    normalized = []
    for row in rows:
        if not row.get("environment"):
            row["environment"] = "local_windows"
        normalized.append({field: row.get(field, "") for field in fieldnames})
    return normalized


def main() -> int:
    RESULTS.mkdir(parents=True, exist_ok=True)
    rows = [
        tool_row("python3", "all Python scripts", "required"),
        tool_row("pip", "Python package install", "required", [sys.executable, "-m", "pip", "--version"]),
        tool_row("make", "reviewer command entry points", "required", ["make", "--version"]),
        tool_row("gcc", "C workload build", "one-of-gcc-or-clang", ["gcc", "--version"]),
        tool_row("clang", "C workload build", "one-of-gcc-or-clang", ["clang", "--version"]),
        tool_row("g++", "C++ workload build", "required", ["g++", "--version"]),
        tool_row("cmake", "optional native workload builds", "optional", ["cmake", "--version"]),
        tool_row("iverilog", "open-source RTL compile/sim", "required-for-open-source-rtl", ["iverilog", "-V"]),
        tool_row("vvp", "Icarus simulation runtime", "required-for-open-source-rtl", ["vvp", "-V"]),
        tool_row("verilator", "alternate open-source RTL lint/sim", "optional", ["verilator", "--version"]),
        tool_row("yosys", "open-source generic synthesis", "required-for-open-source-synth", ["yosys", "-V"]),
        tool_row("nextpnr-ice40", "optional FPGA place/route", "optional", ["nextpnr-ice40", "--version"]),
        tool_row("nextpnr-ecp5", "optional FPGA place/route", "optional", ["nextpnr-ecp5", "--version"]),
        tool_row("latexmk", "paper build", "required-for-paper", ["latexmk", "-version"]),
        tool_row("pdflatex", "paper build fallback", "required-for-paper", ["pdflatex", "--version"]),
        tool_row("bibtex", "paper bibliography build", "required-for-paper", ["bibtex", "--version"]),
        tool_row("biber", "paper bibliography build if biblatex is used", "optional", ["biber", "--version"]),
        tool_row("vivado", "local XSim/Vivado reports", "optional", ["vivado", "-version"], notes="Vivado is licensed/local; absence blocks rerun, not report parsing."),
        tool_row("gem5", "full-system reruns", "optional-external", ["gem5", "--version"], notes="Full gem5 campaign remains external and is not installed by Docker."),
        tool_row("pytest", "Python tests if extended", "required", ["pytest", "--version"], package="pytest"),
        tool_row("numpy", "analysis scripts", "required", package="numpy"),
        tool_row("pandas", "analysis scripts", "required", package="pandas"),
        tool_row("matplotlib", "figures", "required", package="matplotlib"),
    ]
    fieldnames = ["environment", "tool", "required_for", "available", "version", "required", "source", "notes"]
    keep = [row for row in existing_rows(fieldnames) if row.get("environment") != ENVIRONMENT]
    with OUT.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(keep + rows)
    print(f"wrote {OUT.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

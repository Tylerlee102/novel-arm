#!/usr/bin/env python3
"""Build the LaTeX paper if pdflatex is available; otherwise record blocker."""

from __future__ import annotations

import csv
import os
import platform
import shutil
import subprocess
import textwrap
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
PAPER = ROOT / "research" / "paper"
RESULTS = ROOT / "research" / "results"
OUT = RESULTS / "paper_build_status.csv"
LOG_DIR = RESULTS / "logs" / "paper"


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


def count_word(text: str, word: str) -> int:
    return sum(1 for line in text.splitlines() if word.lower() in line.lower())


def first_error_line(text: str) -> str:
    for line in text.splitlines():
        lowered = line.lower()
        if line.startswith("!") or " error:" in lowered or lowered.startswith("error"):
            return line.strip()
    return ""


def github_escape(text: str) -> str:
    return text.replace("%", "%25").replace("\r", "%0D").replace("\n", "%0A")


def emit_github_error(file_path: str, message: str) -> None:
    if os.environ.get("GITHUB_ACTIONS", "").lower() == "true":
        print(f"::error file={file_path},title=COPPER paper build failed::{github_escape(message)}")


def build_reportlab_fallback(tex: Path, pdf: Path, log_path: Path) -> bool:
    try:
        from reportlab import rl_config
        from reportlab.lib.pagesizes import letter
        from reportlab.pdfgen import canvas
    except Exception as exc:
        log_path.write_text(f"latexmk/pdflatex not found and reportlab fallback unavailable: {exc}\n", encoding="utf-8")
        return False

    text = tex.read_text(encoding="utf-8", errors="replace")
    pdf.parent.mkdir(parents=True, exist_ok=True)
    rl_config.invariant = 1
    c = canvas.Canvas(str(pdf), pagesize=letter)
    width, height = letter
    x = 54
    y = height - 54
    c.setFont("Helvetica-Bold", 11)
    c.drawString(x, y, "COPPER paper source fallback render")
    y -= 18
    c.setFont("Helvetica", 8)
    for raw in text.splitlines():
        line = raw.expandtabs(2)
        wrapped = textwrap.wrap(line, width=115) or [""]
        for part in wrapped:
            if y < 54:
                c.showPage()
                c.setFont("Helvetica", 8)
                y = height - 54
            c.drawString(x, y, part[:115])
            y -= 10
    c.save()
    log_path.write_text(
        "latexmk/pdflatex not found on PATH.\n"
        "Generated a plain-text ReportLab fallback PDF from main.tex for artifact completeness.\n"
        "This is not a LaTeX typesetting pass; CI/Docker should still use latexmk when available.\n",
        encoding="utf-8",
    )
    return True


def existing_rows(fieldnames: list[str]) -> list[dict[str, str]]:
    if not OUT.exists():
        return []
    with OUT.open(newline="", encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))
    out = []
    for row in rows:
        if not row.get("environment"):
            row["environment"] = "local_windows"
        if not row.get("pdf_path") and row.get("pdf"):
            row["pdf_path"] = row.get("pdf", "")
        if not row.get("log_path") and row.get("log"):
            row["log_path"] = row.get("log", "")
        if row.get("status") == "PASS":
            pdf = row.get("pdf_path", "")
            log = row.get("log_path", "")
            if not pdf or not (ROOT / pdf).exists():
                continue
            if log and not (ROOT / log).exists():
                continue
        out.append({field: row.get(field, "") for field in fieldnames})
    return out


def write_status(status: str, pdf_path: str, latex_engine: str, errors: str, warnings: str, log_path: str, notes: str) -> None:
    RESULTS.mkdir(parents=True, exist_ok=True)
    fieldnames = ["environment", "status", "pdf_path", "latex_engine", "errors", "warnings", "log_path", "notes"]
    keep = [row for row in existing_rows(fieldnames) if row.get("environment") != ENVIRONMENT]
    row = {
        "environment": ENVIRONMENT,
        "status": status,
        "pdf_path": pdf_path,
        "latex_engine": latex_engine,
        "errors": errors,
        "warnings": warnings,
        "log_path": log_path,
        "notes": notes,
    }
    with OUT.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerows(keep + [row])


def main() -> int:
    tex = PAPER / "main.tex"
    pdf = PAPER / "main.pdf"
    log = PAPER / "main.log"
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    combined_log = LOG_DIR / "build_paper.log"
    latexmk = shutil.which("latexmk")
    pdflatex = shutil.which("pdflatex")
    if not tex.exists():
        combined_log.write_text("main.tex is missing; run build_conference_docs.py first.\n", encoding="utf-8")
        write_status("FAIL", "", "", "1", "0", rel(combined_log), "main.tex is missing; run build_conference_docs.py first.")
        return 1
    if not latexmk and not pdflatex:
        if build_reportlab_fallback(tex, pdf, combined_log) and pdf.exists():
            write_status(
                "PASS",
                rel(pdf),
                "reportlab-fallback",
                "0",
                "0",
                rel(combined_log),
                "LaTeX unavailable; generated plain-text fallback PDF. CI/Docker should use latexmk when available.",
            )
            print(f"built fallback {rel(pdf)}")
            return 0
        write_status("BLOCKED", "", "", "1", "0", rel(combined_log), "latexmk/pdflatex not found on PATH and fallback unavailable.")
        print("paper build blocked: latexmk/pdflatex not found")
        return 0
    if latexmk:
        command = [latexmk, "-pdf", "-file-line-error", "-interaction=nonstopmode", "-halt-on-error", "main.tex"]
        proc = subprocess.run(command, cwd=PAPER, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=120)
        combined = proc.stdout
        ok = proc.returncode == 0
        engine = "latexmk"
    else:
        command = [pdflatex, "-file-line-error", "-interaction=nonstopmode", "-halt-on-error", "main.tex"]
        first = subprocess.run(command, cwd=PAPER, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=60)
        second = subprocess.run(command, cwd=PAPER, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=60)
        combined = first.stdout + "\n" + second.stdout
        ok = first.returncode == 0 and second.returncode == 0
        engine = "pdflatex"
    combined_log.write_text(combined, encoding="utf-8")
    errors = str(count_word(combined, "error"))
    warnings = str(count_word(combined, "warning"))
    if ok and pdf.exists():
        write_status("PASS", rel(pdf), engine, errors, warnings, rel(combined_log), "LaTeX build completed.")
        print(f"built {rel(pdf)}")
        return 0
    first_error = first_error_line(combined)
    note = first_error or "LaTeX returned a non-zero status."
    write_status("FAIL", rel(pdf) if pdf.exists() else "", engine, errors or "1", warnings, rel(combined_log), note)
    emit_github_error(rel(combined_log), note)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())

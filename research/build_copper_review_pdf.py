#!/usr/bin/env python3
"""Build a readable COPPER review PDF directly from the paper Markdown."""

from __future__ import annotations

import html
import re
import textwrap
from pathlib import Path

from pypdf import PdfReader
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import (
    LongTable,
    PageBreak,
    Paragraph,
    Preformatted,
    SimpleDocTemplate,
    Spacer,
    TableStyle,
)


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "research" / "COPPER_FULL_PAPER.md"
OUT = ROOT / "research" / "results" / "COPPER_CONFERENCE_DRAFT_REVIEW.pdf"


def clean_inline(text: str) -> str:
    text = text.replace("**", "")
    text = text.replace("`", "")
    return text


def paragraph_text(text: str) -> str:
    return html.escape(clean_inline(text)).replace("&lt;br&gt;", "<br/>")


def split_table_row(line: str) -> list[str]:
    return [clean_inline(cell.strip()) for cell in line.strip().strip("|").split("|")]


def looks_like_separator(line: str) -> bool:
    return bool(re.match(r"^\s*\|?\s*:?-{3,}:?\s*(\|\s*:?-{3,}:?\s*)+\|?\s*$", line))


def table_widths(headers: list[str], available: float) -> list[float]:
    n = max(1, len(headers))
    if n <= 2:
        return [available / n] * n
    if n == 3:
        return [available * 0.30, available * 0.35, available * 0.35]
    if n <= 7:
        first = available * 0.20
        return [first] + [(available - first) / (n - 1)] * (n - 1)
    return [available / n] * n


def add_table(story: list, rows: list[list[str]], styles, available: float) -> None:
    if len(rows) < 2:
        return
    headers = rows[0]
    body = [row for row in rows[1:] if len(row) == len(headers)]
    if not body:
        return

    font_size = 3.4 if len(headers) > 7 else 4.25
    leading = font_size + 0.1
    cell_style = ParagraphStyle(
        "table_cell",
        parent=styles["BodyText"],
        fontName="Helvetica",
        fontSize=font_size,
        leading=leading,
        spaceAfter=0,
    )
    header_style = ParagraphStyle(
        "table_header",
        parent=cell_style,
        fontName="Helvetica-Bold",
        textColor=colors.HexColor("#1f4d78"),
    )
    data = [
        [Paragraph(paragraph_text(cell), header_style) for cell in headers],
    ]
    for row in body:
        data.append([Paragraph(paragraph_text(cell), cell_style) for cell in row])

    table = LongTable(
        data,
        colWidths=table_widths(headers, available),
        repeatRows=1,
        splitByRow=1,
        hAlign="LEFT",
    )
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#f2f4f7")),
                ("GRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#c9d1dc")),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 2),
                ("RIGHTPADDING", (0, 0), (-1, -1), 2),
                ("TOPPADDING", (0, 0), (-1, -1), 0.45),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 0.45),
            ]
        )
    )
    story.append(table)
    story.append(Spacer(1, 1.7))


def footer(canvas, doc) -> None:
    canvas.saveState()
    canvas.setFont("Helvetica", 7)
    canvas.setFillColor(colors.HexColor("#55606a"))
    canvas.drawCentredString(
        letter[0] / 2,
        0.32 * inch,
        f"COPPER research draft - page {doc.page}",
    )
    canvas.restoreState()


def build_story(styles, available: float) -> list:
    lines = SRC.read_text(encoding="utf-8").splitlines()
    story: list = []
    para: list[str] = []
    table_rows: list[list[str]] = []
    code_lines: list[str] = []
    in_code = False
    skip_artifact_summary = False
    in_references = False

    def flush_para() -> None:
        if not para:
            return
        text = " ".join(item.strip() for item in para).strip()
        para.clear()
        if text:
            story.append(Paragraph(paragraph_text(text), styles["PaperBody"]))
            story.append(Spacer(1, 0.95))

    def flush_table() -> None:
        if table_rows:
            add_table(story, table_rows, styles, available)
            table_rows.clear()

    title = clean_inline(lines[0].lstrip("# "))
    story.append(Paragraph(paragraph_text(title), styles["PaperTitle"]))
    story.append(
        Paragraph(
            "Full research draft with ARM/AArch64 gem5 SE, ARM64 full-system CTLW timing ROI, Vivado RTL, and prior-art review",
            styles["PaperSubtitle"],
        )
    )
    story.append(Spacer(1, 4))

    for raw in lines[1:]:
        line = raw.rstrip()
        heading_probe = re.match(r"^(#{2,4})\s+(.*)$", line)
        if heading_probe and heading_probe.group(2).strip() == "Artifact Summary":
            flush_para()
            flush_table()
            skip_artifact_summary = True
            continue
        if (
            heading_probe
            and heading_probe.group(1) == "##"
            and heading_probe.group(2).strip() == "References"
        ):
            skip_artifact_summary = False
            in_references = True
        elif heading_probe and heading_probe.group(1) == "##":
            in_references = False
        if skip_artifact_summary:
            continue

        if line.startswith("```"):
            if in_code:
                flush_para()
                wrapped = []
                for code_line in code_lines:
                    wrapped.extend(textwrap.wrap(code_line, width=96) or [""])
                story.append(Preformatted("\n".join(wrapped), styles["PaperCode"]))
                story.append(Spacer(1, 2.2))
                code_lines.clear()
                in_code = False
            else:
                flush_para()
                flush_table()
                in_code = True
            continue
        if in_code:
            code_lines.append(line)
            continue

        if line.startswith("|") and "|" in line[1:]:
            flush_para()
            if looks_like_separator(line):
                continue
            table_rows.append(split_table_row(line))
            continue
        flush_table()

        if not line.strip():
            flush_para()
            continue

        heading = re.match(r"^(#{2,4})\s+(.*)$", line)
        if heading:
            flush_para()
            level = len(heading.group(1))
            style = styles["PaperH2"] if level == 2 else styles["PaperH3"]
            story.append(Paragraph(paragraph_text(heading.group(2)), style))
            story.append(Spacer(1, 1.35))
            continue

        bullet = re.match(r"^\s*-\s+(.*)$", line)
        if bullet:
            flush_para()
            story.append(Paragraph(paragraph_text("- " + bullet.group(1)), styles["PaperBody"]))
            continue

        number = re.match(r"^\s*\d+\.\s+(.*)$", line)
        if number:
            flush_para()
            text = clean_inline(line if in_references else number.group(1))
            prefix = "" if in_references else "- "
            story.append(Paragraph(paragraph_text(prefix + text), styles["PaperBodySmall"]))
            continue

        para.append(line)

    flush_para()
    flush_table()
    return story


def build() -> None:
    OUT.parent.mkdir(parents=True, exist_ok=True)
    styles = getSampleStyleSheet()
    styles.add(
        ParagraphStyle(
            "PaperTitle",
            parent=styles["Title"],
            fontName="Helvetica-Bold",
            fontSize=12.3,
            leading=13.2,
            alignment=TA_CENTER,
            textColor=colors.HexColor("#1f2d3d"),
            spaceAfter=3,
        )
    )
    styles.add(
        ParagraphStyle(
            "PaperSubtitle",
            parent=styles["BodyText"],
            fontName="Helvetica",
            fontSize=6.8,
            leading=7.3,
            alignment=TA_CENTER,
            textColor=colors.HexColor("#55606a"),
        )
    )
    styles.add(
        ParagraphStyle(
            "PaperH2",
            parent=styles["Heading2"],
            fontName="Helvetica-Bold",
            fontSize=7.7,
            leading=8.05,
            textColor=colors.HexColor("#2e74b5"),
            spaceBefore=1.4,
            spaceAfter=0.45,
        )
    )
    styles.add(
        ParagraphStyle(
            "PaperH3",
            parent=styles["Heading3"],
            fontName="Helvetica-Bold",
            fontSize=6.75,
            leading=7.05,
            textColor=colors.HexColor("#1f4d78"),
            spaceBefore=1.5,
            spaceAfter=0.45,
        )
    )
    styles.add(
        ParagraphStyle(
            "PaperBody",
            parent=styles["BodyText"],
            fontName="Helvetica",
            fontSize=5.72,
            leading=5.92,
            textColor=colors.HexColor("#1f2d3d"),
            spaceAfter=0.25,
        )
    )
    styles.add(
        ParagraphStyle(
            "PaperBodySmall",
            parent=styles["PaperBody"],
            fontSize=5.45,
            leading=5.65,
        )
    )
    styles.add(
        ParagraphStyle(
            "PaperCode",
            parent=styles["Code"],
            fontName="Courier",
            fontSize=4.9,
            leading=5.2,
            leftIndent=8,
            textColor=colors.HexColor("#23272f"),
        )
    )

    doc = SimpleDocTemplate(
        str(OUT),
        pagesize=letter,
        rightMargin=0.24 * inch,
        leftMargin=0.24 * inch,
        topMargin=0.2 * inch,
        bottomMargin=0.24 * inch,
    )
    story = build_story(styles, doc.width)
    doc.build(story, onFirstPage=footer, onLaterPages=footer)
    pages = len(PdfReader(str(OUT)).pages)
    print(f"{OUT}")
    print(f"pages={pages}")


if __name__ == "__main__":
    build()

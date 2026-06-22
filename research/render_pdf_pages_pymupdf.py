#!/usr/bin/env python3
"""Render a PDF into per-page PNGs plus a compact contact sheet."""

from __future__ import annotations

import argparse
import math
import sys
from pathlib import Path


try:
    import fitz as pymupdf  # type: ignore  # noqa: E402
except ImportError:
    ROOT = Path(__file__).resolve().parents[1]
    VENDOR = ROOT / "research" / "_vendor" / "pymupdf"
    if VENDOR.exists():
        sys.path.insert(0, str(VENDOR))
    try:
        import pymupdf  # type: ignore  # noqa: E402
    except ImportError:
        import fitz as pymupdf  # type: ignore  # noqa: E402
from PIL import Image  # type: ignore  # noqa: E402


def render(pdf: Path, out_dir: Path, dpi: int) -> None:
    pages_dir = out_dir / "pages"
    pages_dir.mkdir(parents=True, exist_ok=True)
    doc = pymupdf.open(pdf)
    zoom = dpi / 72.0
    matrix = pymupdf.Matrix(zoom, zoom)
    page_paths: list[Path] = []

    for idx, page in enumerate(doc, start=1):
        pix = page.get_pixmap(matrix=matrix, alpha=False)
        out = pages_dir / f"page_{idx:02d}.png"
        pix.save(out)
        page_paths.append(out)

    thumbs: list[Image.Image] = []
    for path in page_paths:
        im = Image.open(path).convert("RGB")
        im.thumbnail((360, 480))
        thumbs.append(im.copy())

    cols = 2 if len(thumbs) <= 6 else 4
    rows = max(1, math.ceil(len(thumbs) / cols))
    cell_w, cell_h = 390, 525
    sheet = Image.new("RGB", (cols * cell_w, rows * cell_h), "white")
    for idx, thumb in enumerate(thumbs):
        x = (idx % cols) * cell_w + (cell_w - thumb.width) // 2
        y = (idx // cols) * cell_h + 22
        sheet.paste(thumb, (x, y))
    sheet.save(out_dir / "contact_sheet.png")

    print(f"pdf={pdf}")
    print(f"pages={len(page_paths)}")
    print(f"out_dir={out_dir}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("pdf", type=Path)
    parser.add_argument("out_dir", type=Path)
    parser.add_argument("--dpi", type=int, default=144)
    args = parser.parse_args()
    render(args.pdf, args.out_dir, args.dpi)


if __name__ == "__main__":
    main()

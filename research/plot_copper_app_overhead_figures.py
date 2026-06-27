#!/usr/bin/env python3
"""Generate paper-ready application overhead figures for COPPER."""

from __future__ import annotations

import csv
import textwrap
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Patch


ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "research" / "results"
CSV_IN = RESULTS / "copper_prefetch_traffic_overhead_20260616.csv"
FIG_DIR = RESULTS / "figures"
INDEX_OUT = FIG_DIR / "COPPER_APP_FIGURE_INDEX_20260616.md"

TOKENS = {
    "surface": "#FCFCFD",
    "panel": "#FFFFFF",
    "ink": "#1F2430",
    "muted": "#6F768A",
    "grid": "#E6E8F0",
    "axis": "#D7DBE7",
}

COLORS = {
    "naive": {"base": "#C5CAD3", "dark": "#464C55"},
    "copper": {"base": "#A3BEFA", "dark": "#2E4780"},
    "spp": {"base": "#FFE15B", "dark": "#736422"},
    "slack": {"base": "#A3D576", "dark": "#386411"},
    "orange": {"base": "#F0986E", "dark": "#804126"},
}

POLICY_LABELS = {
    "naive": "Naive DMP",
    "copper_clpd64k_peb": "COPPER",
    "spp": "SPP",
    "spp_copper_slack": "SPP+COPPER slack",
}

POLICY_COLORS = {
    "naive": COLORS["naive"],
    "copper_clpd64k_peb": COLORS["copper"],
    "spp": COLORS["spp"],
    "spp_copper_slack": COLORS["slack"],
}

WORKLOAD_ORDER = [
    "sqlite_medium",
    "sqlite_stress",
    "lua_medium",
    "lua_stress",
    "duktape_medium",
    "duktape_stress",
    "yyjson_medium",
    "yyjson_stress",
    "jsonsqlite_medium",
    "jsonsqlite_stress",
    "cachesvc_small",
    "cachesvc_medium",
]


def read_rows() -> list[dict[str, str]]:
    with CSV_IN.open("r", encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh))


def by_workload_policy(rows: list[dict[str, str]]) -> dict[tuple[str, str], dict[str, str]]:
    return {(row["workload"], row["policy"]): row for row in rows}


def as_float(row: dict[str, str], field: str) -> float:
    value = row.get(field, "")
    return float(value) if value not in {"", None} else 0.0


def fmt_pct1(value: float) -> str:
    if abs(value) < 0.05:
        value = 0.0
    return f"{value:.1f}%"


def label_workload(name: str) -> str:
    if name == "jsonsqlite_medium":
        return "JSON+SQLite medium"
    if name == "jsonsqlite_stress":
        return "JSON+SQLite stress"
    if name == "cachesvc_small":
        return "Cache-service small"
    if name == "cachesvc_medium":
        return "Cache-service medium"
    family, scale = name.split("_", 1)
    family_label = {"sqlite": "SQLite", "lua": "Lua", "duktape": "Duktape", "yyjson": "yyjson"}[family]
    return f"{family_label} {scale}"


def style_axes(ax) -> None:
    ax.set_facecolor(TOKENS["panel"])
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_color(TOKENS["axis"])
    ax.spines["bottom"].set_color(TOKENS["axis"])
    ax.tick_params(axis="both", colors=TOKENS["muted"], labelsize=9, length=0)
    ax.xaxis.grid(True, color=TOKENS["grid"], linewidth=0.8)
    ax.yaxis.grid(False)


def add_header(fig, ax, title: str, subtitle: str) -> None:
    title = textwrap.fill(title, width=76, break_long_words=False)
    subtitle = textwrap.fill(subtitle, width=116, break_long_words=False)
    ax.set_title("")
    fig.subplots_adjust(top=0.82, left=0.18, right=0.96, bottom=0.12)
    left = ax.get_position().x0
    fig.text(left, 0.965, title, ha="left", va="top",
             fontsize=14, fontweight="semibold", color=TOKENS["ink"])
    fig.text(left, 0.91, subtitle, ha="left", va="top",
             fontsize=9.5, color=TOKENS["muted"])


def save(fig, stem: str) -> tuple[Path, Path]:
    FIG_DIR.mkdir(parents=True, exist_ok=True)
    png = FIG_DIR / f"{stem}.png"
    svg = FIG_DIR / f"{stem}.svg"
    fig.savefig(png, dpi=220, facecolor=TOKENS["surface"], bbox_inches="tight")
    fig.savefig(svg, facecolor=TOKENS["surface"], bbox_inches="tight")
    plt.close(fig)
    return png, svg


def plot_runtime(rows: list[dict[str, str]]) -> tuple[Path, Path]:
    data = by_workload_policy(rows)
    policies = ["naive", "copper_clpd64k_peb", "spp", "spp_copper_slack"]
    fig, ax = plt.subplots(figsize=(10.6, 6.2), facecolor=TOKENS["surface"])
    style_axes(ax)

    group_gap = 0.92
    bar_h = 0.17
    offsets = [-0.27, -0.09, 0.09, 0.27]
    y_base = [i * group_gap for i in range(len(WORKLOAD_ORDER))]
    for policy, offset in zip(policies, offsets):
        values = [
            as_float(data[(workload, policy)], "sim_ticks_delta_vs_none_pct")
            for workload in WORKLOAD_ORDER
        ]
        y = [base + offset for base in y_base]
        family = POLICY_COLORS[policy]
        bars = ax.barh(y, values, height=bar_h, color=family["base"],
                       edgecolor=family["dark"], linewidth=0.8,
                       label=POLICY_LABELS[policy])
        for bar, value in zip(bars, values):
            x = value - 0.35 if value < 0 else value + 0.35
            ha = "right" if value < 0 else "left"
            ax.text(x, bar.get_y() + bar.get_height() / 2,
                    fmt_pct1(value), ha=ha, va="center",
                    fontsize=7.6, color=TOKENS["ink"])

    ax.set_yticks(y_base, [label_workload(w) for w in WORKLOAD_ORDER])
    ax.axvline(0, color=TOKENS["ink"], linewidth=0.9)
    ax.set_xlabel("Tick delta versus no prefetching (%)", color=TOKENS["ink"])
    ax.set_xlim(-35, 3)
    ax.invert_yaxis()
    ax.legend(loc="lower left", bbox_to_anchor=(0, 1.02), frameon=False,
              ncol=4, fontsize=8.5, borderaxespad=0)
    add_header(
        fig,
        ax,
        "Runtime deltas show COPPER is modest, while SPP is the raw-speed baseline",
        "Twelve full-system AArch64 app points. Negative tick delta is faster than no prefetching; labels show percent change.",
    )
    return save(fig, "copper_app_runtime_delta")


def plot_ctlw(rows: list[dict[str, str]]) -> tuple[Path, Path]:
    data = by_workload_policy(rows)
    policies = ["copper_clpd64k_peb", "spp_copper_slack"]
    fig, ax = plt.subplots(figsize=(9.4, 5.7), facecolor=TOKENS["surface"])
    style_axes(ax)

    group_gap = 0.75
    bar_h = 0.22
    offsets = [-0.13, 0.13]
    y_base = [i * group_gap for i in range(len(WORKLOAD_ORDER))]
    for policy, offset in zip(policies, offsets):
        values = []
        for workload in WORKLOAD_ORDER:
            naive = as_float(data[(workload, "naive")], "targetLineWitnessMisses")
            current = as_float(data[(workload, policy)], "targetLineWitnessMisses")
            values.append(100.0 * (1.0 - current / naive) if naive else 0.0)
        y = [base + offset for base in y_base]
        family = POLICY_COLORS[policy]
        bars = ax.barh(y, values, height=bar_h, color=family["base"],
                       edgecolor=family["dark"], linewidth=0.8,
                       label=POLICY_LABELS[policy])
        for bar, value in zip(bars, values):
            ax.text(min(value + 1.0, 99.0),
                    bar.get_y() + bar.get_height() / 2,
                    f"{value:.1f}%", ha="left", va="center",
                    fontsize=8, color=TOKENS["ink"])

    ax.set_yticks(y_base, [label_workload(w) for w in WORKLOAD_ORDER])
    ax.set_xlim(0, 105)
    ax.set_xlabel("CTLW miss reduction versus naive DMP (%)", color=TOKENS["ink"])
    ax.invert_yaxis()
    ax.legend(loc="lower left", bbox_to_anchor=(0, 1.02), frameon=False,
              ncol=2, fontsize=8.5, borderaxespad=0)
    add_header(
        fig,
        ax,
        "COPPER sharply reduces target-line witness misses",
        "Reduction is computed against naive DMP on the same workload; higher is better. No translation faults were observed.",
    )
    return save(fig, "copper_app_ctlw_reduction")


def plot_traffic(rows: list[dict[str, str]]) -> tuple[Path, Path]:
    data = by_workload_policy(rows)
    values = [
        as_float(data[(workload, "copper_clpd64k_peb")],
                 "membus_pkt_size_total_delta_vs_none_pct")
        for workload in WORKLOAD_ORDER
    ]
    ordered = sorted(zip(WORKLOAD_ORDER, values), key=lambda item: item[1])
    fig, ax = plt.subplots(figsize=(8.8, 5.2), facecolor=TOKENS["surface"])
    style_axes(ax)

    family = COLORS["orange"]
    y = list(range(len(ordered)))
    min_value = min(values)
    max_value = max(values)
    pad = max(0.2, 0.06 * (max_value - min_value))
    bars = ax.barh(y, [v for _, v in ordered], height=0.46,
                   color=family["base"], edgecolor=family["dark"], linewidth=0.8)
    for bar, (_, value) in zip(bars, ordered):
        if value < 0:
            label_x = value - pad * 0.45
            ha = "right"
        else:
            label_x = value + pad * 0.45
            ha = "left"
        ax.text(label_x, bar.get_y() + bar.get_height() / 2,
                f"{value:.2f}%", ha=ha, va="center", fontsize=8,
                color=TOKENS["ink"])

    mean_value = sum(values) / len(values)
    ax.axvline(mean_value, color=TOKENS["ink"], linestyle=":", linewidth=1.0)
    ax.text(mean_value + 0.08, -0.55, f"mean {mean_value:.2f}%",
            ha="left", va="center", fontsize=8, color=TOKENS["ink"])
    ax.axvline(0, color=TOKENS["axis"], linewidth=0.9)
    ax.set_yticks(y, [label_workload(w) for w, _ in ordered])
    ax.set_xlim(min(0.0, min_value) - pad, max(0.0, max_value) + pad)
    ax.set_xlabel("Memory-bus byte delta versus no prefetching (%)",
                  color=TOKENS["ink"])
    ax.invert_yaxis()
    add_header(
        fig,
        ax,
        "Standalone COPPER keeps bus-byte deltas small on app workloads",
        "Twelve full-system AArch64 app points. Bars show memory-bus byte delta for COPPER CLPD-64K+PEB versus no prefetching.",
    )
    return save(fig, "copper_app_bus_overhead")


def write_index(paths: list[tuple[str, tuple[Path, Path]]]) -> None:
    lines = [
        "# COPPER Application Figure Index",
        "",
        "Source data: `research/results/copper_prefetch_traffic_overhead_20260616.csv`.",
        "",
        "| Figure | PNG | SVG | Purpose |",
        "|---|---|---|---|",
        "| Full baseline runtime matrix | `research/results/figures/copper_app_full_baseline_runtime.png` | `research/results/figures/copper_app_full_baseline_runtime.svg` | Shows naive DMP, standalone COPPER, stride, DCPT, AMPM, SPP, and SPP+COPPER slack on the twelve public app points. |",
    ]
    purposes = {
        "Runtime deltas": "Compares raw timing behavior across no-prefetch-normalized app runs.",
        "CTLW reduction": "Shows authority-risk reduction versus naive DMP.",
        "Bus overhead": "Shows standalone COPPER memory-bus byte deltas versus no prefetching.",
    }
    for label, (png, svg) in paths:
        png_rel = png.relative_to(ROOT).as_posix()
        svg_rel = svg.relative_to(ROOT).as_posix()
        lines.append(
            f"| {label} | `{png_rel}` | `{svg_rel}` | {purposes[label]} |"
        )
    lines.extend(
        [
            "",
            "Notes:",
            "",
            "- Static charts were rendered with Matplotlib because Seaborn is not installed in the local bundled Python runtime.",
            "- The figures intentionally keep SPP framed as the raw-performance baseline and standalone COPPER as the authority/low-overhead path.",
            "",
        ]
    )
    INDEX_OUT.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    plt.rcParams.update({
        "font.family": "sans-serif",
        "font.sans-serif": ["Aptos", "Inter", "Segoe UI", "DejaVu Sans", "Arial"],
        "font.size": 9,
    })
    rows = read_rows()
    paths = [
        ("Runtime deltas", plot_runtime(rows)),
        ("CTLW reduction", plot_ctlw(rows)),
        ("Bus overhead", plot_traffic(rows)),
    ]
    write_index(paths)
    for _, (png, svg) in paths:
        print(png)
        print(svg)
    print(INDEX_OUT)


if __name__ == "__main__":
    main()

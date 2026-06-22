#!/usr/bin/env python3
"""Plot the full app runtime baseline matrix as a static figure."""

from __future__ import annotations

import csv
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D


ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "research" / "results"
FIG_DIR = RESULTS / "figures"
OUT_PNG = FIG_DIR / "copper_app_full_baseline_runtime.png"
OUT_SVG = FIG_DIR / "copper_app_full_baseline_runtime.svg"

WORKLOADS = [
    ("SQLite medium", RESULTS / "gem5_arm_ubuntu_fs_sqlite_app" / "sqlite_app_medium_summary.csv"),
    ("SQLite stress", RESULTS / "gem5_arm_ubuntu_fs_sqlite_app" / "sqlite_app_stress_summary.csv"),
    ("Lua medium", RESULTS / "gem5_arm_ubuntu_fs_lua_app" / "lua_app_medium_summary.csv"),
    ("Lua stress", RESULTS / "gem5_arm_ubuntu_fs_lua_app" / "lua_app_stress_summary.csv"),
    ("Duktape medium", RESULTS / "gem5_arm_ubuntu_fs_duktape_app" / "duktape_app_medium_summary.csv"),
    ("Duktape stress", RESULTS / "gem5_arm_ubuntu_fs_duktape_app" / "duktape_app_stress_summary.csv"),
    ("yyjson medium", RESULTS / "gem5_arm_ubuntu_fs_yyjson_app" / "yyjson_app_medium_summary.csv"),
    ("yyjson stress", RESULTS / "gem5_arm_ubuntu_fs_yyjson_app" / "yyjson_app_stress_summary.csv"),
    (
        "JSON+SQLite medium",
        RESULTS / "gem5_arm_ubuntu_fs_jsonsqlite_app" / "jsonsqlite_app_medium_summary.csv",
    ),
    (
        "JSON+SQLite stress",
        RESULTS / "gem5_arm_ubuntu_fs_jsonsqlite_app" / "jsonsqlite_app_stress_summary.csv",
    ),
    (
        "Cache-service small",
        RESULTS / "gem5_arm_ubuntu_fs_cachesvc_app" / "cachesvc_app_small_summary.csv",
    ),
    (
        "Cache-service medium",
        RESULTS / "gem5_arm_ubuntu_fs_cachesvc_app" / "cachesvc_app_medium_key_summary.csv",
    ),
]

POLICIES = [
    ("naive", "Naive DMP", "#F5BACC", "#8A3A6F", "o"),
    ("copper_clpd64k_peb", "COPPER", "#F0986E", "#804126", "s"),
    ("stride", "Stride", "#E2E5EA", "#464C55", "^"),
    ("dcpt", "DCPT", "#C5CAD3", "#464C55", "v"),
    ("ampm", "AMPM", "#F4F5F7", "#464C55", "D"),
    ("spp", "SPP", "#A3BEFA", "#2E4780", "P"),
    ("spp_copper_slack", "SPP+COPPER slack", "#FFE15B", "#736422", "*"),
]

TOKENS = {
    "surface": "#FCFCFD",
    "panel": "#FFFFFF",
    "ink": "#1F2430",
    "muted": "#6F768A",
    "grid": "#E6E8F0",
    "axis": "#D7DBE7",
}


def read_delta(path: Path) -> dict[str, float]:
    with path.open("r", encoding="utf-8", newline="") as fh:
        return {
            row["policy"]: float(row["tick_delta_vs_none_pct"])
            for row in csv.DictReader(fh)
        }


def main() -> None:
    FIG_DIR.mkdir(parents=True, exist_ok=True)
    data = [(label, read_delta(path)) for label, path in WORKLOADS]

    fig, ax = plt.subplots(figsize=(12.8, 7.2), facecolor=TOKENS["surface"])
    ax.set_facecolor(TOKENS["panel"])

    y_positions = list(range(len(data)))
    offsets = {
        "naive": -0.27,
        "copper_clpd64k_peb": -0.18,
        "stride": -0.09,
        "dcpt": 0.0,
        "ampm": 0.09,
        "spp": 0.18,
        "spp_copper_slack": 0.27,
    }

    for y, (workload, rows) in zip(y_positions, data):
        ax.axhline(y, color=TOKENS["grid"], linewidth=0.8, zorder=0)
        if "spp" in rows and "spp_copper_slack" in rows:
            ax.plot(
                [rows["spp"], rows["spp_copper_slack"]],
                [y + offsets["spp"], y + offsets["spp_copper_slack"]],
                color="#736422",
                linewidth=1.0,
                alpha=0.9,
                zorder=2,
            )

    for policy, label, fill, edge, marker in POLICIES:
        xs = [rows[policy] for _, rows in data]
        ys = [y + offsets[policy] for y in y_positions]
        ax.scatter(
            xs,
            ys,
            s=78 if policy != "spp_copper_slack" else 122,
            marker=marker,
            facecolor=fill,
            edgecolor=edge,
            linewidth=1.0,
            label=label,
            zorder=3,
        )

    ax.axvline(0, color=TOKENS["ink"], linewidth=1.0)
    ax.set_yticks(y_positions)
    ax.set_yticklabels([label for label, _ in data], color=TOKENS["ink"])
    ax.invert_yaxis()
    ax.set_xlim(-34.5, 1.5)
    ax.set_xlabel("Runtime delta vs no prefetching (%)", color=TOKENS["ink"])
    ax.xaxis.grid(True, color=TOKENS["grid"], linewidth=0.8)
    ax.yaxis.grid(False)
    ax.tick_params(axis="x", colors=TOKENS["muted"])
    ax.tick_params(axis="y", length=0)
    for spine in ["top", "right"]:
        ax.spines[spine].set_visible(False)
    ax.spines["left"].set_color(TOKENS["axis"])
    ax.spines["bottom"].set_color(TOKENS["axis"])

    title = "SPP wins app speed; SPP+COPPER slack tracks it with authority checks"
    subtitle = (
        "Twelve AArch64 full-system app points: SQLite/Lua/Duktape/yyjson medium/stress plus JSON+SQLite medium/stress service composition and cache-service hash/LRU scale points; negative is faster than no prefetching. "
        "Markers compare naive DMP, standalone COPPER, stride, DCPT, AMPM, SPP, and SPP+COPPER slack."
    )
    fig.subplots_adjust(top=0.78, left=0.18, right=0.985, bottom=0.12)
    fig.text(0.18, 0.965, title, ha="left", va="top", fontsize=14, fontweight="semibold", color=TOKENS["ink"])
    fig.text(0.18, 0.915, subtitle, ha="left", va="top", fontsize=9, color=TOKENS["muted"], wrap=True)

    handles = [
        Line2D(
            [0],
            [0],
            marker=marker,
            linestyle="",
            markersize=8,
            markerfacecolor=fill,
            markeredgecolor=edge,
            label=label,
        )
        for _, label, fill, edge, marker in POLICIES
    ]
    ax.legend(
        handles=handles,
        loc="lower left",
        bbox_to_anchor=(0, 1.02),
        frameon=False,
        ncol=4,
        fontsize=8.5,
        handletextpad=0.45,
        columnspacing=1.1,
        borderaxespad=0,
    )
    ax.text(
        0.0,
        -0.11,
        "Source: gem5 ARM64 full-system app summaries generated 2026-06-17. Deltas are simulated ROI ticks vs no prefetch.",
        transform=ax.transAxes,
        ha="left",
        va="top",
        fontsize=8,
        color=TOKENS["muted"],
    )

    fig.savefig(OUT_PNG, dpi=180, bbox_inches="tight")
    fig.savefig(OUT_SVG, bbox_inches="tight")
    print(OUT_PNG)
    print(OUT_SVG)


if __name__ == "__main__":
    main()

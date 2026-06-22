#!/usr/bin/env python3
"""Cross-build a serial Olden pointer-benchmark subset for ARM64 gem5."""

from __future__ import annotations

import argparse
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CLANG = ROOT / "tools" / "msys64" / "ucrt64" / "bin" / "clang.exe"
SYSROOT = ROOT / "tools" / "arm64_ubuntu_24_sysroot"
OLDEN = ROOT / "external" / "olden"
OLDEN_V101 = ROOT / "external" / "olden_v101" / "olden_v1.01" / "benchmarks"
RUNTIME = ROOT / "external" / "olden_v101" / "olden_v1.01" / "runtime"
COMPAT = ROOT / "research" / "olden_compat"
LOG_DIR = ROOT / "research" / "results" / "olden_aarch64_build"
GENERATED = ROOT / "research" / "generated" / "olden_checked"


BENCHMARKS: dict[str, dict[str, object]] = {
    "treeadd": {
        "root": OLDEN_V101 / "treeadd",
        "sources": ["args.c", "node.c", "par-alloc.c"],
        "compat": True,
    },
    "bisort": {
        "root": OLDEN / "bisort" / "src",
        "sources": ["args.c", "bitonic.c"],
        "compat": False,
    },
    "mst": {
        "root": OLDEN / "mst" / "src",
        "sources": ["args.c", "hash.c", "main.c", "makegraph.c"],
        "compat": False,
    },
    "health": {
        "root": OLDEN / "health" / "src",
        "sources": ["args.c", "health.c", "list.c", "poisson.c"],
        "compat": False,
    },
}


def make_checked_bisort_source() -> Path:
    """Create a validation-only bisort source with compact result checks."""
    original = OLDEN / "bisort" / "src"
    generated = GENERATED / "bisort"
    generated.mkdir(parents=True, exist_ok=True)
    (generated / "args.c").write_text(
        (original / "args.c").read_text(encoding="utf-8"),
        encoding="utf-8",
    )
    for header in ["node.h", "proc.h"]:
        (generated / header).write_text(
            (original / header).read_text(encoding="utf-8"),
            encoding="utf-8",
        )
    text = (original / "bitonic.c").read_text(encoding="utf-8")
    helper = r'''
struct copper_bisort_fingerprint {
  int count;
  long long checksum;
  unsigned long long hist_hash;
  int min_value;
  int max_value;
  int hist[100];
};

void CopperBisortConsume(value, state)
int value;
struct copper_bisort_fingerprint *state;
{
  int bin;
  if (state->count == 0) {
    state->min_value = value;
    state->max_value = value;
  } else {
    if (value < state->min_value) state->min_value = value;
    if (value > state->max_value) state->max_value = value;
  }
  state->count++;
  state->checksum += value;
  bin = value;
  if (bin >= 0 && bin < 100) {
    state->hist[bin]++;
  }
}

void CopperBisortWalk(root, state)
HANDLE *root;
struct copper_bisort_fingerprint *state;
{
  if (root == NIL) return;
  CopperBisortWalk(root->left, state);
  CopperBisortConsume(root->value, state);
  CopperBisortWalk(root->right, state);
}

void CopperBisortFingerprint(phase, root, spring_value, expected)
char *phase;
HANDLE *root;
int spring_value;
int expected;
{
  int i;
  struct copper_bisort_fingerprint state;
  state.count = 0;
  state.checksum = 0;
  state.hist_hash = 1469598103934665603ULL;
  state.min_value = 0;
  state.max_value = 0;
  for (i = 0; i < 100; i++) state.hist[i] = 0;
  CopperBisortWalk(root, &state);
  CopperBisortConsume(spring_value, &state);
  for (i = 0; i < 100; i++) {
    state.hist_hash = (state.hist_hash ^ (unsigned long long)state.hist[i]) *
                      1099511628211ULL;
  }
  printf("BISORT_FINGERPRINT phase=%s count=%d expected=%d checksum=%lld hist_hash=%llu min=%d max=%d spring=%d\n",
         phase, state.count, expected, state.checksum, state.hist_hash,
         state.min_value, state.max_value, spring_value);
}
'''
    text = text.replace("\nint main(int argc, char **argv) {", f"\n{helper}\nint main(int argc, char **argv) {{")
    text = text.replace(
        "  printf(\"**************************************\\n\");",
        "  CopperBisortFingerprint(\"initial\", h, sval, n);\n  printf(\"**************************************\\n\");",
        1,
    )
    text = text.replace(
        "  sval=Bisort(h,sval,0);\n\n  if (flag) {",
        "  sval=Bisort(h,sval,0);\n  CopperBisortFingerprint(\"forward\", h, sval, n);\n\n  if (flag) {",
    )
    text = text.replace(
        "  sval=Bisort(h,sval,1);\n\n  if (flag) {",
        "  sval=Bisort(h,sval,1);\n  CopperBisortFingerprint(\"backward\", h, sval, n);\n\n  if (flag) {",
    )
    (generated / "bitonic.c").write_text(text, encoding="utf-8")
    return generated


def build_one(
    name: str,
    out_dir: Path,
    log_dir: Path,
    random_alloc: bool,
    checked: bool,
) -> bool:
    out_dir.mkdir(parents=True, exist_ok=True)
    log_dir.mkdir(parents=True, exist_ok=True)
    spec = BENCHMARKS[name]
    src_dir = spec["root"]  # type: ignore[assignment]
    if checked and name == "bisort":
        src_dir = make_checked_bisort_source()
    sources_spec = spec["sources"]  # type: ignore[assignment]
    use_compat = bool(spec["compat"])
    out = out_dir / name
    sources = [str(src_dir / item) for item in sources_spec]
    cmd = [
        str(CLANG),
        "--target=aarch64-linux-gnu",
        f"--sysroot={SYSROOT}",
        "-fuse-ld=lld",
        "-std=gnu89",
        "-O2",
        "-DPLAIN",
        "-Wno-implicit-int",
        "-Wno-implicit-function-declaration",
        "-Wno-int-conversion",
        "-Wno-incompatible-pointer-types",
        "-Wno-incompatible-library-redeclaration",
        "-Wno-return-type",
        f"-I{src_dir}",
        *sources,
        "-lm",
        "-o",
        str(out),
    ]
    if random_alloc:
        cmd.insert(cmd.index(f"-I{src_dir}"), "-Dmalloc=copper_olden_malloc")
        cmd.insert(cmd.index("-lm"), str(COMPAT / "olden_random_alloc.c"))
    if use_compat:
        cmd.insert(cmd.index(f"-I{src_dir}"), "-DPLAIN")
        cmd.insert(cmd.index(f"-I{src_dir}"), f"-I{RUNTIME}")
        cmd.insert(cmd.index(f"-I{src_dir}"), f"-I{COMPAT}")
        cmd.insert(cmd.index("-lm"), str(COMPAT / "olden_runtime_compat.c"))
    proc = subprocess.run(
        cmd,
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
    (log_dir / f"{name}.log").write_text(proc.stdout, encoding="utf-8")
    return proc.returncode == 0


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--benchmarks", nargs="*", default=list(BENCHMARKS))
    parser.add_argument(
        "--layout",
        choices=["default", "random"],
        default="default",
        help="Build normal Olden binaries or randomized-allocation sensitivity binaries.",
    )
    parser.add_argument(
        "--checked",
        action="store_true",
        help="Build validation-only binaries that emit compact correctness checks where available.",
    )
    args = parser.parse_args()

    out_name = "olden_aarch64_random_alloc" if args.layout == "random" else "olden_aarch64"
    if args.checked:
        out_name += "_checked"
    out_dir = ROOT / "research" / "bin" / out_name
    log_dir = LOG_DIR / f"{args.layout}{'_checked' if args.checked else ''}"
    random_alloc = args.layout == "random"
    failures = 0
    rows = [
        "# Olden AArch64 Build",
        "",
        "This builds a small public Olden pointer-intensive benchmark subset",
        "for ARM64 Ubuntu full-system gem5 runs. Bisort, health, and MST use",
        "the LLVM-test-suite-derived Olden copy under `external/olden`; treeadd",
        "uses the v1.01 source plus `research/olden_compat` to replace obsolete",
        "CM/parallel runtime calls with single-process stubs.",
        "",
        "| Benchmark | Status | Binary | Log |",
        "|---|---|---|---|",
    ]
    for name in args.benchmarks:
        ok = build_one(name, out_dir, log_dir, random_alloc, args.checked)
        failures += 0 if ok else 1
        rows.append(
            f"| {name} | {'PASS' if ok else 'FAIL'} | "
            f"`{out_dir / name}` | `{log_dir / (name + '.log')}` |"
        )
    rows.append("")
    rows.append(f"build_status={'PASS' if failures == 0 else 'FAIL'}")
    summary = log_dir / "OLDEN_AARCH64_BUILD.md"
    summary.write_text("\n".join(rows), encoding="utf-8")
    print(summary)
    print(f"build_status={'PASS' if failures == 0 else 'FAIL'}")
    if failures:
        raise SystemExit(1)


if __name__ == "__main__":
    main()

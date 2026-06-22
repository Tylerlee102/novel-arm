#!/usr/bin/env python3
"""Extract a minimal AArch64 Linux C++ sysroot from the gem5 Ubuntu image."""

from __future__ import annotations

import argparse
import posixpath
import shutil
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PKG_DIR = ROOT / "tools" / "py_extfs_pkgs"
if PKG_DIR.exists():
    sys.path.insert(0, str(PKG_DIR))

from dissect.extfs import ExtFS  # type: ignore  # noqa: E402
from dissect.util.stream import RangeStream  # type: ignore  # noqa: E402


FT_DIR = 0x4000
FT_FILE = 0x8000
FT_SYMLINK = 0xA000


DEFAULT_IMAGE = (
    ROOT / "tools" / "msys64" / "home" / "tyboy" / ".cache" / "gem5"
    / "arm-ubuntu-24.04-img-3.0.0"
)
DEFAULT_OUT = ROOT / "tools" / "arm64_ubuntu_24_sysroot"
ROOT_START_LBA = 1_103_872
ROOT_SECTORS = 8_314_880


class Extractor:
    def __init__(self, fs: ExtFS, out: Path) -> None:
        self.fs = fs
        self.out = out
        self.files = 0
        self.dirs = 0
        self.symlinks_copied = 0

    def extract_path(self, src: str, dst_rel: str | None = None) -> None:
        src = posixpath.normpath("/" + src.lstrip("/"))
        dst_rel = dst_rel if dst_rel is not None else src.lstrip("/")
        self._copy_node(src, self.out / Path(dst_rel), depth=0)

    def _copy_node(self, src: str, dst: Path, depth: int) -> None:
        if depth > 16:
            raise RuntimeError(f"too many symlinks while extracting {src}")
        node = self.fs.get(src)
        if node.filetype == FT_DIR:
            dst.mkdir(parents=True, exist_ok=True)
            self.dirs += 1
            for name in node.listdir().keys():
                if name in (".", ".."):
                    continue
                self._copy_node(posixpath.join(src, name), dst / name, depth)
        elif node.filetype == FT_FILE:
            dst.parent.mkdir(parents=True, exist_ok=True)
            with node.open() as fh, dst.open("wb") as out_fh:
                shutil.copyfileobj(fh, out_fh, length=1024 * 1024)
            self.files += 1
        elif node.filetype == FT_SYMLINK:
            target = node.open().read().decode("utf-8", errors="surrogateescape")
            resolved = (
                posixpath.normpath(target)
                if target.startswith("/")
                else posixpath.normpath(posixpath.join(posixpath.dirname(src), target))
            )
            self._copy_node(resolved, dst, depth + 1)
            self.symlinks_copied += 1
        else:
            # Device nodes, sockets, and FIFOs are irrelevant to a compiler sysroot.
            return


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--image", type=Path, default=DEFAULT_IMAGE)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()

    if args.force and args.out.exists():
        shutil.rmtree(args.out)
    args.out.mkdir(parents=True, exist_ok=True)

    offset = ROOT_START_LBA * 512
    size = ROOT_SECTORS * 512
    with args.image.open("rb") as fh:
        fs = ExtFS(RangeStream(fh, offset, size))
        extractor = Extractor(fs, args.out)
        for path in (
            "/usr/include",
            "/usr/lib/aarch64-linux-gnu",
            "/usr/lib/gcc/aarch64-linux-gnu/13",
            "/usr/lib/ld-linux-aarch64.so.1",
        ):
            extractor.extract_path(path)

    lib_dir = args.out / "lib"
    lib_dir.mkdir(exist_ok=True)
    usr_multiarch = args.out / "usr" / "lib" / "aarch64-linux-gnu"
    lib_multiarch = lib_dir / "aarch64-linux-gnu"
    if usr_multiarch.exists():
        shutil.copytree(usr_multiarch, lib_multiarch, dirs_exist_ok=True)

    loader_src = args.out / "usr" / "lib" / "ld-linux-aarch64.so.1"
    loader_dst = lib_dir / "ld-linux-aarch64.so.1"
    if loader_src.exists():
        shutil.copy2(loader_src, loader_dst)

    print(f"sysroot={args.out}")
    print(f"dirs={extractor.dirs}")
    print(f"files={extractor.files}")
    print(f"symlinks_copied={extractor.symlinks_copied}")


if __name__ == "__main__":
    main()

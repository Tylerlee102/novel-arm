"""Probe SCons compiler detection from the active Python environment."""

from __future__ import annotations

import os
import shutil

import SCons.Environment
import SCons.Tool


def main() -> None:
    env = SCons.Environment.Environment()
    env_with_path = SCons.Environment.Environment(ENV={"PATH": os.environ.get("PATH", "")})
    print("os.name", os.name)
    print("os.pathsep", os.pathsep)
    print("PATH", os.environ.get("PATH", ""))
    print("MINGW_PREFIX", os.environ.get("MINGW_PREFIX", ""))
    print("MSYSTEM_PREFIX", os.environ.get("MSYSTEM_PREFIX", ""))
    print("which gcc", shutil.which("gcc"))
    print("which gcc.exe", shutil.which("gcc.exe"))
    print("env Detect gcc", env.Detect(["gcc", "clang"]))
    print("env ENV PATH", env.get("ENV", {}).get("PATH", ""))
    print("env_with_path Detect gcc", env_with_path.Detect(["gcc", "clang"]))
    print("FindTool gcc/clang", SCons.Tool.FindTool(["gcc", "clang"], env))
    print("FindTool gcc/clang with path", SCons.Tool.FindTool(["gcc", "clang"], env_with_path))
    print("FindTool g++/clang++", SCons.Tool.FindTool(["g++", "clang++"], env))
    print("FindTool mingw/gcc", SCons.Tool.FindTool(["mingw", "gcc"], env))
    for tool in ("gcc", "g++", "mingw"):
        test_env = SCons.Environment.Environment(ENV={"PATH": os.environ.get("PATH", "")})
        try:
            test_env.Tool(tool)
            print("direct Tool", tool, "loaded", test_env.get("CC"), test_env.get("CXX"))
        except Exception as exc:
            print("direct Tool", tool, "failed", type(exc).__name__, exc)


if __name__ == "__main__":
    main()

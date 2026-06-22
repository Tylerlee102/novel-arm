# PCRE2 Regex Workload AArch64 Build

Source: deterministic native AArch64 workload that calls the public
PCRE2 8-bit regex compiler and matcher through the Ubuntu ARM64
guest library stack while scanning log-like records containing
address-shaped ticket words loaded as data.

Binary: `C:\Users\tyboy\OneDrive\Documents\novel-arm\research\bin\aarch64_pcre2_regex_workload`

Build command:

```text
C:\Users\tyboy\OneDrive\Documents\novel-arm\tools\msys64\ucrt64\bin\clang.exe --target=aarch64-linux-gnu --sysroot=C:\Users\tyboy\OneDrive\Documents\novel-arm\tools\arm64_ubuntu_24_sysroot -fuse-ld=lld -O2 -DNDEBUG C:\Users\tyboy\OneDrive\Documents\novel-arm\research\aarch64_pcre2_regex_workload.c C:\Users\tyboy\OneDrive\Documents\novel-arm\tools\arm64_ubuntu_24_sysroot\usr\lib\aarch64-linux-gnu\libpcre2-8.so.0.11.2 -o C:\Users\tyboy\OneDrive\Documents\novel-arm\research\bin\aarch64_pcre2_regex_workload
```

build_status=PASS

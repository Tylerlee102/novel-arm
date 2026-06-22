# zlib Workload AArch64 Build

Source: deterministic native AArch64 workload that calls public
zlib compression/decompression through the Ubuntu ARM64 guest
library stack over buffers containing address-shaped words as data.

Binary: `C:\Users\tyboy\OneDrive\Documents\novel-arm\research\bin\aarch64_zlib_workload`

Build command:

```text
C:\Users\tyboy\OneDrive\Documents\novel-arm\tools\msys64\ucrt64\bin\clang.exe --target=aarch64-linux-gnu --sysroot=C:\Users\tyboy\OneDrive\Documents\novel-arm\tools\arm64_ubuntu_24_sysroot -fuse-ld=lld -O2 -DNDEBUG C:\Users\tyboy\OneDrive\Documents\novel-arm\research\aarch64_zlib_workload.c C:\Users\tyboy\OneDrive\Documents\novel-arm\tools\arm64_ubuntu_24_sysroot\usr\lib\aarch64-linux-gnu\libz.so.1.3 -o C:\Users\tyboy\OneDrive\Documents\novel-arm\research\bin\aarch64_zlib_workload
```

build_status=PASS

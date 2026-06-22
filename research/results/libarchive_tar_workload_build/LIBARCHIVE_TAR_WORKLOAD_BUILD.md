# libarchive TAR Workload AArch64 Build

Source: deterministic native AArch64 workload that calls the public
libarchive TAR parser through the Ubuntu ARM64 guest library stack
over in-memory archive entries containing address-shaped words as data.

Binary: `C:\Users\tyboy\OneDrive\Documents\novel-arm\research\bin\aarch64_libarchive_tar_workload`

Build command:

```text
C:\Users\tyboy\OneDrive\Documents\novel-arm\tools\msys64\ucrt64\bin\clang.exe --target=aarch64-linux-gnu --sysroot=C:\Users\tyboy\OneDrive\Documents\novel-arm\tools\arm64_ubuntu_24_sysroot -fuse-ld=lld -O2 -DNDEBUG C:\Users\tyboy\OneDrive\Documents\novel-arm\research\aarch64_libarchive_tar_workload.c C:\Users\tyboy\OneDrive\Documents\novel-arm\tools\arm64_ubuntu_24_sysroot\usr\lib\aarch64-linux-gnu\libarchive.so.13.7.2 C:\Users\tyboy\OneDrive\Documents\novel-arm\tools\arm64_ubuntu_24_sysroot\usr\lib\aarch64-linux-gnu\libz.so.1.3 C:\Users\tyboy\OneDrive\Documents\novel-arm\tools\arm64_ubuntu_24_sysroot\usr\lib\aarch64-linux-gnu\libbz2.so.1.0.4 C:\Users\tyboy\OneDrive\Documents\novel-arm\tools\arm64_ubuntu_24_sysroot\usr\lib\aarch64-linux-gnu\liblzma.so.5.4.5 C:\Users\tyboy\OneDrive\Documents\novel-arm\tools\arm64_ubuntu_24_sysroot\usr\lib\aarch64-linux-gnu\liblz4.so.1.9.4 C:\Users\tyboy\OneDrive\Documents\novel-arm\tools\arm64_ubuntu_24_sysroot\usr\lib\aarch64-linux-gnu\libzstd.so.1.5.5 C:\Users\tyboy\OneDrive\Documents\novel-arm\tools\arm64_ubuntu_24_sysroot\usr\lib\aarch64-linux-gnu\libxml2.so.2.9.14 C:\Users\tyboy\OneDrive\Documents\novel-arm\tools\arm64_ubuntu_24_sysroot\usr\lib\aarch64-linux-gnu\libcrypto.so.3 C:\Users\tyboy\OneDrive\Documents\novel-arm\tools\arm64_ubuntu_24_sysroot\usr\lib\aarch64-linux-gnu\libacl.so.1.1.2302 C:\Users\tyboy\OneDrive\Documents\novel-arm\tools\arm64_ubuntu_24_sysroot\usr\lib\aarch64-linux-gnu\libattr.so.1.1.2502 -o C:\Users\tyboy\OneDrive\Documents\novel-arm\research\bin\aarch64_libarchive_tar_workload
```

build_status=PASS

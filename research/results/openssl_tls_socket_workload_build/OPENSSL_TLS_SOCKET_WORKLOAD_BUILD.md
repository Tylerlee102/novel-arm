# OpenSSL TLS Socket Workload AArch64 Build

Source: deterministic native AArch64 service-style workload that calls
OpenSSL libssl's TLS 1.2 PSK handshake and record path over a
nonblocking Linux AF_UNIX socketpair while maintaining session hash/LRU metadata and
pointer-shaped ticket words loaded as data.

Binary: `C:\Users\tyboy\OneDrive\Documents\novel-arm\research\bin\aarch64_openssl_tls_socket_workload`

Build command:

```text
C:\Users\tyboy\OneDrive\Documents\novel-arm\tools\msys64\ucrt64\bin\clang.exe --target=aarch64-linux-gnu --sysroot=C:\Users\tyboy\OneDrive\Documents\novel-arm\tools\arm64_ubuntu_24_sysroot -fuse-ld=lld -O2 -DNDEBUG -I C:\Users\tyboy\OneDrive\Documents\novel-arm\external\gem5\include C:\Users\tyboy\OneDrive\Documents\novel-arm\research\aarch64_openssl_tls_socket_workload.c C:\Users\tyboy\OneDrive\Documents\novel-arm\external\gem5\util\m5\src\abi\arm64\m5op.S C:\Users\tyboy\OneDrive\Documents\novel-arm\tools\arm64_ubuntu_24_sysroot\usr\lib\aarch64-linux-gnu\libssl.so.3 C:\Users\tyboy\OneDrive\Documents\novel-arm\tools\arm64_ubuntu_24_sysroot\usr\lib\aarch64-linux-gnu\libcrypto.so.3 -o C:\Users\tyboy\OneDrive\Documents\novel-arm\research\bin\aarch64_openssl_tls_socket_workload
```

build_status=PASS

# MiBench Patricia Workload AArch64 Build

Source: deterministic native AArch64 workload using the public
MiBench network/patricia Patricia trie implementation and the
MiBench `small.udp` packet-field input. The driver adds checksum
and return-code reporting for gem5 full-system evaluation.

Public source archive: `external/mibench_download/network.tar.gz`.
MiBench source directory: `C:\Users\tyboy\OneDrive\Documents\novel-arm\external\mibench_network\network\patricia`.
Binary: `C:\Users\tyboy\OneDrive\Documents\novel-arm\research\bin\aarch64_mibench_patricia_workload`

Build command:

```text
C:\Users\tyboy\OneDrive\Documents\novel-arm\tools\msys64\ucrt64\bin\clang.exe --target=aarch64-linux-gnu --sysroot=C:\Users\tyboy\OneDrive\Documents\novel-arm\tools\arm64_ubuntu_24_sysroot -fuse-ld=lld -O2 -DNDEBUG -I C:\Users\tyboy\OneDrive\Documents\novel-arm\external\mibench_network\network\patricia C:\Users\tyboy\OneDrive\Documents\novel-arm\research\aarch64_mibench_patricia_workload.c C:\Users\tyboy\OneDrive\Documents\novel-arm\external\mibench_network\network\patricia\patricia.c -o C:\Users\tyboy\OneDrive\Documents\novel-arm\research\bin\aarch64_mibench_patricia_workload
```

build_status=PASS

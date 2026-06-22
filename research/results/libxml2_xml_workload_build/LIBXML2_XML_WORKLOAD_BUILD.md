# libxml2 XML Workload AArch64 Build

Source: deterministic native AArch64 workload that calls the public
libxml2 XML parser and serializer through the Ubuntu ARM64 guest
library stack over XML records containing address-shaped words as data.

Binary: `C:\Users\tyboy\OneDrive\Documents\novel-arm\research\bin\aarch64_libxml2_xml_workload`

Build command:

```text
C:\Users\tyboy\OneDrive\Documents\novel-arm\tools\msys64\ucrt64\bin\clang.exe --target=aarch64-linux-gnu --sysroot=C:\Users\tyboy\OneDrive\Documents\novel-arm\tools\arm64_ubuntu_24_sysroot -fuse-ld=lld -O2 -DNDEBUG -IC:\Users\tyboy\OneDrive\Documents\novel-arm\tools\msys64\ucrt64\include\libxml2 C:\Users\tyboy\OneDrive\Documents\novel-arm\research\aarch64_libxml2_xml_workload.c C:\Users\tyboy\OneDrive\Documents\novel-arm\tools\arm64_ubuntu_24_sysroot\usr\lib\aarch64-linux-gnu\libxml2.so.2.9.14 C:\Users\tyboy\OneDrive\Documents\novel-arm\tools\arm64_ubuntu_24_sysroot\usr\lib\aarch64-linux-gnu\libz.so.1.3 C:\Users\tyboy\OneDrive\Documents\novel-arm\tools\arm64_ubuntu_24_sysroot\usr\lib\aarch64-linux-gnu\liblzma.so.5.4.5 C:\Users\tyboy\OneDrive\Documents\novel-arm\tools\arm64_ubuntu_24_sysroot\usr\lib\aarch64-linux-gnu\libm.so.6 -o C:\Users\tyboy\OneDrive\Documents\novel-arm\research\bin\aarch64_libxml2_xml_workload
```

build_status=PASS

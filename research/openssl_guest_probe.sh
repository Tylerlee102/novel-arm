echo COPPER_OPENSSL_GUEST_PROBE_START
command -v openssl || true
openssl version || true
echo COPPER_OPENSSL_GUEST_PROBE_TINY_BINARY
/tmp/aarch64_native_workload || true
echo COPPER_OPENSSL_GUEST_PROBE_DONE

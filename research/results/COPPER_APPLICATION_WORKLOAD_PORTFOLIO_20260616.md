# COPPER Application and Service-Style Workload Portfolio

Date: 2026-06-17

This file aggregates the new application/service-style AArch64/Linux
full-system runs. It intentionally does not rewrite the paper; it records
whether the new evidence closes the external-workload gap.

| Workload | Policies present | Checksums agree | COPPER delta | Naive delta | Best conventional | Multi hybrid delta | Slack hybrid delta | Slack blocked | Slack CTLW | Naive CTLW | COPPER CTLW | CTLW reduction | COPPER faults |
|---|---|---:|---:|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|
| SQLite small | none, stride, bop, naive, copper_clpd64k_peb, dcpt, spp, spp_copper, spp_copper_slack, ampm | yes | -0.025% | 0.003% | spp -5.996% | -5.998% | -5.998% | 50,624 | 1,749 | 13,674 | 842 | 93.8% | 0 |
| SQLite medium | none, stride, naive, copper_clpd64k_peb, dcpt, spp, ampm, spp_copper_slack | yes | -0.000% | -0.010% | spp -3.623% |  | -3.617% | 72,512 | 1,778 | 16,326 | 1,211 | 92.6% | 0 |
| SQLite stress | none, stride, naive, copper_clpd64k_peb, dcpt, spp, ampm, spp_copper_slack | yes | -0.037% | -0.007% | spp -2.587% |  | -2.549% | 175,838 | 4,224 | 43,226 | 2,543 | 94.1% | 0 |
| SQLite no-poison | none, naive, copper_clpd64k_peb | yes | 0.058% | 0.045% |  |  |  |  |  | 12,400 | 703 | 94.3% | 0 |
| Lua small | none, stride, bop, naive, copper_clpd64k_peb, dcpt, spp, spp_copper, spp_copper_slack, ampm | yes | -1.230% | -1.001% | spp -18.350% | -18.467% | -18.460% | 112,130 | 766 | 11,084 | 2,310 | 79.2% | 0 |
| Lua medium | none, stride, naive, copper_clpd64k_peb, dcpt, spp, ampm, spp_copper_slack | yes | -2.153% | -1.929% | spp -29.532% |  | -29.240% | 247,148 | 966 | 31,209 | 2,706 | 91.3% | 0 |
| Lua stress | none, stride, naive, copper_clpd64k_peb, dcpt, spp, ampm, spp_copper_slack | yes | -2.800% | -2.426% | spp -31.392% |  | -31.120% | 655,685 | 871 | 23,338 | 5,393 | 76.9% | 0 |
| Lua no-poison | none, naive, copper_clpd64k_peb | yes | -1.272% | -1.000% |  |  |  |  |  | 11,259 | 2,346 | 79.2% | 0 |
| Duktape small | none, naive, copper_clpd64k_peb, spp, spp_copper_slack | yes | -0.097% | -0.109% | spp -4.780% |  | -4.749% | 105,503 | 569 | 9,564 | 896 | 90.6% | 0 |
| Duktape medium | none, stride, naive, copper_clpd64k_peb, dcpt, spp, ampm, spp_copper_slack | yes | -0.135% | -0.157% | spp -6.732% |  | -6.950% | 163,077 | 1,140 | 13,457 | 1,241 | 90.8% | 0 |
| Duktape stress | none, stride, naive, copper_clpd64k_peb, dcpt, spp, ampm, spp_copper_slack | yes | -0.189% | -0.251% | spp -8.385% |  | -8.745% | 301,435 | 1,559 | 15,547 | 1,475 | 90.5% | 0 |
| yyjson medium | none, stride, naive, copper_clpd64k_peb, dcpt, spp, ampm, spp_copper_slack | yes | -0.069% | -0.100% | spp -18.351% |  | -18.342% | 19,465 | 59 | 3,855 | 43 | 98.9% | 0 |
| yyjson stress | none, stride, naive, copper_clpd64k_peb, dcpt, spp, ampm, spp_copper_slack | yes | -0.052% | -0.028% | spp -22.097% |  | -22.186% | 41,408 | 112 | 4,323 | 47 | 98.9% | 0 |
| libxml2 XML tiny | none, naive, copper_clpd64k_peb, spp, spp_copper_slack | yes | 0.041% | 0.055% | spp -13.869% |  | -13.834% | 27,378 | 136 | 12,758 | 139 | 98.9% | 0 |
| libarchive TAR tiny | none, naive, copper_clpd64k_peb, spp, spp_copper_slack | yes | -0.136% | -0.183% | spp -15.906% |  | -15.911% | 41,755 | 233 | 17,091 | 341 | 98.0% | 0 |
| JSON+SQLite medium | none, stride, naive, copper_clpd64k_peb, dcpt, spp, ampm, spp_copper_slack | yes | -0.037% | -0.017% | spp -4.497% |  | -4.523% | 78,860 | 582 | 14,104 | 699 | 95.0% | 0 |
| JSON+SQLite stress | none, stride, naive, copper_clpd64k_peb, dcpt, spp, ampm, spp_copper_slack | yes | -0.080% | -0.102% | spp -3.588% |  | -3.623% | 222,066 | 1,144 | 33,203 | 2,861 | 91.4% | 0 |
| Cache-service small | none, stride, naive, copper_clpd64k_peb, dcpt, spp, ampm, spp_copper_slack | yes | -0.087% | -0.339% | spp -13.440% |  | -13.406% | 7,216 | 19 | 3,637 | 19 | 99.5% | 0 |
| Cache-service medium | none, stride, naive, copper_clpd64k_peb, dcpt, spp, ampm, spp_copper_slack | yes | -0.271% | -0.378% | spp -13.115% |  | -13.086% | 9,967 | 26 | 4,119 | 24 | 99.4% | 0 |
| TLS session-service small | none, stride, naive, copper_clpd64k_peb, dcpt, spp, ampm, spp_copper_slack | yes | -0.074% | -0.117% | spp -13.686% |  | -13.712% | 7,303 | 19 | 3,680 | 18 | 99.5% | 0 |
| OpenSSL libssl TLS memory-BIO small | none, stride, naive, copper_clpd64k_peb, dcpt, spp, ampm, spp_copper_slack | yes | -0.470% | -0.515% | spp -2.614% |  | -2.604% | 9,997 | 54 | 2,411 | 29 | 98.8% | 0 |
| OpenSSL SHA service small | none, stride, naive, copper_clpd64k_peb, dcpt, spp, ampm, spp_copper_slack | yes | -1.916% | -1.876% | spp -16.598% |  | -16.660% | 29,477 | 259 | 10,590 | 301 | 97.2% | 0 |
| OpenSSL EVP/HMAC service small | none, stride, naive, copper_clpd64k_peb, dcpt, spp, ampm, spp_copper_slack | yes | 0.731% | 0.821% | spp -14.501% |  | -14.552% | 87,827 | 828 | 16,685 | 954 | 94.3% | 0 |

Interpretation:

- The application evidence is materially stronger than the earlier generated-only story: SQLite, upstream SQLite speedtest1 JSON/star/ORM, Lua, Duktape, yyjson, two-seed PCRE2 regex matching, public libxml2 XML parser/serializer execution, public libarchive TAR parser execution, Zstd and zlib compression/decompression, composed JSON+SQLite service-style workloads, cache-service hash/LRU workloads, a crypto-adjacent TLS/session-service stress point, real OpenSSL libssl TLS memory-BIO execution, socket-backed OpenSSL libssl TLS execution, strict private-netns TCP-loopback OpenSSL libssl TLS execution, two-seed process-separated private-netns TCP-loopback OpenSSL libssl TLS execution, and real OpenSSL libcrypto SHA256 plus EVP/HMAC drivers run as native AArch64 Linux binaries under gem5 full-system, now with medium/stress scale points for both the single-engine families and the service-composition workload plus small/medium cache-service scale points.
- Across the application points, COPPER preserves checksum correctness and records zero translation faults while reducing naive DMP CTLW misses by roughly 77-99%.
- The 2026-06-17 conventional matrix still covers eight single-engine medium/stress app points plus two bounded JSON+SQLite service-composition points and two bounded cache-service hash/LRU scale points and should be treated as the source of aggregate timing, traffic, and CTLW claims.
- The TLS/session-service point is intentionally reported as a separate crypto-adjacent service-style stress point, not as a production TLS stack. It adds session hash/LRU metadata, linked record chains, and pointer-shaped ticket/mask words loaded by an authentication loop but never used as architectural addresses.
- The PCRE2 seed-stability artifact covers two deterministic seeds for the public 8-bit regex compiler and matcher. Across both seeds, COPPER keeps at least 99.3% CTLW reduction, SPP+COPPER slack keeps at least 98.9% CTLW reduction, and COPPER/slack translation faults remain zero.
- The libxml2 XML point calls the public XML parser and serializer in the ARM64 guest over deterministic in-memory XML records containing address-shaped words as data. On the tiny full-system point, COPPER and SPP+COPPER slack both cut naive-DMP CTLW misses by 98.9%, faults remain zero, and the slack hybrid stays within 0.035 percentage points of SPP.
- The libarchive TAR point calls the public archive parser in the ARM64 guest over deterministic in-memory TAR entries containing address-shaped words as data. On the tiny full-system point, COPPER cuts naive-DMP CTLW misses by 98.0%, SPP+COPPER slack cuts them by 98.6%, faults remain zero, and the slack hybrid is within -0.004 percentage points of SPP.
- The OpenSSL libssl TLS memory-BIO point executes the public TLS 1.2 PSK handshake and TLS record read/write path through libssl over paired memory BIOs with a deterministic benchmark RNG. It is a real TLS-library path, but still an in-process single-handshake harness rather than a production networked TLS server.
- The OpenSSL SHA point is real guest libcrypto execution through the dynamic loader, but it is still a small synthetic driver around SHA256 rather than a full TLS stack or production crypto benchmark.
- The OpenSSL EVP/HMAC point broadens real-libcrypto coverage to AES-CTR, HMAC-SHA256, SHA256, and CRYPTO_memcmp, but it is still a small service-style driver rather than a full TLS stack or production crypto benchmark.
- The conventional matrix shows SPP is the strongest address-stream baseline on the app set; SPP+COPPER slack remains a near-SPP coexistence policy rather than a standalone speedup claim.
- The result still does not justify a universal performance claim. Conventional prefetchers, especially SPP/DCPT/AMPM/BOP depending on workload, remain much faster on raw timing.
- Hybrid SPP+COPPER is the strongest new direction: on the medium/stress application points, it retains SPP-class timing while preserving COPPER child-filter activity and zero translation faults.
- The new slack-only companion arbiter gives this direction a cleaner mechanism: SPP has strict issue priority, and COPPER can issue only when the primary lane has no ready packet.
- Best current paper positioning: COPPER is a safe authority layer for content-derived DMP candidates, and it should coexist with conventional address-correlation prefetchers rather than replacing them.
- Remaining top-tier gap: broader production-like workloads and a deeper evaluation of the slack-only hybrid across more scales and security-adversarial inputs.

portfolio_status=PASS

# COPPER Final Research Output

Date: 2026-06-12, updated 2026-06-20

## Winning Idea Name

**COPPER-PEB/CLPD/CTLW/PASB/RCP: Committed Pointer-Provenance Prefetching with Provenance Epoch Boundaries**

Short form: **COPPER**

## Recommended Paper Title

**COPPER: Committed Pointer-Provenance Prefetching for Safe Data-Memory-Dependent Prefetchers**

## Abstract

Data-memory-dependent prefetchers (DMPs) improve irregular pointer-heavy workloads by using memory contents as future addresses, but Augury and GoFetch show that this can violate constant-time assumptions: data that merely resembles a pointer may trigger secret-dependent cache activity even when software never architecturally uses that data as an address. COPPER changes the DMP authority model. A DMP may dereference a memory-derived value only when the exact source word has committed pointer provenance, remains clean since proof, matches the protection/address-space context, and has a committed target translation witness when recursive cross-page prefetching is needed. The refined mechanism adds Recursive Carried-Provenance (RCP), a Committed Page-Translation Queue (CPTQ), a Commit-Epoch Provenance Filter (CEPF), Provenance Address-Space Binding (PASB), Committed Target-Line Witnessing (CTLW), and a Compressed Line-Provenance Directory (CLPD). Trace simulation blocks all modeled unsafe DMP dereferences while retaining pointer-chain speedup. A graph-style provenance trace shows COPPER-epoch gives 3.276x speedup while blocking data-at-rest and stale rewritten-edge prefetches. A GAPBS-backed topology trace over five generated Kronecker graphs shows COPPER-epoch at 1.770x and CLPD at 1.896x with zero data-at-rest, unproven-edge, or stale-slot prefetches; CLPD recovers 2.115x on a g12 edge scan with 8,192 line entries where the edge-exact ledger needs 131,072 entries for 2.369x. An expanded GAPBS-style kernel sensitivity sweep over 4,320 graph/kernel/table/cache/lookahead runs keeps COPPER unsafe modeled prefetches at zero, while naive DMP produces 81,605,320 unsafe modeled prefetches and source-only provenance still produces 284,488. Vivado simulation includes directed tests, a 2,000-trial randomized invariant monitor, CEPF backend bridge test, full-authority CEPF/PASB/CTLW test, and CLPD directory test; CLPD passes 14 directed plus 5,000 randomized scoreboard trials, and a fresh authority-chain regression passes 10 XSIM scripts with 0 failures. Synthesis of the core gate meets a 10 ns Artix-7 constraint, and the CEPF bridge uses 5 LUTs. ARM/AArch64 gem5 syscall-emulation runs show recursive COPPER improves ARM32 page-permuted pointer chains by 6.76-6.78% and random chains by 5.59-5.66%; direct AArch64 ELF runs show 6.77% and 5.61%. AArch64 Minor and O3 sensitivity remains positive at 2.64-2.79% and 2.68-2.77%, respectively. The ARM64 full-system path boots Ubuntu/Linux 6.8.12, switches from atomic boot to timing CPU for native static AArch64 ROIs, and attaches the selected prefetcher in the L1D cache hierarchy. CTLW-terminal removes PASB-only recursive translation faults and gives small positive timing movement on larger generated full-system pointer ROIs: -0.531% ticks on page-permuted pointers and -0.271% on random pointers while blocking about 15k unproven pointer-shaped candidates per COPPER run. A full-system AArch64 graph-gather control gives COPPER-CTLW -0.367% ticks versus no prefetch, blocks 8,660 unproven candidates, and records zero translation faults; stride still wins that binary because its edge array is sequential. An LLVM/clang-authored freestanding C AArch64 suite runs graph gather, hash probing, tree lookup, and fake pointer-shaped data under full-system Linux; COPPER blocks 679 unproven candidates and records zero translation faults, but is 0.093% slower than no prefetch on that smaller suite. A GAPBS-inspired BFS/SSSP/PageRank/CC mini-suite blocks 952 unproven candidates, eliminates the 408 CTLW misses and 408 unavailable recursive translations seen by naive DMP+CTLW, records 7,729 terminal stops, and matches no-prefetch ROI ticks; a larger 1024-node timing-mode rerun blocks 1,340 unproven candidates, removes naive's 6 CTLW misses and 6 unavailable translations, records 50,737 terminal stops, and gives a small -0.208% tick movement versus no prefetch. Stride remains faster on these mini-suites because their edge arrays are sequential. A bounded invariant checker passes the full PASB/CTLW/terminal rule and finds short counterexamples for no-PASB, no-CTLW, and no-terminal variants. To the best of public knowledge, COPPER is the first public DMP defense to use committed pointer provenance plus address-space and target-line translation witnesses as authority for recursive data-driven prefetch.

CS-SARI extends COPPER's SoC boundary story. It converts DMA/coherence/remap/TLBI revocation events into candidate-specific DMP authority hazards rather than a global prefetch stop. The wired RTL authority harness passes 12 directed plus 10,000 randomized XSIM samples with `conflict_hold=1245`, `avoided_global_hold=1007`, and `errors=0`; a GAPBS-topology revocation proxy reports 82.06% aggregate hold reduction versus global SARI, 269,879 authorized candidates recovered, zero CS-SARI modeled unsafe issues, and 59,013 no-hold unsafe issues. A bounded composition checker explores 7,555 reachable composed CLPD/CTLW/CS-SARI states and finds stale-authority counterexamples in weakened variants. A 20-configuration queue-depth/conflict sensitivity sweep keeps CS-SARI unsafe issues at zero while a no-hold control produces 1,649,883 unsafe modeled issues, with 72.06% median scoped-hold reduction.

The 2026-06-15 refresh adds the strongest local full-system evidence so far. A ROI-bracketed AArch64/Linux heap-pointer workload with 32,768 heap nodes, fake pointer-shaped data, rewrites, and checksum validation shows CLPD-64K improves three heap-layout seeds with mean -2.866% ROI ticks versus no prefetch while naive DMP slows them by mean +15.214%. Adding PEB closes the fake-only warm-state leakage: CLPD-64K+PEB blocks 131,066 of 131,066 fake pointer-shaped observations, issues zero prefetches, drops 76,560 pre-boundary authority entries, and is only +0.033% versus no prefetch. The same PEB mode still improves the three heap seeds by mean -2.905% with zero CTLW misses, zero translation faults, and matching checksums. On official AArch64 GAPBS BFS/CC/PR/SSSP/BC/TC at g10, CLPD-64K+PEB runs all six kernels with `rc=0`, +0.015% aggregate timing versus no prefetch, zero translation faults, zero proof evictions, and 340,128 pre-boundary authority entries dropped. Scalable CLPD SRAM RTL now passes directed/randomized XSIM, the 64K-entry configuration synthesizes on `xc7a200tfbg676-2` with 629 LUTs, 156 FFs, 260 BRAM tiles, and WNS 3.274 ns at 10 ns, then routes out-of-context with WNS 0.362 ns. PEB itself synthesizes on Artix-7 with 346 LUTs, 147 FFs, no BRAM/DSP, and WNS 3.782 ns.

A later public-workload refresh adds Olden AArch64 full-system evidence and stronger built-in prefetcher baselines. On randomized-allocation Olden, stride slows by +10.107% on the small suite and +11.565% on the medium Treeadd/Bisort/Health subset. Naive DMP is near neutral on the small suite (+0.039%) and improves the medium subset by -2.829%, but produces 188,223 and 123,516 CTLW misses. COPPER CLPD-64K+PEB improves by -0.398% on small Olden and -2.616% on medium Olden while reducing those CTLW misses to 29,039 and 47,145, blocking 320,013 and 185,023 unproven candidates, and preserving zero translation faults. A validation-only Bisort build emits identical baseline/COPPER count, checksum, and histogram fingerprints for initial, forward-sort, and backward-sort phases. Built-in gem5 prefetchers are faster on Olden: DCPT reaches -5.742% small / -7.025% medium, SPP reaches -2.963% small / -5.870% medium, and AMPM reaches -2.465% small / -3.909% medium. These are conventional address-correlation baselines, not safe content-derived DMP baselines, so they sharpen the claim: COPPER is an authority mechanism for safe data-derived pointer prefetching, not a universal replacement for the best address-stream prefetcher.

The 2026-06-17/18 public-application baseline matrix adds stride, DCPT, SPP, and AMPM to SQLite, Lua, Duktape, yyjson medium/stress AArch64 full-system runs, bounded JSON+SQLite medium/stress service-composition runs, and small/medium cache-service hash/LRU runs. Across those 12 points, SPP is the best conventional baseline every time, averaging -13.112% ticks versus no prefetching. SPP+COPPER slack averages -13.116%, with an average signed gap of -0.004 percentage points from SPP and 0.360 points worst-case, while preserving zero translation faults and 94.0% aggregate CTLW reduction versus naive DMP. Standalone COPPER averages -0.492% ticks, +0.754% memory-bus bytes, and 91.1% CTLW reduction versus naive DMP. The gem5-counter pressure scorecard now covers the expanded 22-point app/service/parser/compression/TCP side-effect set and gives standalone COPPER 0.879% mean pressure versus 1.083% for naive DMP, an 18.8% lower proxy pollution score. This is an important honesty improvement: the paper can now show fair conventional baselines and still defend SCOOP as a coexistence mechanism rather than claiming COPPER replaces address-stream prefetchers.

The JSON+SQLite service-composition point now has second seeds at both medium and stress scale. Across the two medium seeds, COPPER CLPD-64K+PEB keeps CTLW reduction at least 95.0%, SPP+COPPER slack keeps CTLW reduction at least 95.9%, and the worst SPP+COPPER slack timing gap versus SPP is 0.026 percentage points. Across the two stress seeds, COPPER keeps CTLW reduction at least 91.4%, SPP+COPPER slack keeps CTLW reduction at least 96.6%, and the worst slack timing gap versus SPP is 0.069 percentage points. Both COPPER paths record zero translation faults and all key-policy runs pass checksum/return-code validation. This strengthens the composed parser/database evidence, while still falling short of a production database-server campaign.

Standalone SQLite now has its own medium/stress seed-stability artifact. Across three medium and two stress public SQLite-amalgamation full-system seed points, COPPER CLPD-64K+PEB keeps CTLW reduction at least 90.3%, SPP+COPPER slack keeps CTLW reduction at least 86.4%, both COPPER paths record zero translation faults, all key-policy runs preserve checksum/return-code validation, and the worst slack timing gap versus SPP is 0.056 percentage points. This separates the database-style claim from the composed JSON+SQLite claim.

An upstream SQLite speedtest1 addendum then builds unmodified `test/speedtest1.c` from SQLite 3.53.2 as a native AArch64 Linux binary and runs three tractable full-system components: JSON, star-schema, and ORM-style wide rows, all with `--memdb --verify --stats --size 1 --repeat 1`. All five key policies complete with `rc=0`; JSON/star report a matching zero-byte verification hash, so those hashes are treated as run-consistency markers rather than result-content checksums, while ORM reports 408,505 verification bytes. On JSON, naive DMP records 12,802 CTLW misses and COPPER CLPD-64K+PEB records 983, a 92.3% reduction. On star, naive records 6,844 and COPPER records 340, a 95.0% reduction. On ORM, naive records 38,552 and COPPER records 1,197, a 96.9% reduction. Across the three components, COPPER's minimum CTLW reduction is 92.3%, SPP+COPPER slack's minimum reduction versus naive is 88.5%, slack has no slowdown versus SPP on these components, and all key-policy translation-fault counts are zero. This is public upstream benchmark-component evidence, not a full production database benchmark.

Lua and Duktape now have a separate language-engine seed-stability artifact. Across three medium and two stress seeds per engine, COPPER CLPD-64K+PEB keeps CTLW reduction at least 76.7% over Lua and 90.5% over Duktape, while SPP+COPPER slack keeps CTLW reduction at least 96.3% over Lua and 85.0% over Duktape. Both COPPER paths record zero translation faults, all key-policy runs preserve checksum/return-code validation, and the worst slack timing gap versus SPP is 0.760 percentage points. The Lua stress result is an honesty caveat for standalone COPPER, while SCOOP-style coexistence remains strong.

yyjson now has matching parser-engine seed stability. Across two medium and two stress public yyjson full-system seed points, COPPER CLPD-64K+PEB keeps CTLW reduction at least 98.9%, SPP+COPPER slack keeps CTLW reduction at least 97.4%, both COPPER paths record zero translation faults, all key-policy runs preserve checksum/return-code validation, and the worst slack timing gap versus SPP is 0.089 percentage points.

A PCRE2 addendum then adds public regex parser/matcher library evidence through the Ubuntu ARM64 guest dynamic loader. The native AArch64 driver compiles seven PCRE2 8-bit regular expressions and repeatedly matches them over generated log-like records containing address-shaped ticket words loaded as data. The original seed preserves checksum `0x70905e0adac9ac17` across all key policies, cuts naive-DMP CTLW misses from 9,406 to 62 under COPPER, and cuts them to 79 under SPP+COPPER slack. A second deterministic seed preserves a distinct checksum `0xfc469fc668f4c38c`, cuts naive-DMP CTLW misses from 9,394 to 59 under COPPER, and cuts them to 107 under SPP+COPPER slack. Across both seeds, minimum COPPER CTLW reduction is 99.3%, minimum SPP+COPPER slack CTLW reduction is 98.9%, all key-policy return codes agree, and COPPER/slack translation faults remain zero. This broadens the public parser/matcher evidence, but it is still a benchmark driver rather than production log-processing software.

A libxml2 addendum adds a second public XML/parser-family point through the same ARM64 full-system path. The native AArch64 driver calls the public libxml2 XML parser and serializer over deterministic in-memory XML records containing address-shaped words as data. On the five-policy tiny full-system point, all runs preserve checksum `0x45392e595faf2f7d` and `rc=0`. Naive DMP records 12,758 CTLW misses; COPPER CLPD-64K+PEB records 139, a 98.9% reduction; SPP+COPPER slack records 136, also a 98.9% reduction; and both COPPER paths record zero translation faults. SPP gives -13.869% ticks versus no prefetch, while SPP+COPPER slack is within 0.035 percentage points at -13.834%. This strengthens public parser-library breadth, but it remains a bounded in-memory XML harness rather than a production XML service.

A libarchive addendum broadens the public parser-library evidence beyond text formats. The native AArch64 driver calls the public libarchive TAR parser over deterministic in-memory archive entries containing address-shaped words as data. On the five-policy tiny full-system point, all runs preserve checksum `0x950941dc0c18ee4d` and `rc=0`. Naive DMP records 17,091 CTLW misses; COPPER CLPD-64K+PEB records 341, a 98.0% reduction; SPP+COPPER slack records 233, a 98.6% reduction; and both COPPER paths record zero translation faults. SPP gives -15.906% ticks versus no prefetch, while SPP+COPPER slack is essentially tied at -15.911%. This strengthens archive/parser-library breadth, but it remains a bounded in-memory TAR harness rather than a production archive extraction service.

A MiBench Patricia addendum adds a public pointer-rich trie benchmark-family point through the same native AArch64 full-system path. The driver uses the public MiBench network/patricia Patricia trie implementation plus public `small.udp` and `large.udp` packet-field inputs; the COPPER-specific layer only converts packet fields into deterministic routing keys and emits checksum/return-code fields. On the strongest completed five-policy point with 12,288 public `large.udp` input records and 24,576 lookups, all policies preserve checksum `0x60874357358c1fc4` and `rc=0`. Naive DMP records 18,454 CTLW misses; COPPER CLPD-64K+PEB records 381, a 97.9% reduction; SPP+COPPER slack records 635, a 96.6% reduction; and key-policy translation faults remain zero. SPP gives -14.272% ticks versus no prefetch, while SPP+COPPER slack is -14.237%, a +0.035 percentage-point gap versus SPP. A second 12K seed produces a distinct checksum `0xe4dc12fd1dcd52b0`; across both 12K seeds COPPER keeps at least 97.8% CTLW reduction, SPP+COPPER slack keeps at least 96.6%, the worst slack gap versus SPP is 0.035 percentage points, and COPPER/slack translation faults remain zero. Across 128-, 2,048-, 8,192-, and 12,288-record Patricia scale points, COPPER keeps at least 97.9% CTLW reduction, SPP+COPPER slack keeps at least 96.6%, all COPPER/slack translation faults remain zero, and the worst absolute slack gap versus SPP is 0.050 percentage points. Additional public `large.udp` scale attempts validate larger no-prefetch baseline prefixes at 16,384, 32,768, and 62,721 records, but larger naive/COPPER policy comparisons did not complete within the local interactive gem5 budget; these are reported as negative scale-feasibility evidence, not benchmark wins. This is stronger public benchmark-family evidence than a generated pointer loop, but it is still a MiBench Patricia point rather than SPEC or production network routing software.

A Zstd addendum adds a public compression-library point through the same Ubuntu ARM64 guest dynamic-loader path. The native AArch64 driver calls libzstd compression and decompression over deterministic buffers containing address-shaped words as data, then verifies round-trip output and emits a stable checksum. Across `none`, `naive`, `copper_clpd64k_peb`, `spp`, and `spp_copper_slack`, all runs preserve checksum `0x93d05761620949ad` and `rc=0`. Naive DMP records 9,239 CTLW misses; COPPER records 49, a 99.5% reduction; SPP+COPPER slack records 51, a 99.4% reduction; and all key-policy translation-fault counters remain zero. SPP gives -15.931% ticks versus no prefetch, while SPP+COPPER slack is close at -15.748%. This is a useful public compression-library point, not a production storage or network compression service.

A zlib addendum repeats the compression-library pattern through a second public ABI. The native AArch64 driver calls zlib `compress2`, `uncompress`, and `crc32` over deterministic buffers containing address-shaped words as data. Across the same five key policies, all runs preserve checksum `0xf5b59076d62b0a4a` and `rc=0`. Naive DMP records 11,336 CTLW misses; COPPER records 65, a 99.4% reduction; SPP+COPPER slack records 58, a 99.5% reduction; and all key-policy translation-fault counters remain zero. SPP gives -13.773% ticks versus no prefetch, while SPP+COPPER slack gives -13.809%. This independently supports the compression-library story, while still remaining a bounded driver rather than a production compression service.

The compression-library seed-stability pass then repeats the key policies on a second deterministic input seed for both Zstd and zlib. Across four seed/library points, COPPER and SPP+COPPER slack both keep at least 99.4% CTLW reduction versus naive DMP, all policy return codes and per-seed checksums agree, COPPER/slack translation faults remain zero, and the worst absolute SPP+COPPER slack timing gap versus SPP is 0.183 percentage points. This is stronger than a one-off compression-library result, while still not replacing a production compression-service workload.

A DRAM-energy scorecard then uses gem5's emitted DRAM rank energy counters across 26 full-system points: the 12-point app/service matrix plus TLS/session-service, OpenSSL libssl TLS memory-BIO, OpenSSL SHA256, OpenSSL EVP/HMAC, public PCRE2, public libxml2 XML, public libarchive TAR, public Zstd, public zlib, and scaled process-separated OpenSSL libssl TCP-netns points. This is memory-system energy, not full-chip McPAT or silicon power. Standalone COPPER has mean total DRAM-energy delta -0.232% and operation-energy delta +0.598% versus no prefetch, slightly better than naive DMP at -0.212% and +0.712%. COPPER has lower-or-equal total DRAM energy than naive on 13/26 points and lower-or-equal DRAM operation energy on 19/26. SPP+COPPER slack remains close to SPP: total DRAM-energy gap averages +0.071% and DRAM operation-energy gap averages +0.203%.

A fixed-architecture McPAT sensitivity pass now adds a core/cache power sanity check over the same 26 full-system points and five policies, generating 130 successful McPAT rows from measured ROI cycles, instructions, cache/TLB accesses, and misses. This is still a proxy: the gem5 CPU is TimingSimple-style, the McPAT XML is an AArch64-style proxy, and COPPER metadata-table switching is not separately modeled. Under those limits, standalone COPPER has mean total-runtime-energy proxy delta -0.625% versus no prefetch, while naive DMP is -0.608%. SPP is -9.892% and SPP+COPPER slack is -11.521%, so the coexistence path remains favorable in this fixed proxy.

A Vivado RTL power-proxy pass now reports COPPER metadata structures directly. It opens 15 existing checkpoints and produces 15 successful `report_power` outputs. The strongest datapoint is the routed 64K-entry CLPD on `xc7a200tfbg676-2`: 0.479 W total on-chip FPGA power, 0.344 W dynamic, 0.135 W static, 260 block-RAM tiles, 636 LUT-as-logic, and medium confidence. That result says the largest COPPER metadata structure is storage-dominated on FPGA: 0.313 W of the 0.344 W dynamic estimate is block RAM, while LUT logic is only 0.001 W. The full LSQ/AMBA authority top and PEB reports are synthesized-only and low-confidence, so they are plausibility evidence, not power signoff. One tiny AMBA frontdoor report is intentionally retained as an out-of-context I/O artifact and is not used as an architectural power claim.

An additional CLPD activity-power pass closes part of the vectorless gap. XSim runs the existing CLPD SRAM testbench through 18 directed cases plus 4,000 randomized commit/purge/query operations with `errors=0`, emits SAIF, and Vivado reads that SAIF into a matching routed 64-entry CLPD checkpoint. Vivado matches 126 of 342 nets (37%) and reports 0.076 W total, 0.007 W dynamic, 0.069 W static, 2 block-RAM tiles, 95 LUT-as-logic, 76 registers, medium confidence, and WNS 2.208 ns. This proves the local tool flow can carry simulation activity into a routed COPPER metadata block, but it is still a testbench-scale activity point, not full-system workload SAIF or ASIC-calibrated power.

A workload-derived CLPD activity replay now strengthens that power story without pretending to be silicon signoff. The replay scales 1,318,318 measured gem5 COPPER events from 20 public app/service/parser/compression rows into 120,000 RTL operations: 3,107 proof commits, 65,846 allowed queries, 49,322 no-provenance blocks, and 1,725 fault/permission blocks. XSim completes the replay with `errors=0`, and Vivado maps the resulting SAIF into a routed 1K-entry CLPD with 226/611 nets matched (37%). The resulting FPGA proxy is 0.083 W total, 0.014 W dynamic, 0.069 W static, 4 block-RAM tiles, 151 LUT-as-logic, 144 registers, medium confidence, and WNS 1.807 ns. This is stronger than random activity because the switching ratios come from measured full-system counters, but it is still transaction-level replay, not an instruction-by-instruction full-system waveform or ASIC-calibrated power.

A metadata-toggle sensitivity bound then translates the same measured CLPD event mix into pJ/access accounting. Across the 20 matching public app/service/parser/compression rows, the model counts 34,131 learned-proof writes and 1,284,187 authority reads. Under a deliberately high 20 pJ read, 40 pJ write, and 5 pJ compare/event scenario, estimated metadata access energy is 33.641 uJ, 0.1887% of matching COPPER DRAM operation energy and 0.002097% of total DRAM energy. This is still not SRAM compiler or silicon power, but it makes the "metadata energy probably does not dominate" claim quantitative and rerunnable.

A process-server TCP metadata-toggle bound then applies the same pJ/access accounting style to the strongest libssl TCP process-separated evidence and now normalizes it to the matching gem5 DRAM counters. Across four selected process-server points, including scaled four-pair and eight-pair points, standalone COPPER has 179,343 metadata events and SPP+COPPER slack has 268,494. Under the same deliberately high scenario, metadata energy is 4.633 uJ for standalone COPPER and 6.818 uJ for SPP+COPPER slack. Those bounds are 0.1239% and 0.1510% of matching DRAM operation energy, respectively, and at most 0.005412% of matching total DRAM energy. This shows that the forked TCP/TLS evidence does not create a large metadata-access signal under the stated assumptions.

A TCP process-server CLPD activity replay then drives the Vivado SAIF flow with the conservative SPP+COPPER slack counter mix from those four process-separated TCP points. The replay is unscaled at 268,494 operations: 5,293 proof commits, 39,024 allowed queries, 222,955 no-provenance blocks, and 1,222 fault/permission blocks. XSim completes with `errors=0`, and Vivado maps the SAIF into the routed 1K-entry CLPD with 226/611 nets matched (37%), reporting 0.083 W total, 0.014 W dynamic, 0.069 W static, medium confidence, and WNS 1.807 ns. This strengthens the TCP side-effect story beyond pJ/access accounting, while still remaining transaction-level FPGA replay rather than instruction-level full-system switching or ASIC signoff.

A generated public artifact manifest now reduces the packaging risk created by the large local results tree. It records 573 hashed entries with zero missing references, recommends 571 files, 6,096,123 bytes, for the minimal public package, and marks two SAIF files / 13,479,413 bytes as optional external-store evidence by hash. A materialized package build now copies those direct-package rows plus four generated metadata files into a 575-file reviewer package with zero missing files and zero hash mismatches. This does not make the science stronger by itself, but it makes the current claim set more reviewable and less likely to fail artifact evaluation because of stale or oversized local paths.

The 2026-06-18 service-style addendum adds a crypto-adjacent TLS/session-service native AArch64 Linux ROI. It is not a production TLS stack; it combines session hash-table lookup, LRU session state, linked record chains, and constant-time-ish record-authentication arithmetic over ticket/mask words that are loaded but never used as architectural addresses. On this point, all policies preserve checksum `0x92f3bb62393cd786` and `rc=0`. Naive DMP records 3,680 CTLW misses, COPPER CLPD-64K+PEB records 18, and SPP+COPPER slack records 19, so both COPPER paths reduce CTLW misses by 99.5% with zero translation faults. SPP is the best conventional timing baseline at -13.686%, while SPP+COPPER slack is -13.712%, reinforcing the coexistence claim while leaving production TCP/TLS/standard-crypto and production-service evaluation as an honest remaining gap.

The real-TLS addendum then runs OpenSSL libssl's TLS 1.2 PSK handshake and TLS record read/write path over paired memory BIOs from a native AArch64 Linux ROI. The harness uses a deterministic benchmark RNG to avoid guest entropy blocking in gem5 and is still an in-process memory-BIO driver, not a production TCP/TLS server. In the smoke-scale all-policy run, all eight policies preserve checksum `0x204756e92baedd9b` and `rc=0`. Naive DMP records 2,411 CTLW misses, COPPER CLPD-64K+PEB records 29, and SPP+COPPER slack records 54, so COPPER reduces CTLW misses by 98.8% and slack by 97.8%, both with zero translation faults. SPP is the best conventional timing baseline at -2.614%, and SPP+COPPER slack is close at -2.604%. The medium-scale two-seed key-policy rerun doubles sessions and handshakes, uses two TLS records, and deepens the metadata scan. Across two seeds, COPPER keeps at least 98.8% CTLW reduction, SPP+COPPER slack keeps at least 97.2% CTLW reduction, every run preserves checksum agreement and `rc=0`, and COPPER/slack translation faults stay at zero. This materially strengthens the TLS-library path, while still falling short of a production TCP/TLS server.

A socket-backed TLS addendum then removes the memory-BIO-only criticism for one tractable point. The new native AArch64 workload runs the same OpenSSL libssl TLS 1.2 PSK handshake and record read/write path over a nonblocking Linux AF_UNIX socketpair while preserving session hash/LRU metadata and pointer-shaped ticket words. Across `none`, `naive`, `copper_clpd64k_peb`, `spp`, and `spp_copper_slack`, all runs preserve checksum `0xab75647a27a441b7` and `rc=0`. Naive DMP records 16,554 CTLW misses; COPPER records 144 for a 99.1% reduction; SPP+COPPER slack records 296 for a 98.2% reduction; all key policies have zero translation faults. SPP gives -2.181% ticks versus no prefetch, while SPP+COPPER slack gives -2.220%, so the coexistence story also survives the socket path. This is stronger than memory BIO, but it is still an in-process socketpair service driver rather than a production TCP/TLS server.

A TCP loopback libssl harness was also built. Direct host-namespace TCP loopback under the current no-systemd ARM64 gem5 boot fails before TLS exchange with errno 99/101: the loopback interface is down, the local route table is empty, and the workload cannot raise host `lo`; a fuller systemd boot begins normal networking startup but did not reach the workload within the local 20-minute timeout. The patched harness therefore records an explicit transport tag. Its fallback diagnostic records `transport=af_unix_fallback`, preserves checksum `0xeb221e7bd6b9662b` and `rc=0`, cuts CTLW misses from 8,839 to 177 under COPPER, and remains useful as socket-backed libssl evidence. The stronger strict run creates a private user/network namespace inside the guest process, raises loopback there, and all five key policies record `transport=tcp_loopback_netns`, `strict_tcp=1`, and `afunix_fallback_pairs=0`; COPPER cuts naive-DMP CTLW misses from 9,645 to 221 for a 97.7% reduction, SPP+COPPER slack records 269 for a 97.2% reduction, and faults remain zero. The process-server run then forks a TLS server process and uses the parent as TLS client over AF_INET loopback inside the same private namespace. A two-seed audit records `transport=tcp_loopback_netns_process` for every row, two distinct checksums, 10 total forked TCP pairs, 0 child failures, 0 COPPER/slack faults, 98.5% minimum COPPER CTLW reduction, and 98.1% minimum SPP+COPPER slack reduction, with a 0.130 percentage-point worst slack gap versus SPP. This is process-separated guest TCP-loopback TLS-library evidence, but still a bounded local harness rather than a production TCP/TLS deployment.

The same-day crypto-library addendum then runs OpenSSL libcrypto's exported `SHA256` routine through the guest dynamic loader from a native AArch64 Linux ROI. This is real libcrypto execution, but still a small driver rather than a full TLS stack or production crypto benchmark. All policies preserve checksum `0x81965a75cf2e6850` and `rc=0`. Naive DMP records 10,590 CTLW misses, COPPER CLPD-64K+PEB records 301, and SPP+COPPER slack records 259, so COPPER reduces CTLW misses by 97.2% and slack by 97.6%, both with zero translation faults. After adding stride, DCPT, SPP, and AMPM controls, SPP is the best conventional timing baseline at -16.598%, and SPP+COPPER slack reaches -16.660%.

A broader OpenSSL crypto-suite addendum then calls libcrypto EVP AES-128-CTR, HMAC-SHA256, SHA256, and `CRYPTO_memcmp` from the guest. In the smoke-scale all-policy run, all policies preserve checksum `0x444a220a9b27e7d0` and `rc=0`. Naive DMP records 16,685 CTLW misses, COPPER CLPD-64K+PEB records 954, and SPP+COPPER slack records 828, so COPPER reduces CTLW misses by 94.3% and slack by 95.0%, both with zero translation faults. After adding stride, DCPT, SPP, and AMPM controls, SPP is the best conventional timing baseline at -14.501%, and SPP+COPPER slack reaches -14.552%. The medium-scale two-seed key-policy rerun doubles sessions and requests and uses two crypto rounds. Across two seeds, COPPER keeps at least 95.0% CTLW reduction, SPP+COPPER slack keeps at least 95.6% CTLW reduction, every run preserves checksum agreement and `rc=0`, COPPER/slack translation faults stay at zero, and the worst absolute SPP+COPPER-versus-SPP tick gap is 0.021 percentage points. This is stronger libcrypto evidence than the earlier smoke point, though it is still a bounded service-style driver rather than a broad standard crypto benchmark campaign.

An OpenSSL-speed-like addendum then runs real guest libcrypto AES-128-CTR, SHA256, HMAC-SHA256, and `CRYPTO_memcmp` over fixed benchmark-style buffer sizes of 64, 256, 1024, and 4096 bytes while retaining pointer-shaped metadata loaded as data. This is closer to `openssl speed` than the service-style driver, but it is still a local native ROI rather than the official OpenSSL CLI benchmark. In the first seed, all policies preserve checksum `0x8f37fdbf14f45f13` and `rc=0`. Naive DMP records 16,353 CTLW misses, COPPER CLPD-64K+PEB records 1,257, and SPP+COPPER slack records 1,093, so COPPER reduces CTLW misses by 92.3% and slack by 93.3%, both with zero translation faults. SPP is the strongest conventional timing baseline at -13.213%, and SPP+COPPER slack is close at -13.172%, a +0.041 percentage-point gap. A second-seed rerun preserves the pattern: COPPER keeps 92.3% minimum CTLW reduction, SPP+COPPER slack keeps 92.7% minimum reduction, both have zero translation faults, and the worst absolute slack-vs-SPP tick gap across the two seeds is 0.089 percentage points.

An official OpenSSL CLI feasibility pass narrows the remaining crypto-benchmark caveat. The Ubuntu ARM64 `openssl_3.0.13-0ubuntu3_arm64.deb` binary executes under the same full-system path and reports `OpenSSL 3.0.13 30 Jan 2024` with `rc=0`. However, the smallest honest official speed attempt, `openssl speed -elapsed -seconds 1 -bytes 64 sha256`, remained inside the timer-driven speed loop after a 30-minute local wall-clock limit and produced no completed ROI statistics. This is compatibility evidence, not a benchmark result, and it justifies keeping the fixed-count speed-like driver while explicitly saying it is not the official CLI benchmark. A later official CLI TLS-pair probe confirms the guest has `/usr/bin/openssl` OpenSSL 3.0.13 and can execute it through the new file-based guest ROI script path, but the `openssl s_server`/`s_client` pair reaches private-netns entry and server launch without completing under local timing or atomic gem5 host-time limits. That pair is recorded as negative feasibility evidence, not as benchmark evidence; the completed process-separated libssl TCP-netns workload remains the TCP/TLS-library benchmark path.

The official CLI path is now stronger than compatibility only: a fixed-workload run injects the same Ubuntu ARM64 `openssl` binary, creates a deterministic 64 KiB pointer-shaped guest file before ROI, and measures `openssl dgst -sha256 /tmp/openssl_cli_input.bin` under full-system timing mode. All policies preserve SHA256 digest `77d85bbaaba62a96c40a96e4d9caf5d1265da704daade3a9f10d8e9dd8617cbe`, input checksum `0xc59a1575a221a8e6`, and `rc=0`. Naive DMP records 15,940 CTLW misses; COPPER CLPD-64K+PEB records 387, a 97.6% reduction; SPP+COPPER slack records 415, a 97.4% reduction. Both COPPER paths have zero translation faults. SPP is the strongest timing baseline at -17.786%, and SPP+COPPER slack is -17.691%, a +0.095 percentage-point gap. This is official-command evidence, but still not the timer-driven official `openssl speed` benchmark.

An official OpenSSL CLI AES-CTR fixed-workload run then uses the same Ubuntu ARM64 `openssl` binary to execute `openssl enc -aes-128-ctr` over the deterministic 64 KiB pointer-shaped guest input, followed by an official `openssl dgst -sha256` fingerprint of the encrypted output. All policies preserve encrypted-output digest `39839fb42f8d96fc3a570c163b6cd2edebb8467713d1de6671ede4f99382a076`, input checksum `0xc59a1575a221a8e6`, main `rc=0`, and after-command `rc=0`. Naive DMP records 32,174 CTLW misses; COPPER CLPD-64K+PEB records 1,463, a 95.5% reduction; SPP+COPPER slack records 1,549, a 95.2% reduction. Both COPPER paths have zero translation faults. SPP is the strongest timing baseline at -18.515%, and SPP+COPPER slack is -18.468%, a +0.047 percentage-point gap. This is official-command AES evidence, but still not the timer-driven official `openssl speed` benchmark.

An official OpenSSL CLI HMAC-SHA256 fixed-workload run then uses the same Ubuntu ARM64 `openssl` binary to execute `openssl dgst -sha256 -hmac` over the deterministic 64 KiB pointer-shaped guest input. All policies preserve HMAC digest `d3be5389af52965eb3084df01f75d9ed50f9af56e0cd391d05d760e034d7130a`, input checksum `0xc59a1575a221a8e6`, and `rc=0`. Naive DMP records 16,903 CTLW misses; COPPER CLPD-64K+PEB records 524, a 96.9% reduction; SPP+COPPER slack records 435, a 97.4% reduction. Both COPPER paths have zero translation faults. SPP is the strongest conventional timing baseline at -17.323%, and SPP+COPPER slack is -17.335%, a -0.012 percentage-point gap. This adds official-command MAC evidence, but still not the timer-driven official `openssl speed` benchmark.

A three-seed official CLI stability pass then repeats SHA256, AES-CTR plus digest, and HMAC over two additional deterministic pointer-shaped input seeds. Across nine official CLI seed/workload points, COPPER CTLW reduction is at least 95.5%, SPP+COPPER slack CTLW reduction is at least 95.2%, both COPPER paths keep zero translation faults, all digest/MAC fingerprints and return codes are policy-independent, and the worst absolute SPP+COPPER slack gap versus SPP is 0.294 percentage points. This materially strengthens standard-crypto evidence while still not being timer-driven `openssl speed`.

The gem5/Bash workflow blocker is also closed for this OpenSSL CLI path. A PowerShell-native runner now injects the repo-local MSYS/UCRT runtime path and launches gem5 with direct stdout/stderr capture; a `sha256` smoke run reaches timing mode and work-end with a valid stats file. This is a reproducibility fix, not a new performance claim.

## Core Mechanism Definition

COPPER's invariant:

```text
allow_dmp(source_word, value, context)
    iff committed execution previously used that exact source word/value
        as an address source
    and the source word has remained clean since proof
    and source/target protection context matches
    and target translation and permission checks succeed
```

The current strongest mechanism has these named additions:

- **RCP, Recursive Carried-Provenance:** a COPPER-prefetched line may seed another data-dependent prefetch only if the source word/value already has committed proof in the provenance ledger. The carried record preserves identity/context, not authority.
- **CPTQ, Committed Page-Translation Queue:** cross-page candidates are issued only after the committed-provenance gate and a valid page-table translation.
- **CEPF, Commit-Epoch Provenance Filter:** backend proof creation is allowed only if the committed dependent memory operation carries a source epoch that still matches the current source-word epoch.
- **PASB, Provenance Address-Space Binding:** source proofs and carried-provenance records include an address-space token, preventing proof reuse after Linux process/address-space changes on the same hardware context.
- **CTLW, Committed Target-Line Witnessing:** cross-page recursive prefetches use an exact demand-observed virtual-to-physical line witness and witness-derived fills are terminal until demand-validated.
- **CLPD, Compressed Line-Provenance Directory:** retained source proof is compressed into source-cache-line entries with per-word proof masks and line epochs, closing a graph-scan proof-capacity cliff without authorizing changed line contents.
- **PEB, Provenance Epoch Boundary:** proof authority, carried provenance, target witnesses, and queued proof-derived prefetches are salted by a per-domain epoch/token boundary so pre-boundary authority cannot leak into post-boundary measurement or execution windows.
- **CS-SARI, Conflict-Scoped SoC Authority Revocation Interface:** DMA/coherence/remap/TLBI revocations hold only DMP candidates whose source line, target line, or token conflicts with the pending authority change; overflow falls back to conservative global hold.

## Why It Is Not Merely a Combination

COPPER is not new because it uses metadata, a prefetcher, or an RTL gate. Those are known blocks. The novel claim is the **authority invariant**: DMP dereference authority comes from committed architectural pointer use, not from address-shaped data. RCP extends this invariant recursively, so a prefetched line cannot bootstrap arbitrary pointer chasing unless its source word/value has already been proven by committed demand behavior.

## Prior-Art Comparison

| Prior art | Similarity | Difference | Novelty risk |
|---|---:|---|---:|
| Augury | Very high threat overlap | Demonstrates DMP data-at-rest leakage; not a hardware provenance defense. | 8 |
| GoFetch | Very high threat overlap | Shows practical crypto attacks from DMP activation on pointer-looking values; does not add committed source-word authority. | 8 |
| SplittingSecrets | High DMP defense overlap | Compiler transforms secrets so they do not look like addresses; COPPER changes hardware DMP authority. | 6 |
| PreFence / DIT / DOIT disable | Medium defense overlap | Coarse disable policy; COPPER is fine-grained and preserves safe DMP activity. | 5 |
| Pointer-chase / indirect prefetchers / ICP | High performance overlap | Prefetch irregular accesses but do not require committed proof for DMP dereference. | 7 |
| Taint, CHERI/Morello, MTE | Medium metadata/provenance overlap | Protect information flow or architectural pointer/memory safety, not DMP-specific positive authority. | 6 |
| COPPER-RCP/PASB/CTLW exact public search | Low exact overlap found | No public recursive DMP authority rule using committed source provenance plus exact committed target-line translation witnesses found in this pass. | 3 |

A 2026-06-19 refresh raises the terminology bar: recent linked-data-structure prefetching work explicitly describes missing pointer provenance as a CDP/DDP security flaw, and Okapi uses committed-load tracking for sandboxed speculative accesses. Those are important neighboring signals, but the refresh still did not find a public DMP mechanism that grants dereference authority only to a committed, clean, source-word/value/context proof with PASB, CTLW, PEB, and revocation hooks. The novelty claim must therefore stay narrow: COPPER is not "pointer provenance" in general; it is a DMP-specific authority invariant.

## Prototype and Model Summary

| Artifact | Purpose | Status |
|---|---|---|
| Python trace model | Measures unsafe DMP dereferences and speedup proxy under adversarial traces. | Completed |
| Python fuzz validation | Stale rewrite, first-use, cross-domain, translation, and permission stress cases. | 500 fuzz trials, 0 failures |
| SystemVerilog RTL | Core line-provenance gate, CEPF bridge, stream-table extension, full-authority CEPF/PASB/CTLW predicate gate, CTLW witness directory, CTLW-to-full-authority E2E harness, CLPD-CTLW authority E2E harness, SARI and CS-SARI revocation interfaces, full-authority SVA harness, CEPF-to-line end-to-end SVA harness, compact/scalable CLPD directories, and PEB epoch/token boundary block. | Vivado directed/randomized simulation and SVA assertion harnesses passed |
| Bounded invariant checkers | PASB/CTLW/terminal, richer CEPF/value/PASB/CTLW authority state machines, CLPD directory state space, and CS-SARI/CLPD/CTLW composition state space. | First checker passes 42 states; richer checker passes 11,419 states; CLPD checker passes 24,354 states; CS-SARI composition passes 7,555 states; weakened variants fail as expected |
| Security coverage matrix | Maps modeled unsafe DMP classes to the COPPER mechanism and local evidence artifact that covers them. | Ten unsafe classes checked; evidence string audit PASS |
| Vivado synthesis/implementation | Area/timing sanity checks on Artix-7 targets. | 10 ns met for the core gate and CEPF bridge; compact CLPD synthesis now completes; scalable CLPD-64K synthesizes and routes out-of-context on `xc7a200tfbg676-2`; PEB synthesizes on `xc7a35tcpg236-1` with 346 LUTs and WNS 3.782 ns |
| CS-SARI revocation trace proxies | Generic, GAPBS-topology, and queue-depth/conflict sensitivity streams compare global hold versus conflict-scoped hold. | Zero CS-SARI modeled unsafe issues; 269,879 GAPBS-topology authorized candidates recovered versus global hold; 20-config sweep reports 1,649,883 no-hold unsafe issues and 72.06% median scoped-hold reduction |
| Graph-style trace | CSR-like edge slots with adversarial data and rewritten edges. | 10-seed sweep completed |
| GAPBS-backed topology trace | Parses public GAPBS `.sg` graphs and replays edge-scan/BFS streams with COPPER policies and CLPD. | Five graph sizes, two kernels, five seeds, capacity sweep completed |
| Expanded GAPBS-style kernel trace | Replays PageRank-pull, SSSP-relaxation, CC label propagation, and triangle-oriented traces on GAPBS-generated topologies. | Five-graph main sweep: COPPER unsafe total 0; naive unsafe total 6,434,323 |
| Expanded GAPBS-style sensitivity | Sweeps proof entries, cache lines, lookahead, graph, kernel, and seed over the three largest generated topologies. | 4,320 policy/config runs; COPPER unsafe total 0; naive unsafe total 81,605,320; source-only unsafe total 284,488 |
| ChampSim | Baseline stock prefetcher behavior on pointer-shaped traces. | Built and run |
| GAPBS | Local graph benchmark readiness. | Scale-20 kernels verified |
| gem5 ARM/AArch64 SE | Timing cache/MSHR evaluation with COPPER/CPTQ/RCP. | Integrated and run |
| gem5 ARM64 full-system | Ubuntu/Linux boot/readfile plus native static AArch64 workload ROIs with L1D prefetcher attached. | Tiny PASB ablation, larger page-permuted/random CTLW-terminal timing, graph-gather control, compiled C suite, small/larger GAPBS-inspired mini-suite, official GAPBS g10/g12 controls, ROI-bracketed heap-pointer multi-seed runs, fake-only controls, and PEB runs completed |

## Results Table

| Workload / test | Baseline | COPPER result | Comparator | Interpretation |
|---|---:|---:|---:|---|
| Trace model, synthetic | disabled = 1.000x | COPPER-LINE = 2.414x, 0 unsafe modeled dereferences | naive = 3.628x but 2616 unproven-line prefetches | COPPER keeps useful speedup while blocking modeled unsafe DMP action. |
| Trace fuzz | 500 trials | 0 failures | N/A | Directed/fuzzed safety behavior holds in the model. |
| Vivado RTL invariant fuzz | 2000 randomized cycles | 339 allowed, 1152 blocked, 0 errors | independent scoreboard | RTL gate matches the clean committed-provenance invariant under mixed events. |
| Vivado full-authority gate | 12 directed + 5000 randomized cases | 956 allowed, 3731 blocked, 0 errors | independent scoreboard with named coverage | RTL-shaped predicate covers CEPF/PASB/CTLW/terminal authority, including no-source, unsound, stale, PASB, witness, terminal, and permission classes. |
| Vivado full-authority SVA | 12 directed + 10,000 randomized assertion samples | 1,919 allowed, 7,455 blocked | SVA properties plus coverage counters | Asserts allow requires exact source proof, PASB token, non-terminal source, target authority, and permission success. |
| Vivado CEPF-line E2E SVA | 12 directed + 10,000 randomized samples | 2,257 valid commits, 769 proof-to-allow cases, 0 errors | shadow proof model plus assertions | Ties CEPF proof creation to line proof storage and DMP gate consumption across cycles. |
| Vivado CTLW witness directory | 10 directed + 10,000 randomized samples | 1,484 exact hits, 6,712 misses, 0 errors | shadow witness table plus assertions | Checks exact witness match, token mismatch, line alias mismatch, remap/TLBI clear, and collision eviction. |
| Vivado CTLW-full-authority E2E | 12 directed + 10,000 randomized samples | 3 exact cross-page allows, 7,102 no-witness blocks, 0 errors | CTLW directory wired into final authority gate | Checks exact witness opens cross-page DMP issue and absent, aliased, stale, terminal, permission, and collision cases block at the consumer gate. |
| Vivado CLPD-CTLW authority E2E | 18 directed + 10,000 randomized samples | 180 joint cross-page allows, 8,468 no-source blocks, 0 errors | CLPD source directory + CTLW target directory + authority gate | Checks compressed source proof and exact target witness must both be live; source write/fill/invalidate and target remap/TLBI revoke authority. |
| Vivado SARI revoker | 8 directed + 10,000 randomized cycles | 6,321 immediate holds, 4 ready-low and 4 overflow observations, 0 errors | SoC revocation queue plus DMP hold | Maps DMA/CHI/coherent-I/O writes to queued source clears, remap/TLBI to CTLW, and holds DMP issue while revocation is pending. |
| Vivado SARI-CLPD-CTLW authority E2E | 12 directed + 10,000 randomized samples | 1,828 hold suppressions, DMA/CHI/I/O/remap/TLBI post-blocks, 0 errors | SARI wired into final authority path | Checks no stale issue during same-cycle external revocation and post-drain source/target blocking. |
| Vivado CS-SARI authority E2E | 12 directed + 10,000 randomized samples | 1,245 conflict holds, 1,007 avoided global holds, 0 errors | conflict-scoped revocation hold | Matching source/remap/TLBI/queued/overflow hazards hold; unrelated source/remap/token events safely issue. |
| CS-SARI GAPBS-topology proxy | 3 scenarios over graph-derived source/target locality | 82.06% aggregate hold reduction, 269,879 authorized candidates recovered, 0 CS-SARI unsafe modeled issues | global SARI and no-hold policies | Shows scoped hold recovers issue opportunities while no-hold produces 59,013 modeled stale-authority unsafe issues. |
| CS-SARI composition checker | full composed CLPD/CTLW/CS-SARI rule | PASS, 7,555 reachable states | weakened hold and authority variants | Shows the composed rule requires scoped hold, live source proof, live target witness, token match, remap/TLBI invalidation, and overflow fallback; weakened variants fail as expected. |
| CS-SARI sensitivity sweep | 20 queue-depth/conflict configurations | 0 CS-SARI unsafe modeled issues, 1,649,883 no-hold unsafe issues, 72.06% median scoped-hold reduction | global SARI and no-hold policies | Shows scoped hold remains safe and useful across queue depths 1-16 and low-conflict/balanced/hot-source/target-churn profiles. |
| Vivado CLPD gate | 14 directed + 5000 randomized cases | 4 allowed, 5012 blocked, 0 errors | independent directory scoreboard | RTL-shaped compressed line-proof directory covers word masks, stale line epochs, token mismatch, write/fill/invalidate clearing, and collision eviction. |
| Bounded CLPD checker | full CLPD | PASS, 24,354 states explored | weakened variants fail in 2-17 states | Checks CLPD tag, token, epoch, per-word mask, write clear, fill clear, and invalidate clear requirements against ground truth. |
| Security coverage matrix | 10 unsafe classes | PASS evidence string audit | residual risks listed per class | Maps each modeled unsafe class to a COPPER mechanism and source-backed local artifact. |
| Vivado core gate | 10 ns target | WNS +8.122 ns, 2063 LUTs, 1024 regs | no BRAM/DSP | Core gate is implementable as a small standalone RTL block. |
| Vivado CEPF bridge | 10 ns max-delay target | WNS +3.682 ns, 5 LUTs, 0 regs | no BRAM/DSP | Backend stale-source proof filter is tiny in RTL. |
| Graph-style CSR trace | disabled = 1.000x | COPPER epoch/value = 3.276x, 0 unsafe modeled dereferences | naive = 7.991x but 10240 data-at-rest PF; source-only = 1638 stale PF | CEPF/value binding fixes the stale rewritten-edge limitation. |
| GAPBS-backed topology trace | disabled = 1.000x | COPPER epoch/value = 1.770x, CLPD = 1.896x, 0 data-at-rest/unproven/stale PF | naive = 4.096x but 16,384 data-at-rest PF and 295,463.1 unproven-edge PF | COPPER behavior holds on five GAPBS-generated graph topologies. |
| Expanded GAPBS-style kernel trace | disabled = 1.000x | COPPER-epoch = 1.768x, COPPER-CLPD = 1.592x, 0 unsafe modeled PF | naive = 3.743x but 6,434,323 total unsafe modeled PF | COPPER generalizes beyond edge/BFS traces to PageRank, SSSP, CC, and triangle-style access shapes. |
| Expanded GAPBS-style sensitivity | 4,320 policy/config runs | COPPER unsafe modeled PF = 0 | naive = 81,605,320 unsafe PF; source-only = 284,488 unsafe PF | Stress-tests proof-table size, cache size, lookahead, graph, kernel, and seed; CLPD mitigates the capacity cliff. |
| GAPBS g12 proof capacity | edge-exact 65,536 entries = 1.000x | CLPD 8,192 line entries = 2.115x, 0 unsafe counters | edge-exact 131,072 entries = 2.369x | CLPD fixes a real capacity cliff by compressing clean source-line proof. |
| CLPD storage model | edge-exact full coverage on g12 = 1252.18 KiB | CLPD full coverage on g12 = 39.87 KiB | 31.40x smaller under stated assumptions | Storage proxy explains why CLPD is more plausible than simply enlarging edge-exact proof tables. |
| CLPD g12 measured storage point | CLPD 8,192 entries = 54.00 KiB | 2.115x speedup, 62,713 useful PF hits | edge-exact 131,072 entries = 1696.00 KiB for 2.369x | CLPD recovers most of the useful graph-stream prefetching at far lower storage proxy cost. |
| Vivado CLPD SRAM directory | 18 directed + 4,000 randomized XSIM trials | 3 allowed, 4,011 blocked, 0 errors | independent scoreboard with pending-update and alias-purge cases | The scalable directory keeps one-cycle query behavior while closing update hazards conservatively. |
| Vivado CLPD-64K synthesis/route | `xc7a200tfbg676-2`, 10 ns | synth: 629 LUTs, 156 FFs, 260 BRAM, WNS +3.274 ns; route: 636 LUTs, 170 FFs, 260 BRAM, WNS +0.362 ns | out-of-context block implementation | Shows the exact 64K capacity used by the best gem5 runs is hardware-plausible as an SRAM/BRAM-backed structure. |
| Vivado PEB RTL | directed boundary/token/domain/wrap tests | 11 directed cases, 9 boundaries, 0 errors | Artix-7 synthesis: 346 LUTs, 147 FFs, WNS +3.782 ns | Turns provenance reset from a simulator cleanup into a small O(1) epoch/token hardware mechanism. |
| gem5 page-permuted 8192 nodes | no prefetch = 3514397000 ticks | recursive COPPER = 6.76-6.78% speedup | stride = 0.69% | COPPER survives when stride loses the pattern. |
| gem5 random 8192 nodes | no prefetch approx 4114-4120M ticks | recursive COPPER = 5.59-5.66% speedup | stride = 0.59% | CPTQ+RCP rescue cross-page random pointer chains. |
| gem5 random seed 1 MSHR | demand MSHR misses = 33026 | demand MSHR misses = 8451 | PF MSHR misses = 25166 | Benefit comes from converting demand-visible misses into prefetch-origin misses. |
| gem5 medium page-permute | no prefetch = 52705000 ticks | recursive COPPER = 15.06% speedup | stride = 0.17% | Smaller workload confirms the issue path. |
| gem5 AArch64 page-permute | no prefetch = 3521756000 ticks | recursive COPPER = 6.77% speedup | stride = 0.67% | Direct AArch64 ELF confirms the ARM32 trend. |
| gem5 AArch64 random | no prefetch = 4126726000 ticks | recursive COPPER = 5.61% speedup | stride = 0.57% | Direct AArch64 ELF confirms the cross-page random result. |
| gem5 AArch64 Minor/O3 | irregular full lists | recursive COPPER = 2.64-2.79% Minor, 2.68-2.77% O3 | stride = 0.11-0.59% | Benefit survives deeper CPU models. |
| gem5 AArch64 O3 traffic | no prefetch read bytes = 2113920 | COPPER read bytes = 2123968-2124416 | +0.48-0.50% | O3 gain is not bought with a large bandwidth increase on these tests. |
| gem5 ARM64 full-system probe | Ubuntu/Linux 6.8.12, `no_systemd=true` | `aarch64`, probe start/end markers | 470.7M simulated instructions | Full-system environment works. |
| gem5 ARM64 full-system timing ROI | none | 3,571,493,265 ticks, 38,899 L1D misses | native AArch64 ROI under Linux | Full-system timing denominator. |
| gem5 ARM64 full-system timing ROI | stride | 3,382,963,983 ticks, 15,443 prefetches, 7,125 useful | -5.279% ticks vs none | Regular stride helps this tiny stream-like ROI. |
| gem5 ARM64 full-system timing ROI | naive pointer-shaped DMP | 40 prefetches, 0 useful, 30 translation faults | +0.024% ticks vs none | Address-shapedness creates useless/faulted recursive attempts. |
| gem5 ARM64 full-system timing ROI | COPPER before PASB | 102 pointer-like candidates, 69 learned proofs, 5 allowed, 5 translation faults | same ticks as none | Full-system run exposed address-space-binding hole. |
| gem5 ARM64 full-system timing ROI | PASB-COPPER | 102 pointer-like candidates, 63 learned proofs, 0 allowed, 102 blocked, 0 translation faults | same ticks as none | PASB converts unsafe recursive authorizations into clean blocks. |
| gem5 ARM64 larger full-system page-permute | none | 5,174,659,494 ticks, 76,239 L1D misses | generated native AArch64 ROI | Larger full-system denominator. |
| gem5 ARM64 larger full-system page-permute | COPPER CTLW-terminal | 5,147,204,976 ticks, 24,229 PF issued, 0 translation faults | -0.531% ticks vs none | CTLW removes PASB-only faults and keeps recursion bounded. |
| gem5 ARM64 larger full-system random | none | 5,321,033,973 ticks, 75,792 L1D misses | generated native AArch64 ROI | Random full-system denominator. |
| gem5 ARM64 larger full-system random | naive DMP + CTLW | 27,433 pointer-like allowed, 0 blocked | -0.261% ticks vs none | Translation witnessing alone is not source authority. |
| gem5 ARM64 larger full-system random | COPPER CTLW-terminal | 12,341 allowed, 15,259 blocked, 0 translation faults | -0.271% ticks vs none | COPPER keeps nearly same timing while enforcing source authority. |
| gem5 ARM64 full-system graph-gather | none | 5,272,379,010 ticks, 91,676 L1D misses | generated CSR-like edge binary | Application-shaped denominator beyond pure pointer chains. |
| gem5 ARM64 full-system graph-gather | stride | 4,831,167,330 ticks, 11,337 useful PF | -8.368% ticks vs none | Edge-array stream favors conventional stride. |
| gem5 ARM64 full-system graph-gather | naive DMP + CTLW | 11,479 allowed, 0 blocked | -0.403% ticks vs none | Naive is slightly faster but has no source-authority block. |
| gem5 ARM64 full-system graph-gather | COPPER CTLW-terminal | 49,891 allowed, 8,660 blocked, 0 translation faults | -0.367% ticks vs none | COPPER stays close to naive while enforcing authority. |
| Bounded PASB/CTLW checker | full rule | PASS, 42 states explored | no counterexample depth 10 | Ties the named mechanism to explicit invariants. |
| Bounded PASB/CTLW checker | no-PASB/no-CTLW/no-terminal variants | FAIL as expected | 12/13/24 states to counterexample | Demonstrates why each refinement exists. |
| Rich authority state-space checker | full CEPF/value/PASB/CTLW/terminal rule | PASS, 11,419 states explored | no counterexample depth 12 | Strengthens the proof story beyond the tiny PASB/CTLW model. |
| Rich authority state-space checker | weakened variants | FAIL as expected | 80-508 states to counterexample | Finds stale backend proof, missed source invalidation, token reuse, page-witness, remap, and terminal-fill bugs. |
| ROPL replay/exception/alias contract | full Retirement-Only Provenance Latching rule | PASS, 888 unique states, 1 legal proof, 0 unsafe proofs | weakened variants all produce counterexamples | Checks that proof creation is blocked across replay, squash, exception, same-line alias kill, memory-order violation, and target permission hazards. |
| ROPL-LSQ retire guard RTL | registered 10 ns wrapper around retire-time proof gate | XSim PASS: 18 directed + 20,000 randomized cycles, 0 errors | 14 LUTs, 49 FFs, WNS +6.492 ns | Makes the ROPL replay/squash/alias/order/exception/permission rule a concrete synthesizable backend interface. |
| ROCCA-to-CLPD commit adapter RTL | Retirement-Ordered Clear-wins CLPD Adapter | XSim PASS: 11 directed + 20,000 randomized cycles, 0 errors | ROCCA+64-entry CLPD wrapper: 4,302 LUTs, 2,624 FFs, WNS +1.149 ns | Checks the final proof-write race: same-cycle source-line write/fill/invalidate/global proof-boundary clear suppresses retained CLPD proof creation. |
| CAVI final authority issue gate RTL | Commit-Authority Validity Interlock | XSim PASS: 14 directed + 20,000 randomized trials, 0 errors | 4,591 LUTs, 2,791 FFs, WNS +1.149 ns | Couples ROCCA/CLPD source proof to target-witness freshness so stale source clears, remaps, TLBI, permission downgrades, and queued target revocations all block final DMP issue. |
| gem5 ARM64 full-system compiled C suite | none | 4,600,705,023 ticks, checksum 0x5bf8bf1b | LLVM/clang AArch64 graph/hash/tree/fake-pointer binary | Compiler-authored full-system denominator. |
| gem5 ARM64 full-system compiled C suite | stride | 4,459,479,390 ticks, 9,234 useful PF | -3.070% ticks vs none | Sequential initialization/scans favor stride. |
| gem5 ARM64 full-system compiled C suite | naive DMP + CTLW | 1,583 allowed, 0 blocked | -0.030% ticks vs none | Naive has little benefit but no source-authority block. |
| gem5 ARM64 full-system compiled C suite | COPPER CTLW-terminal | 904 allowed, 679 blocked, 0 translation faults | +0.093% ticks vs none | Safety survives compiled C; not a speedup point. |
| gem5 ARM64 full-system GAPBS-inspired mini-suite | none | 3,770,630,928 ticks, checksum 0xf1dd4e4d | LLVM/clang AArch64 BFS/SSSP/PageRank/CC-shaped binary | Graph-kernel full-system denominator. |
| gem5 ARM64 full-system GAPBS-inspired mini-suite | stride | 3,660,924,078 ticks, 10,313 useful PF | -2.910% ticks vs none | Sequential edge-array scans favor stride. |
| gem5 ARM64 full-system GAPBS-inspired mini-suite | naive DMP + CTLW | 2,243 allowed, 408 CTLW misses, 408 unavailable translations | +0.002% ticks vs none | CTLW alone still permits all pointer-like candidates. |
| gem5 ARM64 full-system GAPBS-inspired mini-suite | COPPER CTLW-terminal | 1,288 allowed, 952 blocked, 0 CTLW misses, 0 translation faults | +0.000% ticks vs none | Authority gate prevents unproven graph-kernel issue while preserving neutral timing. |
| gem5 ARM64 larger GAPBS-inspired mini-suite | none | 7,449,479,397 ticks, checksum 0x0ba8df31 | LLVM/clang AArch64 BFS/SSSP/PageRank/CC-shaped binary | Larger graph-kernel full-system denominator. |
| gem5 ARM64 larger GAPBS-inspired mini-suite | stride | 7,373,493,459 ticks, 22,955 useful PF | -1.020% ticks vs none | Sequential edge-array scans still favor stride. |
| gem5 ARM64 larger GAPBS-inspired mini-suite | naive DMP + CTLW | 6,295 allowed, 6 CTLW misses, 6 unavailable translations | -0.239% ticks vs none | Translation witnessing alone still lacks source authority. |
| gem5 ARM64 larger GAPBS-inspired mini-suite | COPPER CTLW-terminal | 4,953 allowed, 1,340 blocked, 0 CTLW misses, 50,737 terminal stops | -0.208% ticks vs none | Scales the graph-kernel safety/control point while remaining near-neutral on timing. |
| gem5 ARM64 heap ROI, 3 seeds | no prefetch = seed-local baseline | CLPD-64K mean -2.866% ROI ticks; CLPD-64K+PEB mean -2.905% | naive DMP mean +15.214%, 1,568,208 CTLW misses | Full-system pointer-heavy evidence now survives heap-layout seed variation with zero COPPER/PEB CTLW misses and matching checksums. |
| gem5 ARM64 fake-only ROI | no architectural pointer traversal | CLPD-64K+PEB blocks 131,066/131,066 fake observations, issues 0 prefetches, +0.033% ticks | naive DMP +396.087%, 102,409 CTLW misses; CLPD-64K without PEB allowed 6 warm candidates | PEB closes the measured warm-state data-at-rest leakage without relying on a directory sweep. |
| gem5 ARM64 official GAPBS g10 suite | BFS/CC/PR/SSSP/BC/TC | CLPD-64K+PEB +0.015% aggregate ticks, 0 translation faults, 0 proof evictions, 482 CTLW misses | naive DMP +0.060%, 47,176 CTLW misses | Official AArch64 GAPBS is a safety/control suite: not pointer-heavy, but it validates clean execution and boundary behavior across six kernels. |
| gem5 ARM64 public Olden randomized small | Treeadd/Bisort/MST/Health | COPPER CLPD-64K+PEB -0.398% ticks, 547,939 PF, 29,039 CTLW misses, 0 faults | naive DMP +0.039%, 188,223 CTLW misses; DCPT -5.742%; SPP -2.962%; AMPM -2.465% | Public pointer-intensive full-system workload: COPPER reduces unsafe/content-derived misses but is not the fastest conventional prefetcher. |
| gem5 ARM64 public Olden randomized medium | Treeadd/Bisort/Health | COPPER CLPD-64K+PEB -2.616% ticks, 639,330 PF, 47,145 CTLW misses, 0 faults | naive DMP -2.829%, 123,516 CTLW misses; DCPT -7.025%; SPP -5.870%; AMPM -3.909% | Medium public workload strengthens the safety/performance tradeoff and prevents overclaiming universal speedup. |
| 12-point public app/service full-system baseline matrix plus 22-point traffic side-effect scorecard | SPP best conventional on 12/12, mean -13.112% ticks | SPP+COPPER slack mean -13.116%, worst gap 0.360 pp, 0 faults, 94.0% CTLW reduction | standalone COPPER baseline mean -0.492%; expanded side-effect scorecard pressure 0.879% vs naive 1.083% and 93.9% CTLW reduction | Fair conventional baselines show SCOOP preserves SPP-class timing while adding COPPER authority; COPPER alone is the low-overhead authority path, not the fastest prefetcher. |
| SQLite medium/stress seed stability | public SQLite amalgamation database-style workload | COPPER min CTLW reduction 90.3%, 0 faults | SPP+COPPER slack min CTLW reduction 86.4%, worst gap 0.056 pp | Adds standalone database-style seed stability across three medium and two stress points; still not a production database server. |
| Upstream SQLite speedtest1 JSON/star/ORM components | unmodified SQLite 3.53.2 `test/speedtest1.c`, `--testset json`, `star`, and `orm` | COPPER minimum CTLW reduction 92.3%, 0 faults | SPP+COPPER slack minimum CTLW reduction versus naive 88.5%, no slowdown versus SPP on these points | Adds public upstream benchmark-component evidence; tractable points are small and not full database benchmarks. |
| Lua/Duktape medium/stress seed stability | public Lua table and Duktape object workloads | COPPER min CTLW reduction 76.7% Lua / 90.5% Duktape, 0 faults | SPP+COPPER slack min CTLW reduction 96.3% Lua / 85.0% Duktape, worst gap 0.760 pp | Adds language-engine seed stability; Lua stress shows standalone COPPER is not uniformly high-reduction, while slack coexistence remains close to SPP. |
| yyjson medium/stress seed stability | public yyjson parser workload | COPPER min CTLW reduction 98.9%, 0 faults | SPP+COPPER slack min CTLW reduction 97.4%, worst gap 0.089 pp | Adds parser-engine seed stability across two medium and two stress points; still not browser or production-service JSON handling. |
| PCRE2 regex two-seed | public PCRE2 8-bit regex compiler/matcher through guest dynamic loader | COPPER min CTLW reduction 99.3%, 0 faults | SPP+COPPER slack min CTLW reduction 98.9%, worst gap 0.046 pp | Adds public regex parser/matcher-library seed stability; still not production log processing. |
| libxml2 XML tiny | public libxml2 XML parser/serializer through guest dynamic loader | COPPER CTLW reduction 98.9%, 0 faults | SPP+COPPER slack CTLW reduction 98.9%, gap 0.035 pp | Adds a second public XML/parser-family library point; still a bounded in-memory XML harness, not a production XML service. |
| libarchive TAR tiny | public libarchive TAR parser through guest dynamic loader | COPPER CTLW reduction 98.0%, 0 faults | SPP+COPPER slack CTLW reduction 98.6%, gap -0.004 pp | Adds a public archive/parser-library point; still a bounded in-memory TAR harness, not a production extraction service. |
| MiBench Patricia 12,288-record scale plus two-seed stability | public MiBench network/patricia trie plus public `small.udp` and `large.udp` inputs | COPPER min CTLW reduction 97.8%, 0 faults across two 12K seeds | SPP+COPPER slack min CTLW reduction 96.6%, worst 12K seed gap 0.035 pp; larger no-prefetch baselines complete at 16K/32K/full-large | Adds public pointer-rich trie benchmark-family evidence; larger policy comparisons remain negative feasibility evidence, not SPEC or production network routing. |
| JSON+SQLite medium two-seed stability | composed public yyjson plus SQLite service workload | COPPER min CTLW reduction 95.0%, 0 faults | SPP+COPPER slack min CTLW reduction 95.9%, worst gap 0.026 pp | Adds seed stability for the composed parser/database point; still not a production database server. |
| JSON+SQLite stress two-seed stability | composed public yyjson plus SQLite service workload | COPPER min CTLW reduction 91.4%, 0 faults | SPP+COPPER slack min CTLW reduction 96.6%, worst gap 0.069 pp | Adds stress-scale seed stability for the composed parser/database point; still not a production database server. |
| 24-point DRAM-energy scorecard | gem5 DRAM rank energy counters | COPPER total DRAM energy -0.210% mean, op energy +0.641% mean | naive -0.204% total, +0.750% op; slack within +0.088% total DRAM energy of SPP | Memory-system energy evidence; not full-chip/core power. |
| 125-row McPAT sensitivity scorecard | fixed AArch64-style proxy XML driven by measured gem5 ROI stats | COPPER total-runtime-energy proxy -0.312% mean; SPP+COPPER slack -11.249% | naive -0.301%; SPP -11.250% | Core/cache proxy sanity check; not calibrated silicon power and not COPPER metadata switching. |
| 15-checkpoint Vivado RTL power proxy | vectorless Vivado `report_power` over COPPER checkpoints | routed 64K CLPD: 0.479 W total, 0.344 W dynamic, 260 BRAM tiles, medium confidence | full LSQ/AMBA top: 0.118 W total synthesized low-confidence; PEB: 0.089 W total synthesized low-confidence | Direct RTL metadata power plausibility; not workload-SAIF or ASIC signoff. |
| CLPD SAIF activity power | XSim SAIF from 18 directed + 4,000 randomized CLPD operations | routed 64-entry CLPD: 37% net match, 0.076 W total, 0.007 W dynamic, WNS 2.208 ns | VCD negative control matched only 1/342 nets; SAIF unmatched list dominated by mapped RAM bits | Activity-driven RTL power sanity for the proof directory; still not full-system workload or ASIC power. |
| Workload-derived CLPD SAIF replay | measured gem5 COPPER counters from 20 app/service/parser/compression rows scaled into 120,000 RTL operations | routed 1K-entry CLPD: 37% net match, 0.083 W total, 0.014 W dynamic, WNS 1.807 ns | 3,107 commits, 65,846 allows, 49,322 no-provenance blocks, 1,725 fault blocks, `errors=0` | Ties metadata switching to measured workload ratios; still transaction-level replay, not instruction-by-instruction full-system waveform or ASIC power. |
| Metadata-toggle sensitivity bound | measured 20-row CLPD event mix | high scenario: 33.641 uJ metadata, 0.1887% of matching DRAM op energy | 34,131 writes, 1,284,187 reads | Quantifies metadata access order of magnitude; still not SRAM compiler or silicon power. |
| TCP process-server metadata-toggle bound | selected COPPER/slack rows from four process-separated TCP-netns libssl points | high scenario: 4.633 uJ COPPER, 6.818 uJ SPP+COPPER slack; max 0.1510% of matching DRAM op energy | 179,343 and 268,494 metadata events; 0 faults; 0 child failures | Bounds metadata side effects for the strongest TCP/TLS harness against matching gem5 DRAM counters; still pJ/access sensitivity accounting, not ASIC signoff. |
| TCP process-server CLPD SAIF replay | SPP+COPPER slack counter mix from four process-separated TCP-netns libssl points | 0.083 W total, 0.014 W dynamic, WNS 1.807 ns | 268,494 unscaled replay ops, 37% net match, `errors=0` | Runs the strongest TCP/TLS counter mix through XSim and Vivado power; still transaction-level FPGA replay, not ASIC signoff. |
| TLS/session-service crypto-adjacent stress | SPP best conventional, -13.686% ticks | SPP+COPPER slack -13.712%, 0 faults, 99.5% CTLW reduction | standalone COPPER -0.074%, 18 CTLW misses vs naive 3,680 | Adds service/session metadata and pointer-shaped ticket words under full-system AArch64; not a production TLS stack. |
| OpenSSL libssl TLS memory-BIO driver | SPP best of stride/DCPT/SPP/AMPM, -2.614% ticks | SPP+COPPER slack -2.604%, 0 faults, 97.8% CTLW reduction | standalone COPPER -0.470%, 29 CTLW misses vs naive 2,411 | Real guest libssl TLS handshake/record execution over memory BIOs with deterministic benchmark RNG; still not a production TCP/TLS server. |
| OpenSSL libssl TLS memory-BIO medium-scale key-policy run | SPP -0.003% ticks | SPP+COPPER slack -0.236%, 0 faults, 97.2% CTLW reduction | standalone COPPER -0.746%, 725 CTLW misses vs naive 58,980 | Doubles sessions/handshakes and uses two TLS records; stronger TLS-library scale point, still not a production TCP/TLS server. |
| OpenSSL libssl TLS socketpair driver | SPP -2.181% ticks | SPP+COPPER slack -2.220%, 0 faults, 98.2% CTLW reduction | standalone COPPER -0.735%, 144 CTLW misses vs naive 16,554 | Real guest libssl TLS handshake/record execution over a Linux AF_UNIX socketpair; stronger than memory BIO, still not a production TCP/TLS server. |
| OpenSSL libssl TCP-harness tagged fallback | SPP -3.117% ticks | SPP+COPPER slack -2.952%, 0 faults, 97.2% CTLW reduction | standalone COPPER -0.719%, 177 CTLW misses vs naive 8,839 | TCP loopback is unavailable in the current guest, so this run explicitly records `transport=af_unix_fallback`; count it as socket-backed libssl evidence, not TCP evidence. |
| OpenSSL libssl TCP-netns loopback driver | SPP -4.719% ticks | SPP+COPPER slack -4.724%, 0 faults, 97.2% CTLW reduction | standalone COPPER -0.444%, 221 CTLW misses vs naive 9,645 | Strict mode creates a private user/network namespace and uses AF_INET TCP loopback with no AF_UNIX fallback; still not a production TCP/TLS server. |
| OpenSSL libssl TCP-netns process-server driver | SPP -9.784% ticks | SPP+COPPER slack -9.884%, 0 faults, 98.2% CTLW reduction | standalone COPPER +0.036%, 111 CTLW misses vs naive 7,185 | Forked TLS server process plus parent TLS client over AF_INET TCP loopback inside private netns; stronger than in-process loopback, still bounded local harness. |
| OpenSSL TCP process-server two-seed stability | two seeds, two checksums | COPPER min CTLW reduction 98.5%, 0 faults | SPP+COPPER slack min CTLW reduction 98.1%, worst gap 0.130 pp | 10 total forked TCP pairs, 0 child failures, all rows `tcp_loopback_netns_process`; still bounded local harness. |
| OpenSSL medium two-seed stability | libssl TLS and libcrypto EVP/HMAC/SHA | COPPER min CTLW reduction: 98.8% TLS, 95.0% libcrypto; 0 faults | SPP+COPPER slack min CTLW reduction: 97.2% TLS, 95.6% libcrypto | Checksums and `rc=0` pass for every key-policy run across both medium seeds. |
| OpenSSL SHA256 libcrypto driver | SPP best of stride/DCPT/SPP/AMPM, -16.598% ticks | SPP+COPPER slack -16.660%, 0 faults, 97.6% CTLW reduction | standalone COPPER -1.916%, 301 CTLW misses vs naive 10,590 | Real guest libcrypto SHA256 execution, but still a small synthetic driver rather than a full crypto benchmark. |
| OpenSSL EVP/HMAC libcrypto driver | SPP best of stride/DCPT/SPP/AMPM, -14.501% ticks | SPP+COPPER slack -14.552%, 0 faults, 95.0% CTLW reduction | standalone COPPER +0.731%, 954 CTLW misses vs naive 16,685 | Real guest libcrypto AES-CTR/HMAC/SHA execution, still a small service driver rather than a full TLS benchmark. |
| OpenSSL EVP/HMAC medium-scale key-policy run | SPP -12.232% ticks | SPP+COPPER slack -12.253%, 0 faults, 96.0% CTLW reduction | standalone COPPER -0.139%, 892 CTLW misses vs naive 17,857 | Doubles sessions/requests and uses two crypto rounds; stronger scale point, still not a broad standard crypto benchmark suite. |
| OpenSSL speed-like fixed-buffer libcrypto driver | SPP -13.213% ticks, first seed | SPP+COPPER slack -13.172%, 0 faults, 93.3% CTLW reduction; 92.7% min over two seeds | standalone COPPER -0.157%, 1,257 CTLW misses vs naive 16,353; 92.3% min CTLW reduction over two seeds | Real guest libcrypto over benchmark-style buffer sizes; closer to `openssl speed`, but not the official CLI benchmark. |
| Official OpenSSL CLI fixed SHA256 digest | SPP -17.786% ticks | SPP+COPPER slack -17.691%, 0 faults, 97.4% CTLW reduction | standalone COPPER -0.019%, 387 CTLW misses vs naive 15,940 | Official Ubuntu ARM64 `openssl dgst -sha256` over deterministic 64 KiB pointer-shaped input; not timer-driven `openssl speed`. |
| Official OpenSSL CLI fixed AES-CTR + digest | SPP -18.515% ticks | SPP+COPPER slack -18.468%, 0 faults, 95.2% CTLW reduction | standalone COPPER -0.138%, 1,463 CTLW misses vs naive 32,174 | Official Ubuntu ARM64 `openssl enc -aes-128-ctr` plus official digest of encrypted output; not timer-driven `openssl speed`. |
| Official OpenSSL CLI fixed HMAC-SHA256 | SPP -17.323% ticks | SPP+COPPER slack -17.335%, 0 faults, 97.4% CTLW reduction | standalone COPPER -0.097%, 524 CTLW misses vs naive 16,903 | Official Ubuntu ARM64 `openssl dgst -sha256 -hmac` over deterministic 64 KiB pointer-shaped input; not timer-driven `openssl speed`. |
| Official OpenSSL CLI three-seed fixed crypto stability | SHA256/AES-CTR/HMAC, 3 seeds each | COPPER min CTLW reduction 95.5%, 0 faults | SPP+COPPER slack min CTLW reduction 95.2%, worst gap 0.294 pp | Nine official-command fixed-workload points; still not timer-driven `openssl speed`. |

## Pros

- Crisp mechanism: committed pointer provenance replaces address-shapedness as DMP authority.
- Directly answers Augury/GoFetch-style data-at-rest activation.
- RCP is more than a block combination because it enforces the invariant recursively.
- CEPF, ROCCA, and CAVI fix three backend/authority-boundary races: stale in-flight source tags cannot recreate proof after source overwrite, same-cycle source clears win over retained CLPD proof writes, and final DMP issue requires both current source proof and current target witness.
- CLPD fixes a measured graph-scan proof-capacity cliff without relaxing the committed-provenance invariant, now has RTL/checker evidence, and reduces full-coverage proof storage by about 30.86-32.00x on the GAPBS-backed graphs under stated assumptions.
- PEB fixes a measured full-system warm-state leakage mode: fake pointer-shaped data that was not architecturally dereferenced drops from 6 warm CLPD-64K issues to 0 while preserving the heap-pointer speedup across three seeds.
- CS-SARI makes the SoC revocation path more than expected plumbing: it adds a candidate-specific conflict predicate with RTL evidence, composition checking, sensitivity evidence, and workload-derived stall-recovery data.
- Measurable with unsafe-prefetch counts, MSHR counts, timing, translation drops, and RTL timing.
- Local evidence now includes Python, graph-style and GAPBS-backed topology traces, expanded GAPBS-style kernel traces and sensitivity sweeps, CS-SARI revocation proxies, CS-SARI composition and sensitivity checks, ROPL replay/exception/alias backend-proof checking plus a synthesized ROPL-LSQ retire guard, ROCCA-to-CLPD proof-write adapter, and CAVI source-plus-target final issue interlock, AMBA-SARI frontdoor RTL, a source-backed security coverage matrix, Vivado directed/randomized RTL checks including full-authority, CTLW witness, CTLW-to-full-authority E2E, CLPD-CTLW authority E2E, SARI/CS-SARI revocation, CLPD, scalable CLPD SRAM, and PEB gates, Vivado RTL vectorless, testbench-SAIF, workload-counter-replay and TCP-process-replay activity power reports, app/service/parser/compression/TCP and TCP process-server metadata-toggle sensitivity bounds, full-authority and CEPF-line end-to-end SVA assertion harnesses, ChampSim, GAPBS, ARM/AArch64 gem5, McPAT sensitivity, and ARM64 full-system Linux boot/readfile plus native AArch64 ROI execution, including official GAPBS, public Olden, heap/fake-pointer PEB controls, standalone SQLite medium/stress seed stability, upstream SQLite speedtest1 JSON/star/ORM evidence, Lua/Duktape medium/stress seed stability, yyjson medium/stress seed stability, two-seed PCRE2 regex matching, public MiBench Patricia trie execution, public libxml2 XML parser/serializer execution, public libarchive TAR parser execution, medium/stress two-seed JSON+SQLite service-composition stability, larger CTLW-terminal runs, small/larger GAPBS-inspired graph-kernel controls, socket-backed, tagged fallback, strict TCP-netns, and a four-point process-separated TCP-netns OpenSSL libssl TLS portfolio, and OpenSSL libssl/libcrypto speed-like full-system drivers.

## Cons

- Integrated COPPER speedup workloads are still controlled/generated or freestanding pointer, graph, C, and GAPBS-inspired mini-suite binaries. Official full-system GAPBS now runs, but it is mostly integer-graph work rather than a natural pointer-prefetch speedup workload.
- Public Olden, the 12-point SQLite/Lua/Duktape/yyjson/JSON+SQLite/cache-service application matrix, the standalone SQLite medium/stress seed-stability artifact, the upstream SQLite speedtest1 JSON/star/ORM components, the Lua/Duktape medium/stress seed-stability artifact, the yyjson medium/stress seed-stability artifact, the two-seed PCRE2 regex point, the public MiBench Patricia trie two-seed 12K comparison plus larger Patricia feasibility notes, the libxml2 XML parser/serializer point, the libarchive TAR parser point, the medium/stress two-seed JSON+SQLite service-composition stability checks, the TLS/session-service stress point, real OpenSSL libssl TLS memory-BIO small/medium two-seed path, the OpenSSL libssl TLS socketpair, tagged fallback, strict TCP-netns, and four-point process-separated TCP-netns portfolio, OpenSSL SHA256 plus small/medium two-seed EVP/HMAC libcrypto drivers, the OpenSSL-speed-like fixed-buffer driver, and the multi-seed official OpenSSL CLI fixed digest/AES/HMAC paths improve the external workload story, but built-in conventional address-correlation prefetchers such as SPP, DCPT, and AMPM remain faster on raw timing. COPPER's claim must stay framed around safe content-derived DMP authority and SCOOP-style coexistence, not universal prefetch performance.
- Production integration still needs a real load-store-queue dependency path; CEPF plus the ROPL checker, ROPL-LSQ retire guard, ROCCA-to-CLPD clear-wins adapter, and CAVI final source-plus-target issue interlock cover proof timing, proof-write, replay/exception/alias/order, target-witness, and revocation hazards in bounded and RTL-interface form, not a whole backend implementation.
- COPPER loses first-use DMP prefetching by design.
- Recursive COPPER adds prefetch traffic; broader workloads may expose pollution or bandwidth costs.
- DRAM energy is now measured from gem5 rank counters, a fixed-architecture McPAT sensitivity pass exists, Vivado reports vectorless, testbench-SAIF, measured workload-counter-replay RTL metadata power, and TCP-process-replay RTL metadata power, and app/service/parser/compression plus TCP process-server metadata-toggle bounds give pJ/access order-of-magnitude accounting; calibrated full-chip/core power still needs instruction-level full-system switching activity, matched ASIC/RTL power, or hardware counters that include COPPER metadata switching.
- Industry could have unpublished DMP safety mechanisms, so the novelty claim must remain public-knowledge scoped.

## Why It May Not Have Been Done Before

DMP security work has mostly focused on attacks, software transformations, or disabling. Irregular prefetching work mostly optimizes performance and tends to trust memory contents as useful prediction signals. COPPER sits between those communities: it keeps the performance target of pointer prefetching but adds a committed-execution authority rule usually associated with architectural correctness and security invariants.

## Reviewer Risk Assessment

| Risk | Severity | Response |
|---|---:|---|
| "This is just taint tracking." | High | COPPER tracks positive DMP dereference authority, not secrecy or general flow. |
| "This is just CHERI/MTE." | Medium | CHERI/MTE protect architectural pointer or allocation safety; COPPER gates microarchitectural DMP action. |
| "The workloads are synthetic." | High | Still partly true, but weaker than before. The ARM64 full-system path now boots Linux and runs official GAPBS, public Olden, standalone SQLite with medium/stress seed stability, Lua/Duktape with medium/stress seed stability, yyjson with medium/stress seed stability, two-seed PCRE2 regex matching, public MiBench Patricia trie execution, libxml2 XML parser/serializer execution, libarchive TAR parser execution, Zstd/zlib compression-decompression, JSON+SQLite composition with medium/stress two-seed stability, cache-service hash/LRU scale points, a crypto-adjacent TLS/session-service stress point, real OpenSSL libssl TLS memory-BIO small/medium two-seed runs, socket-backed, tagged-fallback, strict TCP-netns, and a four-point process-separated TCP-netns OpenSSL libssl TLS portfolio, real OpenSSL SHA256, small/medium two-seed EVP/HMAC libcrypto drivers, an OpenSSL-speed-like fixed-buffer driver, multi-seed official OpenSSL CLI fixed digest, AES, and HMAC workloads, and larger generated AArch64 pointer, heap, fake-pointer, graph-gather, compiled C, and GAPBS-inspired graph-kernel ROIs. Top-tier acceptance still needs broader pointer-rich application workloads such as SPEC-like, database-scale, runtime-scale, production TCP/TLS/official timer-driven standard crypto benchmark, or production-service code. |
| "Conventional prefetchers beat it." | Medium | True and now measured fairly. SPP is best on the 12-point public app/service matrix; SPP+COPPER slack has a -0.004 percentage-point average signed gap and 0.360-point worst absolute gap while adding COPPER's authority filter. Conventional baselines do not provide safe content-derived DMP authority, which is COPPER's contribution. |
| "First-use prefetching is lost." | Medium | True by design; the paper should quantify warmup and explore safe proof seeding. |
| "Commercial cores may already do this secretly." | Medium | Keep the claim to "to the best of public knowledge" and emphasize open reproducible artifacts. |
| "SARI is just a coherence decoder." | Medium | Use CS-SARI as the sharper contribution: candidate-specific DMP authority hazards, RTL no-transient-authority checks, bounded composition evidence, sensitivity sweeps, and measured stall recovery versus global hold. |
| "PEB is just epoch invalidation." | Medium | Do not present PEB alone as novel. The claim is narrower: DMP proof authority is epoch/token-bound, pre-boundary queued prefetches are cancelled safely, and the fake-only/heap/GAPBS experiments show the measurable containment effect. |

## Scores

| Dimension | Score |
|---|---:|
| Novelty risk | 3/10 for the combined public COPPER authority invariant with PASB/CTLW/CLPD/PEB; 5-6/10 if reviewed as broad safe-DMP gating because commercial DDP details and patents are opaque |
| Feasibility | 8/10 |
| Measurability | 9/10 |
| Hardware cost | 7/10 after scalable CLPD SRAM synthesis/route and PEB synthesis; still unproven as a production CPU backend/TLB/CHI integration |
| Paper strength | 8/10 for a focused conference-style draft; about 7/10 for top-tier architecture/security today |
| Publish-worthiness | 8/10 focused venue, 7/10 top-tier today: stronger than workshop-only, but top-tier still needs broader application evidence and a cleaner production integration story |

## Final Verdict

**Focused-conference plausible; top-tier still not guaranteed.** COPPER-CTLW/PASB/RCP/CPTQ/CEPF/CLPD/PEB/CS-SARI now has a named stale-source fix, address-space-bound full-system correction, committed target-line translation witnesses with standalone and consumer-gate RTL evidence, scalable retained-proof hardware evidence, a measured provenance-boundary fix, graph-style and GAPBS-backed topology evidence, expanded GAPBS-style sensitivity evidence, SARI/CS-SARI SoC revocation testing, CS-SARI composition and sensitivity checking, ROPL replay/exception/alias backend-proof checking, ROCCA clear-wins proof-write RTL evidence, CAVI final source-plus-target issue interlock evidence, AArch64 Minor/O3 sensitivity, traffic counters, richer bounded authority checking, and completed ARM64 full-system Linux timing ROIs with pointer, heap, fake-pointer, graph-gather, compiled C, official GAPBS, public MiBench Patricia two-seed 12K comparison plus larger Patricia baseline-feasibility attempts, standalone SQLite medium/stress seed stability, Lua/Duktape medium/stress seed stability, yyjson medium/stress seed stability, medium/stress two-seed JSON+SQLite service composition, and GAPBS-inspired graph-kernel binaries. I still would not call it a guaranteed top-tier PhD conference submission until it has broader pointer-rich application workloads and a production-scale formal/RTL integration story.

## Remaining Evidence Gates

1. Move beyond official GAPBS and generated/freestanding binaries to SPEC-like, database/runtime, language-VM, or crypto-adjacent AArch64 Linux application runs that naturally exercise pointer-rich structures and DMP-relevant leakage surfaces.
2. Extend the local SVA work from the CEPF-line, CTLW witness/full-authority, CLPD-CTLW integration, and SARI/CS-SARI paths to the full production-style hierarchy: real TLB/TLBI/remap fabrics and a real AMBA CHI/ACE/AXI-coherent event decoder.
3. Extend the new proof-ledger/cache/lookahead sweep to MSHR count, memory bandwidth, prefetch queue size, and RCP depth.
4. Extend energy evidence beyond gem5 DRAM counters, fixed McPAT sensitivity, vectorless Vivado RTL power, CLPD testbench SAIF, workload-counter replay SAIF, and metadata-toggle bounds: instruction-level full-system SAIF/VCD, prefetch bytes, L2 pollution, memory commands, NoC pressure, and ASIC-style switching for COPPER metadata tables.
5. Re-run prior-art search before submission, especially patent/code search around DMP safety and data-dependent prefetch disable/provenance.

## Key Local Artifacts

- `research/COPPER_FULL_PAPER.md`
- `research/COPPER_ARTIFACT_REPRODUCTION_GUIDE.md`
- `research/COPPER_ENVIRONMENT_ARTIFACT_MANIFEST_20260619.md`
- `research/results/COPPER_PUBLIC_ARTIFACT_MANIFEST_20260620.md`
- `research/results/copper_public_artifact_manifest_20260620.csv`
- `research/results/copper_public_artifact_manifest_20260620.sha256`
- `research/results/COPPER_PUBLIC_ARTIFACT_PACKAGE_BUILD_20260620.md`
- `research/COPPER_AMBA_CHI_ACE_EVENT_MAP_20260619.md`
- `research/results/COPPER_OOO_REPLAY_EXCEPTION_ALIAS_CONTRACT.md`
- `research/COPPER_CONFERENCE_DRAFT.docx`
- `research/results/COPPER_CONFERENCE_DRAFT_REVIEW.pdf`
- `research/results/copper_review_pdf_render_latest/contact_sheet.png`
- `research/results/copper_full_docx_render_word/COPPER_CONFERENCE_DRAFT.pdf`
- `research/results/copper_full_docx_render_word/contact_sheet.png`
- `research/COPPER_DOCX_QA.md`
- `research/results/COPPER_LATEST_QA_SUMMARY.md`
- `research/results/COPPER_TOP_TIER_GATE_AUDIT_20260617.md`
- `research/results/COPPER_TOP_TIER_GAP_TRACKER_20260619.md`
- `research/results/gem5_arm_ubuntu_fs_pcre2_app/PCRE2_PCRE2_SEED1_FS_SUMMARY.md`
- `research/results/PCRE2_REGEX_SEED_STABILITY_20260620.md`
- `research/results/gem5_arm_ubuntu_fs_libxml2_app/LIBXML2_XML_TINY_FULL_FS_SUMMARY.md`
- `research/results/gem5_arm_ubuntu_fs_libarchive_app/LIBARCHIVE_TAR_TINY_FULL_FS_SUMMARY.md`
- `research/COPPER_PRIOR_ART.md`
- `research/results/COPPER_PRIOR_ART_REFRESH_20260619.md`
- `research/COPPER_FREE_RUN_RESULTS.md`
- `research/results/GEM5_COPPER_SUMMARY.md`
- `research/results/graph_copper/GRAPH_COPPER_SUMMARY.md`
- `research/gapbs_copper_trace_eval.py`
- `research/results/gapbs_copper_trace/GAPBS_COPPER_TRACE_SUMMARY.md`
- `research/results/gapbs_copper_trace/kron_g14.sg`
- `research/gapbs_copper_kernel_trace_eval.py`
- `research/results/gapbs_copper_kernel_trace/GAPBS_COPPER_KERNEL_TRACE_SUMMARY.md`
- `research/gapbs_copper_kernel_sensitivity.py`
- `research/results/gapbs_copper_kernel_sensitivity/GAPBS_COPPER_KERNEL_SENSITIVITY.md`
- `research/copper_clpd_storage_model.py`
- `research/results/gapbs_copper_trace/COPPER_CLPD_STORAGE_MODEL.md`
- `research/results/gem5_arm_ubuntu_fs_nosystemd_probe/FS_PROBE_SUMMARY.md`
- `research/results/gem5_arm_ubuntu_fs_native_workload_roi/FS_NATIVE_WORKLOAD_SUMMARY.md`
- `research/results/gem5_arm_ubuntu_fs_native_pasb_timing/FS_PASB_TIMING_SUMMARY.md`
- `research/results/gem5_arm_ubuntu_fs_large_ctlw/FS_LARGE_CTLW_SUMMARY.md`
- `research/make_aarch64_graph_gather_bench.py`
- `research/bin/aarch64_graph_gather_random`
- `research/results/gem5_arm_ubuntu_fs_graph_gather_random_none`
- `research/results/gem5_arm_ubuntu_fs_graph_gather_random_stride`
- `research/results/gem5_arm_ubuntu_fs_graph_gather_random_naive`
- `research/results/gem5_arm_ubuntu_fs_graph_gather_random_copper`
- `research/aarch64_c_kernel_suite.c`
- `research/bin/aarch64_c_kernel_suite`
- `research/bin/aarch64_c_kernel_suite_fs`
- `research/results/gem5_arm_ubuntu_fs_c_suite/FS_C_SUITE_SUMMARY.md`
- `research/aarch64_gapbs_mini_suite.c`
- `research/results/gem5_arm_ubuntu_fs_gapbs_mini/GAPBS_MINI_SUMMARY.md`
- `research/results/gem5_arm_ubuntu_fs_gapbs_mini_large/GAPBS_MINI_LARGE_FS_SUMMARY.md`
- `research/results/gem5_arm_ubuntu_fs_gapbs_mini/GAPBS_OFFICIAL_AARCH64_FEASIBILITY.md`
- `research/results/COPPER_INVARIANT_MODEL_CHECK.md`
- `research/results/COPPER_AUTHORITY_STATE_SPACE.md`
- `research/copper_full_authority_gate.sv`
- `research/copper_full_authority_gate_tb.sv`
- `research/results/COPPER_FULL_AUTHORITY_RTL_SUMMARY.md`
- `research/copper_full_authority_sva_tb.sv`
- `research/run_copper_full_authority_sva_xsim.ps1`
- `research/results/COPPER_FULL_AUTHORITY_SVA_SUMMARY.md`
- `research/results/copper_full_authority_sva_xsim.log`
- `research/copper_cepf_line_e2e_sva_tb.sv`
- `research/run_copper_cepf_line_e2e_xsim.ps1`
- `research/results/COPPER_CEPF_LINE_E2E_SVA_SUMMARY.md`
- `research/results/copper_cepf_line_e2e_xsim.log`
- `research/copper_ctlw_witness_dir.sv`
- `research/copper_ctlw_witness_dir_tb.sv`
- `research/run_copper_ctlw_witness_xsim.ps1`
- `research/results/COPPER_CTLW_WITNESS_RTL_SUMMARY.md`
- `research/results/copper_ctlw_witness_xsim.log`
- `research/copper_ctlw_full_authority_e2e_tb.sv`
- `research/run_copper_ctlw_full_authority_e2e_xsim.ps1`
- `research/results/COPPER_CTLW_FULL_AUTHORITY_E2E_SUMMARY.md`
- `research/results/copper_ctlw_full_authority_e2e_xsim.log`
- `research/copper_clpd_ctlw_authority_e2e_tb.sv`
- `research/run_copper_clpd_ctlw_authority_e2e_xsim.ps1`
- `research/results/COPPER_CLPD_CTLW_AUTHORITY_E2E_SUMMARY.md`
- `research/results/copper_clpd_ctlw_authority_e2e_xsim.log`
- `research/copper_sari_revoker.sv`
- `research/copper_sari_revoker_tb.sv`
- `research/run_copper_sari_revoker_xsim.ps1`
- `research/results/COPPER_SARI_REVOKER_RTL_SUMMARY.md`
- `research/results/copper_sari_revoker_xsim.log`
- `research/copper_sari_clpd_ctlw_authority_e2e_tb.sv`
- `research/run_copper_sari_clpd_ctlw_authority_e2e_xsim.ps1`
- `research/results/COPPER_SARI_CLPD_CTLW_AUTHORITY_E2E_SUMMARY.md`
- `research/results/copper_sari_clpd_ctlw_authority_e2e_xsim.log`
- `research/copper_sari_scoped_revoker.sv`
- `research/copper_sari_scoped_authority_e2e_tb.sv`
- `research/run_copper_sari_scoped_authority_e2e_xsim.ps1`
- `research/results/COPPER_CS_SARI_AUTHORITY_E2E_SUMMARY.md`
- `research/results/copper_sari_scoped_authority_e2e_xsim.log`
- `research/copper_sari_scoped_trace_sim.py`
- `research/results/sari_scoped_trace/SARI_SCOPED_TRACE_SUMMARY.md`
- `research/copper_cs_sari_gapbs_revocation_eval.py`
- `research/results/cs_sari_gapbs_revocation/CS_SARI_GAPBS_REVOCATION_SUMMARY.md`
- `research/copper_sari_scoped_revoker_v.v`
- `research/copper_cs_sari_composition_state_space.py`
- `research/results/COPPER_CS_SARI_COMPOSITION_STATE_SPACE.md`
- `research/copper_cs_sari_sensitivity_sweep.py`
- `research/results/cs_sari_gapbs_revocation/sensitivity/CS_SARI_SENSITIVITY_SWEEP.md`
- `research/copper_cs_sari_area_proxy.py`
- `research/results/cs_sari_area_proxy/CS_SARI_AREA_PROXY.md`
- `research/results/COPPER_CS_SARI_PRIOR_ART_REVIEW.md`
- `research/results/COPPER_VIVADO_2025_2_TCLSTORE_TRIAGE.md`
- `research/run_copper_authority_regression_xsim.ps1`
- `research/results/COPPER_AUTHORITY_REGRESSION_SUMMARY.md`
- `research/copper_clpd_gate.sv`
- `research/copper_clpd_gate_tb.sv`
- `research/results/COPPER_CLPD_RTL_SUMMARY.md`
- `research/copper_clpd_sram_dir.sv`
- `research/copper_clpd_sram_dir_tb.sv`
- `research/results/COPPER_CLPD_SRAM_DIR_RTL_SUMMARY.md`
- `research/results/COPPER_CLPD_SRAM_SYNTH_SUMMARY.md`
- `research/results/COPPER_CLPD_SRAM_IMPL64K_A200T_SUMMARY.md`
- `research/copper_provenance_epoch_boundary.sv`
- `research/copper_provenance_epoch_boundary_tb.sv`
- `research/results/COPPER_PEB_RTL_SUMMARY.md`
- `research/copper_clpd_state_space.py`
- `research/results/COPPER_CLPD_STATE_SPACE.md`
- `research/copper_security_coverage_matrix.py`
- `research/results/COPPER_SECURITY_COVERAGE_MATRIX.md`
- `research/results/gem5_arm_ubuntu_fs_heap_roi/HEAP_POINTER_ROI_N32768_P16_F4_FS_SUMMARY.md`
- `research/results/gem5_arm_ubuntu_fs_heap_roi/HEAP_POINTER_ROI_N32768_P16_F4_SEED_SWEEP_SUMMARY.md`
- `research/results/gem5_arm_ubuntu_fs_heap_roi/HEAP_POINTER_ROI_N32768_FAKEONLY_F4_SUMMARY.md`
- `research/results/gem5_arm_ubuntu_fs_gapbs_official_suite/GAPBS_OFFICIAL_SUITE6_G10_FS_SUMMARY.md`
- `research/analyze_copper_mcpat_sensitivity.py`
- `research/results/COPPER_MCPAT_SENSITIVITY_20260618.md`
- `research/results/copper_mcpat_sensitivity_20260618.csv`
- `research/results/mcpat_copper_sensitivity_20260618/`
- `research/run_copper_rtl_power_proxy.tcl`
- `research/summarize_copper_rtl_power_proxy.py`
- `research/results/COPPER_RTL_POWER_PROXY_20260618.md`
- `research/results/copper_rtl_power_proxy_20260618.csv`
- `research/results/copper_rtl_power_proxy_manifest_20260618.csv`
- `research/summarize_copper_clpd_activity_power.py`
- `research/results/COPPER_CLPD_ACTIVITY_POWER_20260619.md`
- `research/results/copper_clpd_sram_dir_activity.saif`
- `research/results/copper_clpd_sram_dir_activity_saif_power.rpt`
- `research/build_copper_workload_clpd_replay.py`
- `research/copper_clpd_sram_workload_activity_tb.sv`
- `research/summarize_copper_workload_clpd_activity_power.py`
- `research/results/COPPER_WORKLOAD_CLPD_ACTIVITY_POWER_20260619.md`
- `research/results/copper_clpd_sram_workload_activity.saif`
- `research/results/copper_clpd_sram_workload_activity_saif_power.rpt`
- `research/build_copper_tcp_process_clpd_replay.py`
- `research/run_copper_clpd_sram_tcp_process_activity_xsim.ps1`
- `research/run_copper_clpd_sram_tcp_process_saif_power.tcl`
- `research/summarize_copper_tcp_process_clpd_activity_power.py`
- `research/results/COPPER_TCP_PROCESS_CLPD_ACTIVITY_POWER_20260620.md`
- `research/results/copper_clpd_sram_tcp_process_activity.saif`
- `research/results/copper_clpd_sram_tcp_process_activity_saif_power.rpt`
- `research/analyze_copper_metadata_toggle_bound.py`
- `research/results/COPPER_METADATA_TOGGLE_BOUND_20260619.md`
- `research/results/copper_metadata_toggle_bound_20260619.csv`
- `research/analyze_openssl_tcp_process_metadata_toggle_bound.py`
- `research/results/OPENSSL_TCP_PROCESS_METADATA_TOGGLE_BOUND_20260620.md`
- `research/results/openssl_tcp_process_metadata_toggle_bound_20260620.csv`
- `research/results/gem5_copper_summary.csv`
- `research/results/gem5_arm_ubuntu_fs_ossltlsbio_app/OSSLTLSBIO_APP_MEDIUM_FS_SUMMARY.md`
- `research/results/gem5_arm_ubuntu_fs_ossltlssocket_app/OSSLTLSSOCKET_SOCKET_SMOKE_FS_SUMMARY.md`
- `research/results/gem5_arm_ubuntu_fs_osslcrypto_app/OSSLCRYPTO_APP_MEDIUM_FS_SUMMARY.md`
- `research/results/gem5_arm_ubuntu_fs_osslspeed_app/OSSLSPEED_APP_SMOKE_FS_SUMMARY.md`
- `research/results/OPENSSL_SPEEDLIKE_SEED_STABILITY_20260619.md`
- `research/results/OPENSSL_CLI_FEASIBILITY_20260619.md`
- `research/results/OPENSSL_CLI_TLS_PAIR_FEASIBILITY_20260620.md`
- `research/openssl_guest_probe.sh`
- `research/openssl_cli_tls_pair_guest.sh`
- `research/results/gem5_arm_ubuntu_fs_osslcli_app/OSSLCLI_FIXED_64K_FS_SUMMARY.md`
- `research/results/gem5_arm_ubuntu_fs_osslcli_app/OSSLCLI_AESCTR_64K_FS_SUMMARY.md`
- `research/results/gem5_arm_ubuntu_fs_osslcli_app/OSSLCLI_HMAC_64K_FS_SUMMARY.md`
- `research/results/gem5_arm_ubuntu_fs_osslcli_app/OSSLCLI_FIXED_64K_SEED2_FS_SUMMARY.md`
- `research/results/gem5_arm_ubuntu_fs_osslcli_app/OSSLCLI_AESCTR_64K_SEED2_FS_SUMMARY.md`
- `research/results/gem5_arm_ubuntu_fs_osslcli_app/OSSLCLI_HMAC_64K_SEED2_FS_SUMMARY.md`
- `research/results/OPENSSL_CLI_SEED_STABILITY_20260619.md`
- `research/results/OPENSSL_MEDIUM_SEED_STABILITY_20260619.md`
- `research/run_openssl_cli_fixed_fs.ps1`
- `research/results/GEM5_POWERSHELL_RUNNER_FIX_20260619.md`
- `research/summarize_sqlite_seed_stability.py`
- `research/results/SQLITE_MEDIUM_STRESS_SEED_STABILITY_20260619.md`
- `research/build_sqlite_speedtest1_aarch64.py`
- `research/run_sqlite_speedtest1_fs.sh`
- `research/summarize_sqlite_speedtest1_fs.py`
- `research/summarize_sqlite_speedtest1_components.py`
- `research/results/gem5_arm_ubuntu_fs_sqlite_speedtest1/SQLITE_SPEEDTEST1_SPEEDTEST1_JSON_SMOKE_SIZE1_FS_SUMMARY.md`
- `research/results/gem5_arm_ubuntu_fs_sqlite_speedtest1/SQLITE_SPEEDTEST1_SPEEDTEST1_STAR_SMOKE_SIZE1_FS_SUMMARY.md`
- `research/results/gem5_arm_ubuntu_fs_sqlite_speedtest1/SQLITE_SPEEDTEST1_SPEEDTEST1_ORM_SMOKE_SIZE1_FS_SUMMARY.md`
- `research/results/SQLITE_SPEEDTEST1_COMPONENTS_20260619.md`
- `research/aarch64_mibench_patricia_workload.c`
- `research/build_mibench_patricia_workload_aarch64.py`
- `research/run_mibench_patricia_fs.sh`
- `research/summarize_mibench_patricia_fs.py`
- `research/results/mibench_patricia_workload_build/MIBENCH_PATRICIA_WORKLOAD_BUILD.md`
- `research/results/gem5_arm_ubuntu_fs_mibench_patricia_app/MIBENCH_PATRICIA_PATRICIA_PREPROBE_FS_SUMMARY.md`
- `research/results/gem5_arm_ubuntu_fs_mibench_patricia_app/MIBENCH_PATRICIA_PATRICIA_SMALL2048_FS_SUMMARY.md`
- `research/results/gem5_arm_ubuntu_fs_mibench_patricia_app/MIBENCH_PATRICIA_PATRICIA_SMALL8192_FS_SUMMARY.md`
- `research/results/gem5_arm_ubuntu_fs_mibench_patricia_app/MIBENCH_PATRICIA_PATRICIA_LARGE12288_FS_SUMMARY.md`
- `research/results/gem5_arm_ubuntu_fs_mibench_patricia_app/MIBENCH_PATRICIA_PATRICIA_LARGE12288_SEED1_FS_SUMMARY.md`
- `research/results/MIBENCH_PATRICIA_SCALE_PORTFOLIO_20260620.md`
- `research/results/MIBENCH_PATRICIA_12K_SEED_STABILITY_20260621.md`
- `research/results/MIBENCH_PATRICIA_LARGE16384_FEASIBILITY_20260620.md`
- `research/results/MIBENCH_PATRICIA_LARGE32768_FEASIBILITY_20260620.md`
- `research/results/MIBENCH_PATRICIA_LARGE62721_FEASIBILITY_20260620.md`
- `research/summarize_lua_duktape_seed_stability.py`
- `research/results/LUA_DUKTAPE_MEDIUM_STRESS_SEED_STABILITY_20260619.md`
- `research/summarize_yyjson_seed_stability.py`
- `research/results/YYJSON_MEDIUM_STRESS_SEED_STABILITY_20260619.md`
- `research/results/gem5_arm_ubuntu_fs_jsonsqlite_app/JSONSQLITE_MEDIUM_SEED1_FS_SUMMARY.md`
- `research/results/JSONSQLITE_MEDIUM_SEED_STABILITY_20260619.md`
- `research/results/gem5_arm_ubuntu_fs_jsonsqlite_app/JSONSQLITE_STRESS_SEED1_FS_SUMMARY.md`
- `research/results/JSONSQLITE_STRESS_SEED_STABILITY_20260619.md`
- `research/copper_commit_epoch_proof_bridge.sv`
- `research/copper_ropl_lsq_retire_guard.sv`
- `research/results/COPPER_ROPL_LSQ_RETIRE_GUARD_RTL_SUMMARY.md`
- `research/copper_rocca_clpd_commit_adapter.sv`
- `research/copper_rocca_clpd_commit_adapter_tb.sv`
- `research/results/COPPER_ROCCA_CLPD_COMMIT_ADAPTER_RTL_SUMMARY.md`
- `research/copper_cavi_authority_issue_gate.sv`
- `research/copper_cavi_authority_issue_gate_tb.sv`
- `research/results/COPPER_CAVI_AUTHORITY_ISSUE_GATE_RTL_SUMMARY.md`
- `external/gem5/src/mem/cache/prefetch/copper.cc`
- `external/gem5/src/mem/cache/prefetch/copper.hh`

## Public Sources Used

- Augury: https://www.prefetchers.info/augury.pdf
- GoFetch: https://gofetch.fail/
- SplittingSecrets: https://arxiv.org/abs/2601.12270
- PreFence: https://arxiv.org/abs/2410.00452
- ICP: https://arxiv.org/abs/2605.15645
- Improved Prefetching Techniques for Linked Data Structures: https://arxiv.org/abs/2505.21669
- Okapi: https://arxiv.org/abs/2312.08156
- Intel Data-Dependent Prefetcher guidance: https://www.intel.com/content/www/us/en/developer/articles/technical/software-security-guidance/technical-documentation/data-dependent-prefetcher.html
- SQLite 3.53.2 release log: https://sqlite.org/releaselog/3_53_2.html
- SQLite source downloads: https://sqlite.org/download.html
- MiBench network benchmark archive: https://vhosts.eecs.umich.edu/mibench/network.tar.gz
- SITE self-invalidating TLB entries: https://www.csa.iisc.ac.in/~arkapravab/papers/pact2017_final_version.pdf
- ecoTLB shootdown optimization: https://www.cs.yale.edu/homes/abhishek/kumar-taco20.pdf


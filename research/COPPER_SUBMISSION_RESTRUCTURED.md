# COPPER: Committed Pointer-Provenance as Authority for Safe Data-Memory-Dependent Prefetching

Status: restructured submission draft derived from `COPPER_FULL_PAPER.md` and the refreshed 2026-06-23 audit.

## Abstract

Data-memory-dependent prefetchers (DMPs) can accelerate pointer-rich workloads by treating loaded data values as future memory addresses. Recent attacks such as Augury and GoFetch show why that optimization is dangerous: data that merely resembles a pointer can create secret-dependent cache activity even when software never uses it as an architectural address. This paper proposes COPPER, a DMP authority mechanism that permits content-derived dereference only when committed execution has already proven the exact source word as a pointer source, the proof remains clean, the address-space/protection context matches, and recursive cross-page targets have committed target-line witnesses.

COPPER is not a claim that metadata, taint, or pointer prefetching are new. The contribution is the authority rule for DMP issue and its recursive consequences: address-shapedness is insufficient, prefetched data is terminal until demand-validated, and stale or cross-domain proof is destroyed before it can authorize another dereference. We implement this rule with a compressed line-provenance directory, commit-epoch proof filtering, address-space binding, committed target-line witnessing, and a slack-only companion mode, SCOOP, that coexists with a conventional primary prefetcher.

Across adversarial traces, AArch64/Linux full-system workloads, public library/application suites, bounded checkers, and Vivado RTL, COPPER blocks modeled unsafe DMP dereferences while retaining useful pointer-prefetch opportunities. The strongest performance claim is coexistence rather than universal speedup: on the 12-point public app/service matrix, SPP is the best conventional baseline on all points, while SPP+COPPER slack stays within 0.360 percentage points worst-case and preserves COPPER's authority checks. A 22-point side-effect scorecard reports standalone COPPER's base-weighted pressure score at 0.879% versus 1.083% for naive DMP, with 18.1%-20.6% lower proxy-pollution results across checked weightings. The artifact package passes 177/177 local checks.

## 1. Introduction

Modern processors use prefetching to hide memory latency. Conventional prefetchers infer future misses from the address stream: stride, delta, temporal, or instruction-correlated patterns. DMPs go further: they inspect memory contents and use pointer-looking values as future addresses. This is attractive for linked data structures, graph traversal, hash tables, and pointer arrays because the useful address is often stored in memory before it appears in the architectural address stream.

The same behavior breaks a key assumption used by constant-time software. Constant-time code avoids secret-dependent branches and architectural memory addresses, but a DMP may act on secret-dependent data anyway. Augury showed data-at-rest leakage through pointer-looking values, and GoFetch showed practical cryptographic key extraction from DMP activation. A coarse defense is to disable the DMP in sensitive regions; a software defense is to transform secrets so they do not look like addresses. Those mitigations are useful, but they leave open an architectural question:

Can a DMP keep useful pointer prefetching while denying authority to arbitrary data?

COPPER answers yes by changing the issue authority. A DMP may dereference a memory-derived value only when the processor has already committed architectural evidence that the exact source word is a pointer source, and when no subsequent event has invalidated that evidence. This shifts the DMP from "looks like an address" to "has committed pointer provenance."

This paper makes five contributions:

1. It defines a narrow DMP authority invariant: committed pointer provenance, clean-since-proof lifecycle, address-space/protection binding, and committed target-line witnesses for recursive cross-page issue.
2. It gives a concrete mechanism: CLPD for compressed line provenance, CEPF for commit-epoch proof filtering, PASB for address-space binding, CTLW for target-line witnesses, PEB for epoch boundary containment, and RCP for recursive carried provenance.
3. It adds SCOOP, a slack-only companion mode in which COPPER runs beside a conventional primary prefetcher and issues only when the primary lane has no request.
4. It extends the mechanism to SoC revocation with CS-SARI, a candidate-specific refinement of global SARI hold for DMA/remap/TLBI-like events.
5. It evaluates the claim across adversarial trace models, graph-derived traces, AArch64/Linux full-system workloads, public library/application suites, bounded state-space checkers, and Vivado RTL.

The claim is intentionally bounded. COPPER is a safety authority for content-derived DMP issue. It is not a universal replacement for the fastest address-stream prefetcher, not an ASIC signoff result, and not a production-service benchmark campaign.

## 2. Background and Threat Model

### 2.1 Data-Memory-Dependent Prefetching

A DMP observes loaded memory values and predicts that some values are addresses worth prefetching. If a program loads a pointer from a list node and later dereferences it, a DMP can hide latency by prefetching the target early. This is different from stride or delta prefetching because the prediction source is data, not only the stream of committed addresses.

DMPs create three authority problems:

- Data-at-rest problem: a memory word can look like an address even when software never uses it as one.
- Recursive problem: a prefetched line can contain more pointer-looking data, allowing the DMP to walk through memory without architectural demand evidence.
- Context problem: a value that is valid in one protection domain, address space, translation epoch, or permission state may be invalid or unsafe in another.

### 2.2 Attacker and Observation Model

The attacker can arrange or influence data values that are loaded by victim code and can observe timing or cache effects caused by DMP traffic. The attacker does not need the victim to architecturally dereference the secret-dependent value. The relevant leakage is microarchitectural: prefetches, fills, cache pollution, and translation attempts that depend on data values.

The defense goal is to prevent DMP issue from data that lacks committed pointer provenance under the correct address-space/protection context. The goal is not to hide all legal demand accesses, prove a full processor noninterference theorem, or replace software constant-time discipline.

### 2.3 What Counts as Authority

COPPER treats a source word as authorized only after committed execution has used that exact word as a pointer source. Authority is destroyed or blocked by writes, fills that overwrite the source, invalidations, proof-epoch transitions, address-space mismatch, permission or translation failure, source revocation, target remap, token TLBI, global TLBI, and target-witness invalidation.

This makes proof lifecycle part of the DMP contract. A proof is not merely a cache hint. It is the condition under which a content-derived hardware agent may perform another memory access.

## 3. Mechanism

### 3.1 Core Rule

The COPPER issue rule is:

```text
allow_dmp_issue =
    committed_source_proof(source_word)
    && source_clean_since_proof(source_word)
    && address_space_token_matches(source_word, request)
    && translation_and_permission_allow(request)
    && target_witness_valid_for_recursive_cross_page_issue(request)
```

The rule has two important consequences. First, address-shaped data is not enough. Second, recursive prefetching must carry authority from committed architectural evidence, not from prior speculative DMP traffic.

### 3.2 Proof Creation and Destruction

Proof creation occurs at commit, not execute. This avoids granting authority to instructions that later squash, fault, replay, or lose ordering against a source overwrite. The Commit-Epoch Provenance Filter (CEPF) protects the backend boundary by rejecting stale in-flight source tags after a source-word overwrite or epoch transition.

Proof destruction is conservative. Writes, source invalidations, fills that replace a proven word, proof-epoch boundaries, address-space changes, and relevant translation/protection events clear or block authority. A line-resident implementation can clear on eviction; the compressed ledger variant can retain clean line proofs across replacement but still respects source lifecycle and epoch rules.

### 3.3 Compressed Line-Provenance Directory

The Compressed Line-Provenance Directory (CLPD) stores per-line proof state instead of exact per-edge proof for every source word. This compresses metadata while retaining the authority rule at the granularity needed by the DMP gate. On GAPBS-backed graph traces, CLPD gives about 30.86x-32.00x full-coverage proof-storage reduction. On the g12 edge-scan capacity point, 8192 CLPD entries cost 54 KiB and recover 2.115x speedup; the edge-exact ledger needs 131072 entries and 1696 KiB to reach 2.369x.

### 3.4 Recursive Carried Provenance and Target Witnesses

Recursive Carried-Provenance (RCP) lets prefetched pointer lines seed later DMP requests only when the source word already has committed provenance. A Committed Page-Translation Queue (CPTQ) extends this across pages after valid process translation. Provenance Address-Space Binding (PASB) keys proof by an address-space/protection token, preventing proof reuse across domains.

Committed Target-Line Witnessing (CTLW) closes the cross-page recursive target problem. A target line may authorize recursive target formation only after committed execution has witnessed the exact virtual-to-physical line. Witness-derived fills are terminal until demand-validated. This prevents a DMP from using one speculative content-derived fill as authority to walk into another page.

### 3.5 Provenance Epoch Boundary

The Provenance Epoch Boundary (PEB) is a containment mechanism for phase changes, domain boundaries, and fake-only warm-state leakage. It drops stale authority entries at epoch boundaries and blocks wrap cases in RTL. PEB is not novel because it uses an epoch; its role is narrower: binding DMP proof authority to a measured containment boundary.

### 3.6 SCOOP Companion Mode

SCOOP runs COPPER as a slack-only companion beside a conventional primary prefetcher such as SPP. The primary has strict issue priority. COPPER issues only in slack cycles and only after passing the full authority rule. This separates two claims:

- Use the conventional primary for raw address-stream performance.
- Use COPPER/SCOOP for safe content-derived pointer authority.

### 3.7 CS-SARI for SoC Revocation

Global SARI-style hold is safe but coarse: revocation activity can stop all DMP issue. CS-SARI scopes revocation evidence to the candidate source, queued source line, target witness, token, and global invalidation state. The goal is to retain the safety of revocation hold while avoiding unnecessary stalls for unrelated candidates.

The refreshed sensitivity artifact makes the prior source/target independence assumption explicit by adding a sampled source-target correlation sweep over `rho=0.00..1.00`.

## 4. Security Argument

The security argument is an invariant over DMP issue:

If a content-derived DMP request issues, then the source word has committed pointer provenance in the current authority domain, the source has not been invalidated since proof, and any recursive cross-page target has an exact committed target-line witness.

For data-at-rest attacks, arbitrary pointer-looking words are blocked because they lack committed source proof. For recursive attacks, prefetched data is terminal unless demand execution later proves it. For stale-source attacks, writes, fills, invalidations, and epoch boundaries clear or block proof. For address-space and permission attacks, PASB plus translation/permission gating prevent cross-domain reuse. For target-remap and TLBI hazards, CTLW and CS-SARI revoke or hold the candidate.

The bounded checkers support the argument by finding counterexamples for weakened variants: execute-stage proof, unretired-source proof, missed source revocation, missed target revocation, missing PASB, page-level witnesses, missed TLBI/remap clearing, and missed permission gates. They do not constitute a full production processor proof, but they exercise the exact failure modes that shaped the mechanism.

## 5. Implementation

The prototype includes trace models, gem5 prefetcher integration, AArch64/Linux full-system workloads, and SystemVerilog RTL components. The hardware-facing blocks include:

- CLPD gate and scalable CLPD SRAM directory.
- CEPF proof bridge.
- PEB epoch/token block.
- CTLW witness directory.
- ROPL-LSQ retire guard and ROCCA clear-wins proof-write adapter.
- CAVI final source-plus-target issue interlock.
- AMBA/SARI frontdoor and CS-SARI revocation logic.
- TLB/coherence authority filter.
- SCOOP companion arbiter.

The RTL evidence is intentionally described as representative integration evidence, not production ARM signoff. Vivado/XSim checks cover directed and randomized cases, synthesis timing, and SAIF/vectorless power-proxy runs.

## 6. Evaluation Methodology

The evaluation asks four questions:

1. Safety: Does COPPER block modeled unsafe content-derived DMP issue?
2. Performance: How much useful pointer-prefetch opportunity remains?
3. Coexistence: Can COPPER coexist with strong conventional address-stream prefetchers?
4. Side effects and feasibility: What are the traffic, energy-proxy, metadata, and RTL costs?

The evidence stack is deliberately layered:

- Adversarial trace oracles isolate data-at-rest, recursive, cross-domain, and stale-source hazards.
- Graph-derived traces stress pointer-like CSR/GAPBS locality and metadata capacity.
- AArch64/Linux full-system workloads test native binaries under gem5 timing mode.
- Public application/library suites broaden workload coverage.
- Side-effect scorecards use gem5 counters, DRAM energy counters, McPAT sensitivity, metadata-toggle bounds, and RTL power proxies.
- Bounded checkers and RTL testbenches validate authority composition.

The audit-refresh updates are folded into the methodology. The pressure score is reported as a base proxy plus weight sensitivity, not calibrated power. Synthetic cross-domain leakage is reported as a mix sweep, not a hidden default. CS-SARI reports a sampled correlation addendum, not just independent source/target revocation streams.

## 7. Results

### 7.1 Security Oracles and Trace Models

On a mixed benign/adversarial trace, naive DMP reaches 3.628x speedup but performs 2048 data-at-rest prefetches, 1076 cross-domain prefetches, and 2616 unproven-line prefetches. COPPER-LINE reaches 2.414x speedup while eliminating modeled unsafe dereferences.

The refreshed cross-domain sensitivity makes this count conditional on workload mix. With `cross_domain_secret_rate` swept from 0.00 to 1.00, naive cross-domain prefetches move from 0.0 to 2048.0, while COPPER-LINE remains at 0.0 in the modeled trace.

The secret-traffic oracle shows unsafe DMP emits 32,760 extra prefetches when a secret bit changes data words from high-bit junk to heap addresses. COPPER and SCOOP reduce the unauthorized scan-phase allowed-candidate delta to zero. A split scan/probe audit shows unsafe DMP leaks before the observer probe, while COPPER/SCOOP block the scan-phase candidates.

### 7.2 Graph and Metadata Capacity

A ten-seed CSR-like graph trace gives COPPER-epoch 3.276x speedup while blocking data-at-rest and stale rewritten-edge prefetches. A GAPBS-backed topology trace over five generated Kronecker graphs gives COPPER-epoch and CLPD 1.770x and 1.896x speedup, respectively, with zero data-at-rest, unproven-edge, or stale-slot prefetches.

An expanded GAPBS-style kernel sensitivity sweep over 4320 graph/kernel/table/cache/lookahead runs preserves zero COPPER unsafe modeled prefetches. Naive DMP produces 81,605,320 unsafe modeled prefetches, and source-only provenance still produces 284,488.

### 7.3 Full-System Pointer and Graph Workloads

In gem5 pointer-chain workloads, recursive COPPER improves ARM32 page-permuted lists by 6.76%-6.78% and random lists by 5.59%-5.66%; direct AArch64 syscall-emulation binaries show 6.77% and 5.61%. AArch64 Minor and O3 CPU-model sensitivity remains positive at 2.64%-2.79% and 2.68%-2.77%.

The ARM64 full-system path boots Ubuntu/Linux 6.8.12, switches from atomic boot to timing CPU, and attaches COPPER inside the L1D hierarchy. PASB and CTLW-terminal remove recursive translation faults in generated pointer ROIs. A heap-pointer ROI with 32768 heap nodes and three layout seeds gives CLPD-64K mean -2.866% ROI ticks versus no prefetch; adding PEB blocks 131,066/131,066 fake pointer-shaped observations, issues zero prefetches in the fake-only ROI, and keeps the pointer traversal at mean -2.905%.

Official AArch64 GAPBS BFS/CC/PR/SSSP/BC/TC at g10 runs with `rc=0`, +0.015% aggregate timing versus no prefetch, zero translation faults, zero proof evictions, and 340,128 pre-boundary authority entries dropped. These kernels are not pointer-heavy, but they provide clean full-system execution and boundary evidence.

### 7.4 Public Applications and Conventional Baselines

The public workload refresh adds SQLite, Lua, Duktape, yyjson, JSON+SQLite, cache-service, Olden, MiBench Patricia, PCRE2, libxml2, libarchive, Zstd, zlib, OpenSSL libssl, OpenSSL libcrypto, OpenSSL-speed-like fixed-buffer drivers, and official OpenSSL CLI fixed workloads.

The conventional-baseline result is the most important claim boundary. On the 12-point SQLite/Lua/Duktape/yyjson plus JSON+SQLite and cache-service app matrix:

| Result | Value |
|---|---:|
| Best conventional policy count | SPP on 12/12 |
| SPP mean timing versus no prefetch | -13.112% |
| SPP+COPPER slack mean timing versus no prefetch | -13.116% |
| Average signed slack gap versus SPP | -0.004 pp |
| Worst absolute slack gap versus SPP | 0.360 pp |
| SPP+COPPER CTLW reduction versus naive DMP | 94.0% |
| COPPER/slack translation faults | 0 |

Thus the honest performance statement is not that COPPER beats every prefetcher. It does not. The stronger statement is that SCOOP preserves SPP-class timing while adding COPPER's content-derived authority gate.

Across a 15-point repeated SQLite/Lua/Duktape seed portfolio, standalone COPPER beats unsafe naive DMP on 9/15 points, cuts aggregate naive CTLW misses by 90.706%, and SPP+COPPER slack stays within 0.760 percentage points of SPP while cutting CTLW misses by 91.505%.

### 7.5 Side Effects, Energy Proxies, and Claim Conditioning

The 22-point gem5-counter side-effect scorecard separates speed from traffic and pollution. Under the transparent base pressure weights:

| Policy | Mean runtime delta | Mean pressure score | Mean bus delta | Mean DRAM-read delta | CTLW misses |
|---|---:|---:|---:|---:|---:|
| naive DMP | -0.304% | 1.083% | 0.530% | 0.782% | 327,629 |
| COPPER CLPD-64K+PEB | -0.321% | 0.879% | 0.441% | 0.651% | 20,046 |

Standalone COPPER's base pressure score is 18.8% lower than naive DMP. Across six transparent weight scenarios, the lower proxy-pollution result ranges from 18.1% to 20.6%, and COPPER is lower-or-equal on 20/22 points under every checked weighting. This remains a proxy over gem5 counters, not calibrated silicon power.

The DRAM-energy scorecard covers 26 full-system points. Standalone COPPER has mean total DRAM-energy delta -0.232% and operation-energy delta +0.598% versus no prefetch, slightly better than naive DMP at -0.212% and +0.712%. COPPER has lower-or-equal total DRAM energy than naive on 13/26 points and lower-or-equal DRAM operation energy on 19/26. SPP+COPPER slack remains close to SPP, with total DRAM-energy gap averaging +0.071% and DRAM operation-energy gap averaging +0.203%.

McPAT sensitivity, metadata-toggle pJ/access bounds, and RTL power-proxy replays add sanity checks but do not replace calibrated ASIC power.

### 7.6 CS-SARI Revocation

The wired SARI-to-CLPD/CTLW/full-authority RTL harness passes 12 directed plus 10,000 randomized XSim samples with `conflict_hold=1245`, `avoided_global_hold=1007`, and `errors=0`.

The GAPBS-topology revocation proxy reports 82.06% aggregate hold reduction versus global SARI, 269,879 authorized candidate opportunities recovered, zero CS-SARI modeled unsafe issues, and 59,013 unsafe issues for a no-hold policy. A 20-configuration queue-depth/conflict sweep keeps CS-SARI unsafe issues at zero while the no-hold control produces 1,649,883 unsafe modeled issues and the median scoped-hold reduction is 72.06%.

The sampled source/target-correlation addendum uses the largest two GAPBS topologies (`kron_g13`, `kron_g14`) with two passes per run and `rho=0.00..1.00`. It reports zero scoped unsafe modeled issues, 15,481 no-hold unsafe modeled issues, and 83.57%-84.04% hold reduction. In this balanced profile, added target events mostly overlap candidates already held by source conflicts, so precision does not collapse. This is still a modeled revocation proxy, not full CHI/DMA event capture.

### 7.7 RTL and Hardware Feasibility

The CLPD SRAM directory passes 18 directed plus 4000 randomized XSim tests. The 64K-entry configuration used by gem5 synthesizes on `xc7a200tfbg676-2` with 629 LUTs, 156 FFs, 260 BRAM tiles, and WNS 3.274 ns at 10 ns, then routes out-of-context with WNS 0.362 ns.

PEB synthesizes on Artix-7 with 346 LUTs, 147 FFs, no BRAM/DSP, and WNS 3.782 ns. The TLB/coherence issue filter passes 27 directed plus 10,000 randomized XSim checks and synthesizes with 332 LUTs, 167 FFs, no BRAM/DSP, and WNS +6.898 ns at 10 ns.

The RTL power-proxy pass includes vectorless and SAIF-driven reports. A workload-derived replay maps measured COPPER events into a 120,000-operation CLPD RTL replay; XSim completes with `errors=0`, and Vivado maps its SAIF into a routed 1K-entry CLPD with 0.083 W total, 0.014 W dynamic, medium confidence, and WNS 1.807 ns. These are plausibility datapoints, not ASIC-calibrated power.

## 8. Discussion

### 8.1 What COPPER Should Claim

COPPER should claim safe authority for content-derived DMP issue. SCOOP should claim coexistence with strong address-stream prefetchers. The paper should not claim that standalone COPPER is the fastest prefetcher or that proxy power results are silicon measurements.

The clean reviewer-facing statement is:

> COPPER converts DMP issue from an address-shapedness heuristic into a committed pointer-provenance authority rule. SCOOP lets that authority rule coexist with a conventional primary prefetcher.

### 8.2 Why the Mechanism Is Not Just a Combination

The novelty is not metadata, epochs, TLB checks, or prefetch arbitration by themselves. The novelty is the composition boundary: a DMP may act on memory contents only when committed execution has proven the exact source word as a pointer source and when source, domain, target, and revocation authority still hold. Removing any part reintroduces a concrete failure mode exercised by the checkers.

### 8.3 Limitations

The current evidence has important limits:

- The evaluation is not SPEC, production database/server software, or a production TCP/TLS deployment.
- The full-system path is gem5 timing-mode ARM64 Linux, not silicon.
- The RTL is representative and bounded, not production OoO/SoC signoff.
- McPAT, metadata-toggle, gem5 DRAM energy, and Vivado power reports are proxies, not calibrated ASIC power.
- CS-SARI uses revocation proxies and bounded checks, not full coherent interconnect traces.
- The threat model covers DMP issue authority, not all forms of speculative side channel.

These limits should stay visible in the paper because they make the core claim more credible.

## 9. Related Work

Augury and GoFetch motivate the threat by showing that DMP activation can leak data at rest or break constant-time cryptographic assumptions. SplittingSecrets, PreFence, and PhantomFetch explore software/compiler/scheduling defenses. Conventional prefetching work such as ICP, DX100, pointer-chase prefetchers, and linked-data prefetching establishes the performance motivation but does not provide committed pointer-provenance authority for content-derived issue.

Speculation and metadata-safety work such as SafeSpec, BliMe, HardTaint, CHERI/PICASSO-style capability work, MTE studies, and sandboxing designs such as Okapi provide adjacent ideas: containment, metadata, taint, capability checks, or leakage-free speculation. COPPER's narrower contribution is to put a committed provenance authority rule directly on DMP dereference and recursive content-derived prefetching.

TLB and coherence work such as self-invalidating TLBs and eventually consistent TLBs informs the revocation setting, but COPPER/CS-SARI is focused on whether a DMP candidate may issue under source, target, token, remap, and permission authority.

## 10. Artifact Structure

The evidence-heavy full record remains in `research/COPPER_FULL_PAPER.md`, `research/COPPER_FINAL_OUTPUT.md`, `research/results/`, and `AUDIT.md`. This restructured draft is intended to be the submission-facing narrative.

Key source-backed artifacts include:

| Artifact | Purpose |
|---|---|
| `research/results/COPPER_RESULTS.md` | Synthetic, adversarial, cross-domain, value-table, and cache-sweep trace results |
| `research/results/COPPER_APP_BASELINE_MATRIX_20260617.md` | Fair conventional prefetcher matrix |
| `research/results/COPPER_ENERGY_POLLUTION_SCORECARD_20260617.md` | 22-point side-effect scorecard and weight sensitivity |
| `research/results/COPPER_DRAM_ENERGY_SCORECARD_20260618.md` | 26-point DRAM-energy scorecard |
| `research/results/cs_sari_gapbs_revocation/sensitivity/CS_SARI_SENSITIVITY_SWEEP.md` | CS-SARI queue/profile and correlation sensitivity |
| `research/results/COPPER_CLAIM_EVIDENCE_MATRIX_20260617.md` | Claim-to-evidence gate |
| `research/results/COPPER_ARTIFACT_AUDIT_20260616.md` | 177/177 local artifact verification |

## 11. Conclusion

Data-memory-dependent prefetching is useful precisely because it treats loaded data as future addresses. That same behavior is unsafe when arbitrary data can authorize cache activity. COPPER changes the authority model: a DMP may dereference a memory-derived value only after committed execution proves the source word as a pointer source and only while source, domain, target, and revocation authority remain valid.

The evaluation supports a bounded but meaningful claim. COPPER blocks modeled unsafe content-derived issue across adversarial traces, graph-derived traces, full-system AArch64 workloads, checkers, and RTL tests. SCOOP preserves the performance benefit of a strong conventional primary while adding COPPER authority in slack cycles. The remaining work is production-scale workload breadth, production OoO/SoC integration, and calibrated silicon power.

## References

1. Augury: Using Data Memory-Dependent Prefetchers to Leak Data at Rest. https://www.prefetchers.info/augury.pdf
2. GoFetch: Breaking Constant-Time Cryptographic Implementations Using Data Memory-Dependent Prefetchers. https://gofetch.fail/
3. SplittingSecrets: A Compiler-Based Defense for Preventing Data Memory-Dependent Prefetcher Side-Channels. https://arxiv.org/abs/2601.12270
4. PreFence: A Scheduling-Aware Defense Against Prefetching-Based Side-Channel Attacks. https://arxiv.org/abs/2410.00452
5. PhantomFetch: Obfuscating Loads against Prefetcher Side-Channel Attacks. https://arxiv.org/abs/2511.05110
6. ICP: Exploiting Instruction Correlation for Prefetching Irregular Memory Accesses. https://arxiv.org/abs/2605.15645
7. DX100: A Programmable Data Access Accelerator for Indirection. https://arxiv.org/abs/2505.23073
8. Pointer-Chase Prefetcher for Linked Data Structures. https://arxiv.org/abs/1801.08088
9. Improved Prefetching Techniques for Linked Data Structures. https://arxiv.org/abs/2505.21669
10. Okapi: Efficiently Safeguarding Speculative Data Accesses in Sandboxed Environments. https://arxiv.org/abs/2312.08156
11. SafeSpec: Banishing the Spectre of a Meltdown with Leakage-Free Speculation. https://arxiv.org/abs/1806.05179
12. BliMe: Verifiably Secure Outsourced Computation with Hardware-Enforced Taint Tracking. https://arxiv.org/abs/2204.09649
13. HardTaint: Production-Run Dynamic Taint Analysis via Selective Hardware Tracing. https://arxiv.org/abs/2402.17241
14. PICASSO: Scaling CHERI Use-After-Free Protection to Millions of Allocations using Colored Capabilities. https://arxiv.org/abs/2602.09131
15. ARM MTE Performance in Practice. https://arxiv.org/abs/2601.11786
16. Revelator: Rapid Data Fetching via OS-Driven Hash-based Speculative Address Translation. https://arxiv.org/abs/2508.02007
17. ChampSim. https://github.com/ChampSim/ChampSim
18. GAP Benchmark Suite. https://github.com/sbeamer/gapbs
19. Intel Data Dependent Prefetcher guidance. https://www.intel.com/content/www/us/en/developer/articles/technical/software-security-guidance/technical-documentation/data-dependent-prefetcher.html
20. Self-invalidating TLB Entries. https://www.csa.iisc.ac.in/~arkapravab/papers/pact2017_final_version.pdf
21. ecoTLB: Eventually Consistent TLBs. https://www.cs.yale.edu/homes/abhishek/kumar-taco20.pdf

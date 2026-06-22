# COPPER Prior-Art Review

Date: 2026-06-11

Scope: public academic papers, arXiv records, project pages, patent search signals, and open-source search signals for COPPER: Committed Pointer-Provenance Prefetching.

## Exact Claim Reviewed

The defensible novelty claim is not "secure prefetching" and not "pointer prefetching." Those are heavily explored areas.

The narrow claim reviewed here is:

> COPPER-LINE gates a data-memory-dependent prefetcher (DMP) using line/word-local clean pointer-provenance metadata. A memory word is eligible to be dereferenced by the DMP only if committed architectural execution has previously proven that exact word to be a pointer/address source, the word has not been overwritten or invalidated since proof, the security/domain context matches, and normal translation/permission checks pass.

The refined mechanism adds:

> Recursive Carried-Provenance (RCP): a DMP-prefetched line may seed deeper data-dependent prefetches only if the prefetched source word/value already has committed provenance in the ledger; the carried record preserves source identity/context, not authority.

> CPTQ: a Committed Page-Translation Queue that permits cross-page DMP issue only after the committed-provenance gate and a valid process translation.

> CEPF: a Commit-Epoch Provenance Filter that allows backend proof creation only if a committed dependent memory operation carries a source epoch that still matches the current source-word epoch.

> PASB: Provenance Address-Space Binding that keys source proofs and carried records by a translation identity token, rather than by a hardware context alone.

> CTLW: Committed Target-Line Witnessing that permits cross-page recursive target formation only from an exact demand-observed virtual-to-physical cache-line witness; witness-derived fills are terminal until demand-validated.

> CLPD: a Compressed Line-Provenance Directory that retains source-line proof masks with source-line epochs, compressing repeated pointer-array/CSR proofs while invalidating the whole line on any source-line write or coherence event.

The named invariant is:

> No DMP dereference from unproven, stale, cross-domain, or permission-invalid data words.

This is different from a DMP that merely checks whether a value "looks like" an address, and different from disabling the prefetcher during sensitive regions.

## Bottom Line

To the best of public knowledge from this pass, I did not find public prior art that already does the exact COPPER mechanism: a DMP-specific, committed-execution, clean-since-proof pointer-provenance bit/vector or ledger attached to source words and used as a hard DMP eligibility rule, with recursive runahead still gated by committed source-word proof.

However, reviewers will see strong adjacent prior art. The idea is not "new because metadata exists" or "new because DMPs exist." Its publishable contribution has to be the invariant and the measured security/performance tradeoff:

1. Keep most useful pointer/indirect prefetching.
2. Block GoFetch/Augury-style data-at-rest activation.
3. Do this with tiny line metadata and coherence-aware clearing, rather than compiler transformation or global prefetcher disable.

My skeptical novelty risk is 4/10 for the broad COPPER-LINE framing because adjacent work on DMPs, indirect prefetching, taint, capabilities, and prefetcher defenses is crowded. For the narrower RCP/PASB/CTLW mechanism, after additional public searches for committed pointer provenance, DMP committed provenance, address-space-bound DMP proof, and committed translation witness variants, I would rate public novelty risk at 3/10. CLPD should be presented as a measured storage representation for the COPPER invariant, not as an independently broad metadata invention; region/line metadata is crowded, but the exact use as retained committed DMP source authority still did not surface in this public pass. This is not a freedom-to-operate opinion and does not rule out unpublished industrial designs.

## Prior-Art Comparison

| Prior art | What it does | Similarity to COPPER | Key difference | Novelty risk |
|---|---|---:|---|---:|
| Augury: Using Data Memory-Dependent Prefetchers to Leak Data at Rest | Identifies an Apple A14/M1 Array-of-Pointers DMP that examines memory data and prefetches through pointer-like values. | Very high problem overlap | Attack/reverse engineering work, not a hardware defense. It shows why unproven data-driven dereference is dangerous. | 8 |
| GoFetch | Demonstrates practical key extraction from constant-time crypto via DMPs that dereference loaded values that look pointer-like. | Very high threat overlap | Attack and software guidance. It does not propose committed pointer-provenance metadata in cache lines. | 8 |
| SplittingSecrets | Compiler defense that transforms secret data so it does not resemble addresses and trigger DMPs; includes AArch64 backend support. | High security-goal overlap | Software transformation of secrets, not a hardware DMP rule. Does not preserve all DMP behavior for ordinary pointer structures. | 6 |
| PreFence | OS/scheduling-aware defense that disables prefetchers during security-critical windows on platforms that allow this. | Medium security overlap | Coarse disable/enable policy. COPPER aims to keep safe DMP activity active continuously. | 5 |
| PhantomFetch | Hardware-agnostic load obfuscation against IP-stride prefetcher side channels. | Medium prefetch-security overlap | Targets IP-stride coupling, not data-memory-dependent dereference from data words. | 4 |
| Pointer-chase prefetchers / AoP / indirect prefetchers | Prefetch linked structures or arrays of pointers for performance. | High mechanism overlap | Performance-only: they identify future pointers, but do not require committed proof that the source word is a valid pointer source. | 7 |
| ICP: Instruction-Correlation Prefetching | Recent irregular prefetcher using instruction-level correlations, outperforming DMP on some benchmarks. | Medium performance overlap | Avoids DMP-style memory-content dereference; not a DMP safety/provenance defense. | 4 |
| DX100 | Programmable data access accelerator for indirection and indirect memory access streams. | Medium indirect-access overlap | Offload/accelerator for bandwidth and reordering, not side-channel-safe DMP gating. | 3 |
| SafeSpec | Keeps speculative side effects in shadow structures until commit to mitigate Spectre/Meltdown-style leakage. | Medium invariant overlap around commit | Handles speculative side effects. COPPER targets non-speculative/data-at-rest DMP activation and source-word eligibility. | 5 |
| Hardware taint / DIFT / BliMe / HardTaint | Tracks information flow or tainted data in hardware/software hybrids. | Medium metadata overlap | Taint tracks secrecy/flow. COPPER tracks "proven pointer source and clean since proof" only for DMP dereference permission. | 6 |
| CHERI / Morello / PICASSO colored capabilities | Pointer/capability metadata and provenance-validity tables for memory safety, including Arm Morello in the CHERI ecosystem. | High provenance-wording overlap | Capability systems protect architectural pointer use and require ISA/software ecosystem support. COPPER is a microarchitectural DMP eligibility structure for ordinary AArch64-style pointers. | 6 |
| ARM MTE / memory tags | Tags memory granules to detect memory safety errors. | Low-medium metadata overlap | Allocation/tag checking, not proof that a cache word was committed-used as an address source for DMP gating. | 3 |
| Patents/open-source search signals | Searched for DMP/pointer-provenance/prefetcher/taint combinations. | Unknown | No close public patent or open implementation surfaced in this web pass. This is not a freedom-to-operate opinion. | 4 |
| COPPER-RCP/CPTQ exact search strings | Additional search for committed pointer provenance, DMP committed provenance, pointer-provenance prefetchers, and patent variants. | Low exact overlap found | Returned adjacent DMP attacks/defenses and irregular prefetchers, but no public recursive carried-provenance authority rule. | 3 |
| COPPER-PASB exact search strings | Additional 2026-06-11 search for DMP/prefetcher ASID, VMID, address-space, context-token, and committed provenance combinations. | Low exact overlap found | Returned SplittingSecrets, DMP attack summaries, ICP, and general prefetch-security work, but no public source-word proof key bound to an address-space token for DMP authority. | 3 |
| Revelator / speculative address translation | Predicts or accelerates VA-to-PA data fetches using OS-driven mapping regularity. | Medium translation/prefetch adjacency | CTLW does not predict physical addresses and is not a general translation accelerator; it reuses exact committed demand-observed target-line translations only after COPPER source authority and PASB match. | 4 |
| COPPER-CTLW exact search strings | Additional 2026-06-11 search for committed translation witness, target-line witness, target-page witness, prefetch translation proof, and ASID-bound translation witness variants. | Low exact overlap found | Returned translation acceleration and general prefetch work, but no public exact committed target-line translation witness used as recursive DMP authority. | 3 |
| COPPER-CLPD exact search strings | Additional 2026-06-11 search for DMP provenance, line provenance directory, region metadata, and prefetcher authority combinations. | Medium metadata adjacency | Line/region metadata and compressed tracking are known ideas; the defensible claim is narrower: a line-epoch proof mask retaining committed DMP source authority while conservatively invalidating source-line writes. | 5 |

## Source Notes

- Augury shows that DMPs examine memory contents and use them to choose prefetch targets, leaking data at rest; it also identifies an Apple AoP DMP that prefetches patterns like `*A[i]`.
- GoFetch expands the threat to practical cryptographic key extraction and says the DMP activates on values that look like pointers.
- GoFetch's public page also notes platform-specific DMP disable paths such as DIT/DOIT or Apple HID configuration bits, reinforcing why a fine-grained hardware authority rule is a distinct research direction.
- SplittingSecrets is the closest DMP-specific defense found. It prevents secret memory from looking like addresses with compiler transformations, rather than adding a DMP hardware invariant.
- PreFence is the closest broad prefetch-defense mechanism: disable the prefetcher during sensitive operations.
- Pointer-chase, indirect, ICP, and DX100 work show that the performance side is crowded. COPPER should not be pitched as a new indirect prefetcher.
- CHERI/PICASSO are the closest provenance-adjacent works. The paper must clearly distinguish "architectural capability provenance for memory safety" from "microarchitectural committed pointer-use proof for DMP eligibility."
- PASB should be framed as a full-system correction to the COPPER proof key, not as a broad new address-space tagging mechanism. Address-space identifiers, ASIDs, VMIDs, and PCIDs are well-known; the new claim is binding DMP source-word authority to that token so committed proof cannot move across Linux address spaces sharing a hardware context.
- CTLW should be framed as a full-system correction to recursive target formation, not as a general address-translation accelerator. Virtual-to-physical translation caches and speculative translation mechanisms are known. The new claim is exact committed target-line witness reuse after COPPER source proof and PASB authority, with terminal witness-derived fills to prevent recursive amplification.
- CLPD should be framed as a capacity representation for COPPER, not as a new kind of directory by itself. Its value is that the GAPBS-backed topology trace exposed an edge-ledger capacity cliff and CLPD recovered most speedup with 8,192 line entries while preserving zero unsafe modeled DMP prefetches.

## How to Frame COPPER So It Survives

Weak framing:

> We add provenance bits to a prefetcher.

This is likely to be rejected as "taint tracking plus a prefetcher."

Stronger framing:

> DMPs are unsafe because they treat address-shaped data as prefetch authority. COPPER replaces address-shapedness with a new authority invariant: a cache word may be DMP-dereferenced only after committed execution has consumed that exact word as an address source, and the proof is destroyed by any write, invalidation, domain mismatch, or permission failure.

This makes the novelty the eligibility rule and its coherence/commit behavior, not the mere presence of metadata.

## Remaining Reviewer Risks

1. "This is just taint tracking." Response: COPPER's metadata is not secrecy taint. It is a positive proof of pointer-source eligibility, scoped to DMP dereference.
2. "This is just CHERI/MTE tags." Response: CHERI/MTE protect architectural memory safety. COPPER protects a microarchitectural prefetcher that can otherwise dereference data never used architecturally.
3. "This kills DMP usefulness." Response must be quantitative. Our synthetic traces show COPPER-LINE keeps pointer-chain benefits while blocking unproven and cross-domain dereferences, but we still need SPEC/GAP/gem5-class traces.
4. "Industry already does something like this secretly." Response: possible. Public claim must be "to the best of public knowledge." The paper should emphasize an open invariant, RTL sketch, and reproducible experiments.
5. "Why not just disable DMP under DIT/DOIT/security mode?" Response: COPPER is continuous, fine-grained, and aims to preserve safe performance outside and inside mixed-security workloads.

## Verdict

Current state: strong workshop / focused architecture-security candidate, still not a guaranteed top-tier paper. The 2026-06-15 full-system refresh adds official GAPBS, public Olden, heap/fake-pointer PEB controls, scalable CLPD SRAM route evidence, and stronger conventional built-in prefetcher baselines.

Novelty risk: 3/10 for the combined public RCP/PASB/CTLW/CLPD/PEB COPPER authority invariant; 5-6/10 if reviewed only as broad safe-DMP gating because commercial DDP details and patents are opaque
Feasibility: 8/10
Measurability: 9/10
Paper strength now: 7/10 after AArch64 Minor/O3 sensitivity, graph-style and GAPBS-backed provenance traces, CLPD capacity evidence, CEPF backend proof filtering, randomized RTL-invariant testing, full-system PASB/CTLW/CTLW-terminal timing evidence, official GAPBS controls, public Olden, and Vivado CLPD/PEB evidence. The score is held down by workload breadth and the fact that DCPT/SPP/AMPM beat COPPER on public Olden when the metric is raw timing rather than safe content-derived DMP authority.
Paper strength if backed by broader pointer-rich real workloads and production-style backend/TLB/coherence integration: 8+/10

Best next experiment: move from generated/freestanding, official GAPBS, public Olden, and GAPBS-backed topology replay to SPEC-like, database/runtime, language-VM, or crypto-adjacent AArch64 Linux workloads plus GoFetch/Augury-inspired adversarial traces. The result that would make this paper top-tier credible is:

> COPPER blocks all DMP data-at-rest oracle cases in adversarial traces while preserving most of the speedup of an unsafe DMP on benign pointer-intensive workloads, at metadata cost small enough for L1/L2 cache integration.

## Sources

- Augury PDF: https://www.prefetchers.info/augury.pdf
- GoFetch project/paper page: https://gofetch.fail/
- SplittingSecrets: https://arxiv.org/abs/2601.12270
- PreFence: https://arxiv.org/abs/2410.00452
- PhantomFetch: https://arxiv.org/abs/2511.05110
- ICP: https://arxiv.org/abs/2605.15645
- DX100: https://arxiv.org/abs/2505.23073
- Pointer-Chase Prefetcher: https://arxiv.org/abs/1801.08088
- SafeSpec: https://arxiv.org/abs/1806.05179
- BliMe: https://arxiv.org/abs/2204.09649
- HardTaint: https://arxiv.org/abs/2402.17241
- Revelator: https://arxiv.org/abs/2508.02007
- PICASSO / colored capabilities: https://arxiv.org/abs/2602.09131
- ARM MTE performance/practice: https://arxiv.org/abs/2601.11786

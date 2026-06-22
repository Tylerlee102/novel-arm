# COPPER Prior-Art Refresh

Date: 2026-06-19

Scope: public web, academic, and patent-facing search for COPPER-like data-memory-dependent prefetcher defenses. Search terms included committed pointer-provenance prefetching, data-dependent/data-memory-dependent prefetcher provenance, pointer provenance hardware prefetcher, content-directed prefetcher pointer provenance, and patents around pointer/content-directed prefetching.

## Search Result Summary

| Source | What It Shows | Relationship To COPPER | Novelty Impact |
|---|---|---|---|
| Augury, "Using Data Memory-Dependent Prefetchers to Leak Data at Rest" | Establishes the DMP threat model: DMPs examine memory contents and may dereference pointer-looking data, enabling data-at-rest leakage. | Very close threat model, but it is an attack/reverse-engineering paper, not a committed-provenance hardware defense. | Strengthens motivation; does not appear to anticipate COPPER's authority ledger. |
| GoFetch, "Breaking Constant-Time Cryptographic Implementations Using Data Memory-Dependent Prefetchers" | Shows practical cryptographic key extraction via DMP activation on pointer-looking values and discusses coarse mitigations such as DMP disable bits. | Very close security target, but defense guidance is disabling/avoidance-oriented rather than fine-grained DMP authority. | Strengthens motivation and crypto relevance; not a COPPER-like mechanism. |
| SplittingSecrets | Compiler transforms secret values to avoid DMP-induced leakage. | Software/compiler defense; it avoids pointer-looking secrets rather than changing prefetcher authority. | Distinct from COPPER; reviewers may compare as a software alternative. |
| Improved Prefetching Techniques for Linked Data Structures | Explicitly notes that CDP/DDP-style mechanisms can treat data as pointers because of missing pointer provenance. | The closest phrasing found: it identifies "lack of pointer provenance" as a flaw, but it does not provide COPPER's committed-source-word proof, clean-line lifetime, PASB/CTLW, or PEB rules. | Raises terminology collision risk; also supports the paper's premise that provenance is the right missing property. |
| Okapi | Tracks committed loads to learn legal speculative memory accesses for sandbox enforcement. | Shares the idea that committed behavior can establish a hardware legality set, but applies to speculative sandbox access bounds, not data-dependent prefetch dereference authority over source words/values. | Important neighboring concept; cite to avoid overclaiming "committed access learning" broadly. |
| Intel Data-Dependent Prefetcher guidance and SDM bits | Publicly describes DDP/DDP-disabling controls and security guidance. | Coarse control/disable path, not per-source committed pointer provenance. | Supports baseline comparison against disable-style mitigation. |
| US9886385B1, content-directed prefetch circuit with quality filtering | Patent scans cache-line fills for pointer candidates and uses quality counters indexed by PC/offset and other features. | Very close performance mechanism: pointer candidate scanning and recursive/content-directed filtering. It appears confidence/quality-driven, not committed architectural pointer-source authority with clean-since proof. | High prior-art proximity for CDP hardware; COPPER must emphasize authority invariant, not pointer detection. |
| US11693780B2, enhanced pointer identification and prefetching | Patent predicts pointer-load instructions and treats returned data as a second prefetch target. | Close pointer-chase prefetching mechanism, but framed as prediction of pointer loads and multi-stage prefetch, not security authority from committed prior dereference. | Prior-art risk for recursive pointer prefetch mechanics; not for COPPER's safety invariant. |
| US12050916B2, array-of-pointers prefetching | Patent targets arrays of pointers and future-load data prefetching. | Close workload/mechanism family, but not a public committed-source provenance defense. | Reinforces that AoP/pointer prefetching itself is not novel. |

## Reviewer-Skeptical Read

To the best of public knowledge from this refresh, COPPER should not claim novelty as "a pointer prefetcher," "a content-directed prefetcher," "recursive pointer prefetching," "quality-filtered pointer scanning," or "using committed events somewhere in hardware." Those themes have public predecessors.

The defensible novelty claim remains narrower:

```text
DMP dereference authority is granted only to a source word/value/context
that committed execution already used as an address source, remains clean
since proof, remains bound to the same address-space/security token, and
has an exact demand-observed target-line witness for cross-page recursive
fills.
```

That mechanism is materially more specific than a combination of known blocks because it defines a new negative right for DMPs: data that merely looks like a pointer has no microarchitectural dereference authority. The authority is source-word and value specific, carried recursively without creating fresh authority, revoked on clean-line/coherence/translation boundary events, and checked by RTL/SVA-style artifacts.

## Current Novelty Risk Adjustment

- Pointer/CDP prefetch mechanism novelty risk: high, 8/10.
- DMP security motivation novelty risk: high, 8/10.
- Committed-source-word DMP authority invariant with clean-line lifetime plus PASB/CTLW/PEB composition: moderate-low public novelty risk, 3/10.
- Reviewer confusion risk: medium, because "pointer provenance" is now visible in related prefetching language and Okapi uses committed-load tracking in a different domain.

## Sources

- Augury: https://www.prefetchers.info/augury.pdf
- GoFetch: https://gofetch.fail/
- SplittingSecrets: https://arxiv.org/html/2601.12270v1
- Improved Prefetching Techniques for Linked Data Structures: https://arxiv.org/html/2505.21669v1
- Okapi: https://arxiv.org/html/2312.08156v3
- Intel Data-Dependent Prefetcher guidance: https://www.intel.com/content/www/us/en/developer/articles/technical/software-security-guidance/technical-documentation/data-dependent-prefetcher.html
- Intel SDM mirror with DDP disable bit text: https://kib.kiev.ua/x86docs/Intel/SDMs/335592-087.pdf
- US9886385B1: https://patents.google.com/patent/US9886385B1/en
- US11693780B2: https://patents.google.com/patent/US11693780B2/en
- US12050916B2: https://patents.google.com/patent/US12050916B2/en

status=PASS

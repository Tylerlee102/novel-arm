# COPPER Prior-Art Update

Date: 2026-06-16

Scope: public academic papers, arXiv entries, vendor/security notes, patents,
and open web results for data-memory-dependent prefetching, pointer-chase
prefetching, prefetcher side-channel defenses, capability/provenance-assisted
prefetching, and content-directed prefetcher patents.

## Updated Claim Boundary

The safest novelty claim is **not** a "first DMP defense" or priority claim.
That claim is too broad because SplittingSecrets is a 2026 compiler-based DMP
defense. The defensible COPPER claim is a narrower distinction:

> The current public-literature pass did not identify another DMP authority
> mechanism that permits content-derived dereference only from committed
> source-word pointer provenance, bound to address-space authority, and, for
> recursive cross-page targets, an exact committed target-line translation
> witness.

SARI-RQ should be treated as an implementation/timing structure for the SoC
revocation path, not as the paper's core novelty.

## Closest Public Prior Art

| Work | What it does | Similarity to COPPER | Difference from COPPER | Novelty risk |
|---|---|---|---|---:|
| Augury, IEEE S&P 2022, https://jose-sv.github.io/publication/augury | Demonstrates DMP leakage of data-at-rest on Apple A14/M1-class processors. | Establishes the security problem COPPER targets. | Attack paper; no committed-provenance hardware authority rule. | Low |
| GoFetch, USENIX Security 2024, https://www.usenix.org/system/files/usenixsecurity24-chen-boru.pdf | Shows practical cryptographic attacks using DMP behavior. | Direct threat model for unsafe content-derived prefetching. | Attack and mitigation discussion, not an RTL authority mechanism. | Low |
| SplittingSecrets, arXiv 2026, https://arxiv.org/abs/2601.12270 | Compiler transforms secrets so they are not stored in address-like form, avoiding DMP activation. | It is a direct DMP side-channel defense and therefore blocks any broad "first defense" claim. | Software/compiler hardening for selected secrets; it avoids DMP activation rather than changing the DMP's hardware authority model. | Medium |
| Intel Data Dependent Prefetcher note, https://www.intel.com/content/www/us/en/developer/articles/technical/software-security-guidance/technical-documentation/data-dependent-prefetcher.html | Describes DDP limits: memory type/addressability constraints and no recursive dereference of DDP-fetched contents. | Shows commercial DDPs may already include safety-oriented constraints. | Public note does not disclose committed source-word provenance, CLPD/CEPF/PASB/CTLW, or recursive witness-gated authority. | Medium |
| Content-directed prefetch patent US9886385B1, https://patents.google.com/patent/US9886385B1/en | Detects pointer candidates in fills and gates prefetches with quality-factor counters indexed by PC/offset/history. | Very close to DMP/content-directed prefetch structure. | Performance/quality filtering, not committed architectural pointer provenance or target-line translation witnesses. | Medium |
| Linkey, arXiv 2025, https://arxiv.org/html/2505.21669v1 | Hardware/software linked-data-structure prefetching using layout hints to reduce speculative pointer guessing. | Avoids blind pointer inference for performance and applicability. | Requires software layout/root information; not a secret-safe DMP authority layer for ordinary AArch64 memory. | Medium |
| CHERI-picking, PLOS 2023, https://people.ece.ubc.ca/sasha/papers/plos23-final64.pdf | Uses CHERI capability tags to identify pointers and prefetch referenced pages. | Provenance/capability-assisted pointer prefetching is conceptually close. | Capability ISA/OS page-prefetch setting; COPPER targets ordinary AArch64-style DMP cache prefetching without capability pointers. | Medium |
| Secure Prefetching for Secure Cache Systems, MICRO 2024, https://webdiis.unizar.es/~agusnt/PDF/24/24_MICRO.pdf | Studies on-commit prefetching and timeliness mechanisms for secure cache systems. | Uses commit timing as part of prefetch security/performance design. | Addresses invisible-speculation cache systems and conventional prefetchers, not content-derived DMP dereference authority. | Medium |
| PreFence, EuroS&P 2025, https://cispa.de/en/research/publications/84658-prefence-a-fine-grained-and-scheduling-aware-defense-against-prefetching-based-attacks | Scheduler/application-controlled prefetcher disable during sensitive regions. | Security defense against prefetcher side channels. | Coarse software-controlled disable/enable; not a hardware rule that admits safe content-derived candidates. | Low |

## Reviewer-Sensitive Consequences

- COPPER must explicitly cite SplittingSecrets and PreFence as DMP/prefetcher
  defenses and avoid implying that defenses only disable prefetching.
- COPPER should cite CHERI-picking and Linkey when discussing pointer-provenance
  and software/hardware-assisted pointer prefetching.
- COPPER's key distinction is **ordinary-pointer committed execution as
  authority**: no CHERI capability tags, no software secret splitting, no
  layout hints, and no pure quality filtering.
- Intel's public DDP note means the paper should not speculate that industry
  lacks DMP safety constraints. The honest framing is that public descriptions
  do not reveal COPPER-style committed provenance, PASB, CTLW, or SARI-RQ.

## Updated Novelty Risk

| Claim | Risk | Reason |
|---|---:|---|
| "First DMP defense" | 9/10 | Publicly false or at least indefensible after SplittingSecrets/PreFence. |
| "First public hardware DMP authority mechanism based on committed source provenance plus PASB/CTLW" | 3/10 | Closest public work uses software secret transformation, capability-tag page prefetching, layout hints, quality counters, or disable controls. |
| "SARI-RQ ring queue is novel" | 8/10 | Ring queues are standard; cite it only as a timing/refinement structure. |
| "End-to-end AArch64/SoC-feasible COPPER evidence" | 4/10 | Stronger after LSQ and AMBA/SARI bridge RTL, but still not a commercial OoO proof. |

## Sources Checked

- Augury project page: https://jose-sv.github.io/publication/augury
- GoFetch paper: https://www.usenix.org/system/files/usenixsecurity24-chen-boru.pdf
- SplittingSecrets arXiv entry: https://arxiv.org/abs/2601.12270
- Intel DDP note: https://www.intel.com/content/www/us/en/developer/articles/technical/software-security-guidance/technical-documentation/data-dependent-prefetcher.html
- US9886385B1 content-directed prefetch patent: https://patents.google.com/patent/US9886385B1/en
- Linkey arXiv HTML: https://arxiv.org/html/2505.21669v1
- CHERI-picking paper: https://people.ece.ubc.ca/sasha/papers/plos23-final64.pdf
- Secure Prefetching for Secure Cache Systems: https://webdiis.unizar.es/~agusnt/PDF/24/24_MICRO.pdf
- PreFence publication page: https://cispa.de/en/research/publications/84658-prefence-a-fine-grained-and-scheduling-aware-defense-against-prefetching-based-attacks

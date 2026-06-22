# COPPER Prior-Art Update, 2026-06-15

Honesty stance: this is not an absolute claim of invention. It is a public
prior-art comparison saying that, to the best of public knowledge checked here,
COPPER's mechanism is not merely a renamed pointer prefetcher, DMP, or quality
filter.

## Core Mechanism Under Review

COPPER means Committed Pointer-Provenance Prefetching:

> A content-derived pointer candidate may issue only if it is backed by a
> commit-created source proof that remains live under source-line revocation,
> domain/epoch boundary rules, translation/permission checks, and, for recursive
> cross-page issue, an exact target-line witness.

The named mechanism is the COPPER authority chain:

- CEPF: commit-epoch proof creation at retired dependent memory operations.
- CLPD: compressed line-provenance directory storing source-line/word proof
  authority.
- CTLW: exact target-line witness directory for recursive cross-page issue.
- PEB: provenance epoch boundary for O(1) domain/context revocation.
- CS-SARI: conflict-scoped SoC/coherence revocation hold, avoiding global stalls
  where the source/target event cannot affect the candidate.

## Prior-Art Comparison

| Prior art | What it does | Similarity to COPPER | Key difference | Novelty risk |
|---|---|---|---|---:|
| Dependence-Based Prefetching for Linked Data Structures, ASPLOS 1998 ([PDF](https://ftp.cs.wisc.edu/sohi/papers/1998/asplos-prefetch-lds.pdf)) | Dynamically extracts dependence relationships among pointer loads and runs a prefetch engine ahead of the processor. | Targets linked data structures and pointer-load latency. | It predicts/traverses pointer-load dependence kernels; it does not require a commit-created provenance proof, source-line revocation, CTLW target witness, or boundary epoch invariant before content-derived issue. | 4 |
| Pointer Cache Assisted Prefetching, MICRO 2002 ([PDF](https://cseweb.ucsd.edu/~calder/papers/MICRO-02-PCache.pdf)) | Uses a pointer cache as a value predictor for load base addresses to expose pointer-chain parallelism. | Uses remembered pointer/load values to accelerate pointer chasing. | It is load-value prediction for pointer bases, not a proof-carrying content-prefetch authority system tied to commit, invalidation, translation, and permission state. | 4 |
| Content-directed prefetch with quality filtering, US9886385B1 ([Google Patents](https://patents.google.com/patent/US9886385B1/en)) | Scans cache-line fills for pointer candidates and filters them with PC/offset quality counters. | Very close at the "scan memory contents for pointer-looking values" layer. | Its admission test is a learned quality/confidence filter; COPPER's admission test is a safety/provenance invariant. The patent does not disclose commit-created source proofs, CTLW exact witnesses, or PEB/CS-SARI revocation. | 5 |
| Enhanced recursive pointer-chasing prefetcher, WO2022171309A1 ([Google Patents](https://patents.google.com/patent/WO2022171309A1/en)) | Hardware recursive traversal prefetcher for linked structures. | Recursive pointer chasing is central overlap. | It focuses on recursive traversal performance. COPPER focuses on authority-bounded recursive issue: live source proof plus live target witness plus scoped revocation. | 5 |
| Intel Data Dependent Prefetcher public guidance ([Intel](https://www.intel.com/content/www/us/en/developer/articles/technical/software-security-guidance/technical-documentation/data-dependent-prefetcher.html)) | Defines data-dependent prefetching from memory contents and documents restrictions: architecturally readable current context, allowed speculative-read memory type, and no recursive dereference of data-dependent prefetched lines. | Industry DDP is the closest conceptual class. | Intel's disclosed restrictions are context/readability and non-recursion limits. COPPER permits recursive content-derived prefetching only when a CTLW witness and committed source proof remain live. That is a different positive authority mechanism. | 6 |
| Augury Apple DMP reverse engineering ([PDF](https://www.prefetchers.info/augury.pdf), [project page](https://www.prefetchers.info/)) | Shows a data memory-dependent prefetcher that examines memory contents and can leak pointer values. | Establishes real DMPs and their security concern. | Augury is an attack/reverse-engineering study, not a constructive commit-provenance design. COPPER's contribution is an RTL/model invariant intended to prevent unproven content-derived issue. | 3 |
| GoFetch, USENIX Security 2024 ([PDF](https://www.usenix.org/system/files/usenixsecurity24-chen-boru.pdf)) | Demonstrates end-to-end attacks on constant-time cryptography using DMP behavior. | Strongly motivates DMP safety mechanisms. | GoFetch is a security attack and software/system analysis. It does not propose CLPD/CTLW/PEB authority-gated DMP hardware. | 3 |
| Prefetch side-channel attacks, CCS 2016 ([PDF](https://gruss.cc/files/prefetch.pdf)) | Shows prefetch can leak address-translation information and compromise isolation. | Motivates translation/permission and side-channel caution. | It studies explicit prefetch side effects and attacks; COPPER is a hardware admission/revocation mechanism for content-derived prefetches. | 3 |
| Complex/graph prefetching in gem5, Cambridge TR-923 ([PDF](https://www.cl.cam.ac.uk/techreports/UCAM-CL-TR-923.pdf)) | Implements complex/graph prefetchers in gem5 with TLB interaction. | Similar evaluation substrate and virtual-address prefetch concern. | It is not a commit-provenance authority chain and does not define a safety invariant over source proof, target witness, and revocation events. | 3 |

## Why This Is Not Merely Combined RTL Blocks

The individual blocks are not the paper claim. The paper claim is the invariant
that connects them:

`issue(candidate) -> committed_source_proof_live && source_word_proven && source_epoch_current && source_domain_current && translation_ok && permission_ok && (!recursive_cross_page || exact_target_witness_live) && !scoped_revocation_hazard`

The blocks exist because each term in that predicate has a different lifetime:
commit-time proof creation, cache-line write/fill/invalidate lifetime, target
translation/remap lifetime, domain-boundary lifetime, and external coherence/IO
event lifetime. Removing any one term changes measurable behavior:

- Without CTLW, recursive cross-page candidates can be translated without exact
  target-line authority.
- Without PEB, boundary revocation requires sweeping the directory or risks
  stale proofs.
- Without CS-SARI, external source-line/target-remap hazards either create
  stale authority or force broad global stalls.
- Without CLPD, the mechanism collapses toward a costly per-pointer table or a
  confidence-only content-directed prefetcher.

## Current Novelty Assessment

To the best of public knowledge from this pass, COPPER is closest to a
content-directed/DMP pointer prefetcher with security restrictions. The novelty
is not "it prefetches pointers." The plausible novelty is:

1. Commit-created provenance, not confidence, is the admission source.
2. Recursive cross-page issue is allowed only with exact target-line witness
   authority.
3. Boundary and SoC/coherence revocation are part of the prefetch admission
   invariant, not external cleanup.
4. The same invariant is implemented in gem5 behavior, RTL/SVA checkers, and
   synthesis/place-route artifacts.

Novelty risk after this pass: 3/10 for the mechanism as a whole, but 5-6/10
for broad claims about "safe DMP" because industry DDP details and patents are
partly opaque. The paper should present COPPER as a concrete public design point
and measured invariant, not as the first safe DMP ever.

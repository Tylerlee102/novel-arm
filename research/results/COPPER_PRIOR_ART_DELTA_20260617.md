# COPPER/SCOOP Prior-Art Delta

Date: 2026-06-17

Scope: targeted public search for work that could collapse COPPER/SCOOP into a renamed known mechanism. This is not an exhaustive patent/legal search and should be phrased as "to the best of public knowledge."

| Public work | What it establishes | Similarity to COPPER/SCOOP | Difference that still matters | Novelty risk |
|---|---|---|---|---:|
| Augury: Using Data Memory-Dependent Prefetchers to Leak Data at Rest, 2022, https://www.prefetchers.info/augury.pdf | Publicly demonstrates commercial Apple DMP behavior and data-at-rest leakage primitives. | Same DMP threat class and pointer-looking-data activation. | Attack/reverse-engineering paper; does not propose committed pointer-provenance authority, PASB, CTLW, CLPD, PEB, or slack-only coexistence. | 8 |
| GoFetch, USENIX Security 2024, https://gofetch.fail/ | Shows practical key extraction from constant-time crypto through Apple DMP behavior; reports Intel DMP is more restrictive but present. | Same motivating failure: DMP turns data into attacker-observable memory activity. | Attack and mitigation discussion; no public hardware rule that authorizes DMP issue only from committed pointer-source proof. | 8 |
| Intel Data Dependent Prefetcher guidance, updated 2022, https://www.intel.com/content/www/us/en/developer/articles/technical/software-security-guidance/technical-documentation/data-dependent-prefetcher.html | Documents DDP restrictions: user-mode limits, domain isolation, no recursive dereference, and disable controls. | Closest public industrial mitigation signal because it constrains DDP side channels. | Public behavior is restriction/disable/isolation, not a positive committed-source provenance authority that preserves recursive content-derived issue with CTLW witnesses. | 6 |
| SplittingSecrets, arXiv 2601.12270, 2026, https://arxiv.org/abs/2601.12270 | Compiler defense transforms secrets so they do not look like addresses to DMPs. | Same DMP side-channel problem and AArch64 relevance. | Software hardening avoids DMP activation on protected data; COPPER changes hardware prefetch authority and is not secret-specific. | 6 |
| ICP: Exploiting Instruction Correlation for Prefetching Irregular Memory Accesses, arXiv 2605.15645, 2026, https://arxiv.org/abs/2605.15645 | Recent irregular prefetcher using instruction correlation and speculative computation; compares against DMP. | Irregular memory prefetch performance and DMP-related baseline. | Performance prefetcher; does not address DMP data-at-rest safety or committed provenance. It strengthens the need to avoid overclaiming performance. | 5 |
| DX100, ISCA 2025, https://arxiv.org/abs/2505.23073 | Programmable accelerator for bulk indirect memory accesses and memory bandwidth utilization. | Targets indirection and graph/database-style memory behavior. | ISA/offload accelerator for performance, not a transparent DMP authority/security mechanism. | 4 |
| Pointer-Chase Prefetcher for Linked Data Structures, arXiv 1801.08088, 2018, https://arxiv.org/abs/1801.08088 | Pointer-chase prefetching with compiler hints for linked data structures. | Pointer prefetching target domain. | Does not solve address-shaped data-at-rest leakage and does not define committed-source proof as DMP authority. | 5 |

## Delta Conclusion

The public-prior-art picture still supports the narrow COPPER/SCOOP claim: the novelty is not "metadata," "pointer prefetching," "indirect prefetching," or "prefetch throttling." Those are all crowded. The remaining defensible contribution is the named authority invariant and its measured implementation path:

```text
DMP content-derived issue is allowed only when the source word has committed
pointer-source proof, the proof remains clean and address-space bound, and
cross-page recursive targets use committed target-line witnesses.
```

SCOOP then contributes a coexistence invariant rather than a new ordinary prefetcher: a conventional primary keeps strict issue priority, while COPPER may issue only in slack cycles. The 2026-06-17 app matrix makes this framing important because SPP wins raw speed on all eight public application points, while SPP+COPPER slack preserves SPP-class timing and retains the COPPER authority filter.

Status: `novelty_risk=3/10` for the specific public COPPER/SCOOP authority-and-coexistence claim; higher if reviewers flatten the work into generic metadata, taint tracking, or ordinary indirect prefetching.

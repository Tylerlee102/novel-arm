# COPPER SARI/CS-SARI AMBA CHI/ACE Event Map

Date: 2026-06-19

Scope: this is a public, high-level mapping from AMBA-style coherence and maintenance event classes to COPPER authority actions. It does not copy proprietary Arm microarchitecture, confidential implementation details, or complete CHI/ACE opcode tables. It is meant to make the SARI/CS-SARI contract concrete enough for paper review and future RTL integration.

Public context used:

- Arm CHI protocol fundamentals describe CHI as a coherent interconnect protocol family for scalable systems: https://developer.arm.com/documentation/102407/0102/CHI-protocol-fundamentals
- Arm's public ACE/cache-coherency whitepaper describes ACE/ACE-Lite support for system-level coherency, cache maintenance, DVM, and barriers: https://developer.arm.com/-/media/Arm%20Developer%20Community/PDF/CacheCoherencyWhitepaper_6June2011.pdf
- gem5's public CHI documentation describes a CHI-based Ruby protocol model for design-space exploration: https://www.gem5.org/documentation/general_docs/ruby/CHI/
- Public verification/vendor discussions identify CHI/ACE-family concerns such as snoops, DVM, remote invalidation, cache maintenance, poisoning/protection, and persistence-related operations, but the COPPER mapping below stays at the event-class level.

## Authority Actions

| COPPER action | Meaning |
|---|---|
| `source_revoke(line, domain)` | Clear CLPD/CEPF source proof for a cache line/domain because bytes that justified DMP authority may have changed or become unowned. |
| `target_witness_revoke(line, token)` | Clear CTLW target-line witness because virtual-to-physical or permission authority may be stale. |
| `pasb_token_revoke(token)` | Clear or retire proof tied to an address-space/security/VM token. |
| `peb_epoch_bump(domain)` | Advance the provenance epoch so pre-boundary proofs cannot authorize post-boundary DMP issue. |
| `candidate_hold(source_line, target_line, token)` | Hold DMP issue while a relevant revocation is same-cycle or queued. |
| `overflow_global_hold()` | Conservative fallback when the scoped revocation queue cannot preserve precision. |

## Event Map

| AMBA-style event class | COPPER action | Why this is required | Precision rule |
|---|---|---|---|
| Same-line write by CPU, DMA, coherent I/O, or accelerator | `source_revoke`; `candidate_hold` for matching source-line candidates | A committed source proof is authority over source bytes; a later writer can change those bytes. | Hold only candidates whose source line/domain matches, unless the queue overflows. |
| Ownership transfer or snoop that can invalidate/dirty a source line | `source_revoke`; `candidate_hold` for matching source-line candidates | If another agent can modify or invalidate the line, old proof cannot keep authorizing DMP issue. | Use source-line match plus domain/token where available. |
| Cache maintenance invalidate/clean-invalidate affecting source lines | `source_revoke`; possible `peb_epoch_bump` for broad domain operations | Maintenance can discard or make stale the line state used by the proof directory. | Exact line/range clear if decoded; epoch bump for broad or ambiguous operations. |
| DVM/TLBI or translation-context invalidation | `target_witness_revoke`; `pasb_token_revoke`; optional `peb_epoch_bump` | CTLW and PASB depend on committed translation/context authority. | Token/range precision when available; otherwise conservative token or domain clear. |
| Page-table permission downgrade observed through TLB/cache-maintenance path | `target_witness_revoke`; `candidate_hold` for matching target-line candidates | A prefetch must not use a stale permission witness. | Target-line/token match. |
| Security-domain, VM, ASID/VMID, PASID, or context-color boundary | `pasb_token_revoke`; `peb_epoch_bump` | Pre-boundary source proof must not authorize post-boundary DMP issue. | Domain/token exact when exposed; epoch bump for coarse boundaries. |
| Barrier or synchronization event that orders maintenance/revocation | Drain queued `candidate_hold` before allowing affected DMP issue | COPPER must not race a queued invalidation with a new DMP issue. | Affected domain/token only if the queue has sufficient metadata. |
| Non-coherent DMA write not visible as a coherent transaction | Platform must inject `source_revoke` or use `overflow_global_hold` before affected DMP issue | Otherwise COPPER cannot know source bytes changed outside coherence. | Treat as unsupported until the SoC supplies a range event or software boundary hook. |
| Poison/protection/error indication on source or target data | `source_revoke` or `target_witness_revoke`; suppress proof creation from poisoned data | Error-marked data should not create new DMP authority. | Match line and token when possible. |

## Integration Invariants

1. A DMP candidate may issue only if no same-cycle or queued SARI event conflicts with its source line, target line, or PASB token.
2. A source proof must be cleared or made unreachable before any later write/ownership/maintenance event can let stale source bytes authorize DMP issue.
3. A target witness must be cleared before any remap, TLBI, permission downgrade, or token change can let stale translation authority authorize cross-page recursive issue.
4. Queue overflow must fall back to a global hold or epoch/token bump; it must not silently drop revocation.
5. Unrelated source-line, target-line, and token events should not globally stall DMP issue when CS-SARI can prove non-conflict.

## Relationship To Existing Local Evidence

- `research/results/COPPER_TLB_COHERENCE_CONTRACT.md` models source revocation, queued target revocation, remap, token TLBI, global TLBI, and permission downgrade.
- `research/results/COPPER_AMBA_SARI_FRONTDOOR_RTL_SUMMARY.md` maps the public event classes into a small synthesizable SARI front door and registered timing slice.
- `research/results/COPPER_TLB_COHERENCE_AUTHORITY_FILTER_RTL_SUMMARY.md` implements the issue-side hold and exact-witness/permission gate.
- `research/results/COPPER_SARI_RQ_STATE_SPACE.md` covers ring/shift queue equivalence and overflow fallback.
- `research/results/COPPER_CS_SARI_COMPOSITION_STATE_SPACE.md` checks the composed source-proof, target-witness, and revocation-hold rule.
- `research/results/cs_sari_gapbs_revocation/CS_SARI_GAPBS_REVOCATION_SUMMARY.md` and the sensitivity sweep quantify the benefit of scoped holds over a global hold policy.

## Remaining Gap

This map is stronger than saying "connect it to coherence later," and the companion AMBA-SARI frontdoor RTL now gives a small public decoder for the event classes. It is still not a complete CHI/ACE/AXI decoder, not a formal proof against the full Arm AMBA specifications, and not wired into a production RTL fabric. The next integration step is to bind these event classes to a concrete public CHI/ACE model with range, barrier, ordering, and overflow coverage.

status=PASS

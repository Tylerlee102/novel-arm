# COPPER ROPL Replay/Exception/Alias Contract

Date: 2026-06-19

ROPL means Retirement-Only Provenance Latching. It is the backend rule
that COPPER source proofs are latched only at dependent-memory retirement
after replay, squash, exception, alias, memory-order, translation, and
permission hazards have been quarantined. This is a bounded public model,
not a proprietary ARM backend.

Sound ROPL invariant:

- the dependent memory operation is at retirement, not execute
- the source load is older, executed, retired, and exception-free
- the dependent memory operation is exception-free
- the carried source tag is live and not stale
- replay generation, squash epoch, and same-line alias generation still match
- no memory-order violation is pending
- target translation and permission checks succeed

| Variant | Unique states | Legal proofs | Unsafe proofs | First unsafe counterexample | First legal proof witness |
|---|---:|---:|---:|---|---|
| FULL_ROPL_CONTRACT | 888 | 1 | 0 | - | execute_source_capture_ropl_tag -> retire_source_load -> execute_dependent_memory -> retire_dependent_memory |
| BUG_EXECUTE_STAGE_PROOF | 1720 | 1 | 3 | execute_source_capture_ropl_tag -> execute_dependent_memory | execute_source_capture_ropl_tag -> retire_source_load -> backend_squash_epoch_advance -> execute_dependent_memory -> backend_squash_epoch_advance -> retire_dependent_memory |
| BUG_SOURCE_NOT_RETIRED | 920 | 1 | 1 | execute_source_capture_ropl_tag -> execute_dependent_memory -> retire_dependent_memory | execute_source_capture_ropl_tag -> retire_source_load -> execute_dependent_memory -> retire_dependent_memory |
| BUG_NO_EXCEPTION_QUARANTINE | 903 | 1 | 1 | execute_source_capture_ropl_tag -> retire_source_load -> execute_dependent_memory -> dependent_exception_before_retire -> retire_dependent_memory | execute_source_capture_ropl_tag -> retire_source_load -> execute_dependent_memory -> retire_dependent_memory |
| BUG_NO_REPLAY_GENERATION | 899 | 1 | 1 | execute_source_capture_ropl_tag -> retire_source_load -> execute_dependent_memory -> dependent_replay -> execute_dependent_memory -> retire_dependent_memory | execute_source_capture_ropl_tag -> retire_source_load -> execute_dependent_memory -> retire_dependent_memory |
| BUG_NO_SQUASH_EPOCH | 888 | 1 | 1 | execute_source_capture_ropl_tag -> retire_source_load -> execute_dependent_memory -> backend_squash_epoch_advance -> retire_dependent_memory | execute_source_capture_ropl_tag -> retire_source_load -> execute_dependent_memory -> retire_dependent_memory |
| BUG_NO_ALIAS_GENERATION | 888 | 1 | 1 | execute_source_capture_ropl_tag -> retire_source_load -> execute_dependent_memory -> same_line_store_alias_kill -> retire_dependent_memory | execute_source_capture_ropl_tag -> retire_source_load -> execute_dependent_memory -> retire_dependent_memory |
| BUG_NO_ORDER_VIOLATION_CLEAR | 903 | 1 | 1 | execute_source_capture_ropl_tag -> retire_source_load -> execute_dependent_memory -> memory_order_violation -> retire_dependent_memory | execute_source_capture_ropl_tag -> retire_source_load -> execute_dependent_memory -> retire_dependent_memory |
| BUG_NO_TRANSLATION_PERMISSION_GATE | 888 | 1 | 3 | execute_source_capture_ropl_tag -> retire_source_load -> execute_dependent_memory -> target_translation_fault -> retire_dependent_memory | execute_source_capture_ropl_tag -> retire_source_load -> execute_dependent_memory -> retire_dependent_memory |

Interpretation:

- Full ROPL contract status: PASS.
- The full contract has reachable legal proof creation and zero bounded unsafe proof creations.
- Every weakened variant has a short counterexample, so the replay/exception/alias checks are not cosmetic.
- This closes a paper-facing integration ambiguity, but it is still not an end-to-end proof of a production ARM load-store queue.

status=PASS

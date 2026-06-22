# COPPER OoO-LSQ Proof Contract

Date: 2026-06-17

This bounded checker targets the production-backend integration objection:
a COPPER proof must not be created by speculative execution, by a younger
dependent memory operation before source retirement, after a backend flush,
after source revocation or epoch/value drift, or when target translation or
permission fails. It models a minimal out-of-order backend contract rather
than a proprietary ARM LSQ.

Sound proof contract:

- dependent memory operation reaches retirement/architectural commit
- source load that produced the carried tag is older and retired
- carried source tag is live and not stale
- current source epoch/value still match the captured tag
- no backend flush has invalidated the speculative chain
- target translation and permission checks succeed

| Variant | Unique states | Legal proofs | Unsafe proofs | First unsafe counterexample | First legal proof witness |
|---|---:|---:|---:|---|---|
| FULL_CONTRACT | 156 | 1 | 0 | - | execute_source_load_capture_tag -> retire_source_load -> execute_dependent_memory -> retire_dependent_memory |
| BUG_EXECUTE_STAGE_PROOF | 228 | 1 | 3 | execute_source_load_capture_tag -> execute_dependent_memory | execute_source_load_capture_tag -> retire_source_load -> silent_epoch_value_change -> execute_dependent_memory -> silent_epoch_value_change -> retire_dependent_memory |
| BUG_SOURCE_NOT_RETIRED | 180 | 1 | 1 | execute_source_load_capture_tag -> execute_dependent_memory -> retire_dependent_memory | execute_source_load_capture_tag -> retire_source_load -> execute_dependent_memory -> retire_dependent_memory |
| BUG_NO_FLUSH_CLEAR | 226 | 1 | 1 | execute_source_load_capture_tag -> retire_source_load -> execute_dependent_memory -> backend_flush -> retire_dependent_memory | execute_source_load_capture_tag -> retire_source_load -> execute_dependent_memory -> retire_dependent_memory |
| BUG_NO_SOURCE_REVOCATION | 100 | 1 | 1 | execute_source_load_capture_tag -> retire_source_load -> execute_dependent_memory -> source_write_or_fill_revoke -> retire_dependent_memory | execute_source_load_capture_tag -> retire_source_load -> execute_dependent_memory -> retire_dependent_memory |
| BUG_NO_CEPF_EPOCH_VALUE | 156 | 1 | 1 | execute_source_load_capture_tag -> retire_source_load -> execute_dependent_memory -> silent_epoch_value_change -> retire_dependent_memory | execute_source_load_capture_tag -> retire_source_load -> execute_dependent_memory -> retire_dependent_memory |
| BUG_NO_TRANSLATION_PERMISSION_GATE | 156 | 1 | 3 | execute_source_load_capture_tag -> retire_source_load -> execute_dependent_memory -> target_translation_fault -> retire_dependent_memory | execute_source_load_capture_tag -> retire_source_load -> execute_dependent_memory -> retire_dependent_memory |

Interpretation:

- Full contract status: PASS.
- The full contract has reachable legal proof creation and zero bounded unsafe proof creations.
- Every weakened variant has a short counterexample in this model.
- This reduces the production OoO integration ambiguity by making the backend proof contract executable, but it is not a full formal proof of a commercial ARM load-store queue.

status=PASS

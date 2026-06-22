# COPPER TLB/Coherence Authority Contract

Date: 2026-06-17

This bounded checker targets the production memory-system objection:
a COPPER DMP issue must require live source proof, an exact target-line
witness under the current address-space token, fresh remap/TLBI epoch,
permission success, and no conflicting pending invalidation.

Modeled contract:

- committed source proof is separate from hardware source metadata
- exact target-line witness metadata is separate from target ground truth
- target remap, token TLBI, and global TLBI invalidate target truth and bump a witness epoch
- DMA/CHI updates invalidate source truth through a bounded queue
- same-cycle and queued revocations must hold conflicting DMP candidates
- permission downgrade blocks target issue until permission is restored and demand revalidates authority

Model: 2 source lines, 2 target lines, 2 tokens,
revocation queue depth 2, trace bound 5.

Full-contract reachable states explored: 39098

| Variant | Reachable states | Safety result | Precision result | Notes |
|---|---:|---|---|---|
| FULL_TLB_COHERENCE_CONTRACT | 39098 | PASS | PASS | no stale authority found; has unrelated-revocation precision witness at event=dma_write(src=1), query=valid=1 src=0 token=0 tgt=0 |
| BUG_NO_INCOMING_SOURCE_HOLD | 39098 | FAIL expected | n/a | counterexample reason=incoming_source_revocation; path=commit_source(src=0) -> record_target(token=0, tgt=0); event=dma_write(src=0); query=valid=1 src=0 token=0 tgt=0 |
| BUG_NO_QUEUED_SOURCE_HOLD | 39091 | FAIL expected | n/a | counterexample reason=queued_source_revocation; path=commit_source(src=0) -> record_target(token=0, tgt=0) -> dma_write(src=0); event=none; query=valid=1 src=0 token=0 tgt=0 |
| BUG_NO_TARGET_REMAP_HOLD | 39098 | FAIL expected | n/a | counterexample reason=same_cycle_target_remap; path=commit_source(src=0) -> record_target(token=0, tgt=0); event=target_remap(token=0, tgt=0); query=valid=1 src=0 token=0 tgt=0 |
| BUG_NO_TARGET_REMAP_CLEAR | 50170 | FAIL expected | n/a | counterexample reason=stale_target_epoch; path=commit_source(src=0) -> target_remap(token=0, tgt=0) -> record_target(token=0, tgt=0); event=none; query=valid=1 src=0 token=0 tgt=0 |
| BUG_NO_TOKEN_TLBI_HOLD | 39098 | FAIL expected | n/a | counterexample reason=same_cycle_token_tlbi; path=commit_source(src=0) -> record_target(token=0, tgt=0); event=tlbi_token(token=0); query=valid=1 src=0 token=0 tgt=0 |
| BUG_NO_TOKEN_TLBI_CLEAR | 52142 | FAIL expected | n/a | counterexample reason=stale_target_epoch; path=commit_source(src=0) -> tlbi_token(token=0) -> record_target(token=0, tgt=0); event=none; query=valid=1 src=0 token=0 tgt=0 |
| BUG_NO_GLOBAL_TLBI_HOLD | 39098 | FAIL expected | n/a | counterexample reason=same_cycle_global_tlbi; path=commit_source(src=0) -> record_target(token=0, tgt=0); event=tlbi_global; query=valid=1 src=0 token=0 tgt=0 |
| BUG_NO_GLOBAL_TLBI_CLEAR | 54112 | FAIL expected | n/a | counterexample reason=stale_target_epoch; path=commit_source(src=0) -> tlbi_global -> record_target(token=0, tgt=0); event=none; query=valid=1 src=0 token=0 tgt=0 |
| BUG_NO_PERMISSION_DOWNGRADE_HOLD | 39098 | FAIL expected | n/a | counterexample reason=same_cycle_permission_downgrade; path=commit_source(src=0) -> record_target(token=0, tgt=0); event=permission_downgrade(token=0, tgt=0); query=valid=1 src=0 token=0 tgt=0 |
| BUG_NO_PERMISSION_GATE | 39098 | FAIL expected | n/a | counterexample reason=permission_not_allowed; path=commit_source(src=0) -> record_target(token=0, tgt=0) -> permission_downgrade(token=0, tgt=0); event=none; query=valid=1 src=0 token=0 tgt=0 |
| BUG_NO_TARGET_QUEUE_HOLD | 39098 | FAIL expected | n/a | counterexample reason=queued_target_revocation; path=commit_source(src=0) -> record_target(token=0, tgt=0) -> target_remap(token=0, tgt=0); event=none; query=valid=1 src=0 token=0 tgt=0 |
| BUG_PAGE_LEVEL_TARGET_WITNESS | 39098 | FAIL expected | n/a | counterexample reason=missing_or_stale_target_witness; path=commit_source(src=0) -> record_target(token=0, tgt=0); event=none; query=valid=1 src=0 token=0 tgt=1 |
| BUG_SOURCE_ONLY_AUTHORITY | 39098 | FAIL expected | n/a | counterexample reason=missing_or_stale_target_witness; path=commit_source(src=0) -> record_target(token=0, tgt=0); event=none; query=valid=1 src=0 token=0 tgt=1 |
| BUG_GLOBAL_HOLD | 39098 | PASS | FAIL expected | unnecessary global hold; path=commit_source(src=0) -> record_target(token=0, tgt=0); event=dma_write(src=1); query=valid=1 src=0 token=0 tgt=0 |

## Hazard Coverage

### incoming_source_revocation

- Path: `commit_source(src=0) -> record_target(token=0, tgt=0)`
- State: `source_truth=[True, False] source_meta=[True, False] target_truth=[[True, False], [False, False]] target_meta=[[True, False], [False, False]] current_epoch=[[0, 0], [0, 0]] witness_epoch=[[0, 0], [0, 0]] permission=[[True, True], [True, True]] source_queue=[] target_queue=[] overflow=0`
- Event: `dma_write(src=0)`
- Query: `valid=1 src=0 token=0 tgt=0`

### queued_source_revocation

- Path: `commit_source(src=0) -> record_target(token=0, tgt=0) -> dma_write(src=0)`
- State: `source_truth=[False, False] source_meta=[True, False] target_truth=[[True, False], [False, False]] target_meta=[[True, False], [False, False]] current_epoch=[[0, 0], [0, 0]] witness_epoch=[[0, 0], [0, 0]] permission=[[True, True], [True, True]] source_queue=[0] target_queue=[] overflow=0`
- Event: `none`
- Query: `valid=1 src=0 token=0 tgt=0`

### queued_target_revocation

- Path: `commit_source(src=0) -> record_target(token=0, tgt=0) -> target_remap(token=0, tgt=0)`
- State: `source_truth=[True, False] source_meta=[True, False] target_truth=[[False, False], [False, False]] target_meta=[[True, False], [False, False]] current_epoch=[[0, 0], [0, 0]] witness_epoch=[[0, 0], [0, 0]] permission=[[True, True], [True, True]] source_queue=[] target_queue=[0] overflow=0`
- Event: `none`
- Query: `valid=1 src=0 token=0 tgt=0`

### same_cycle_global_tlbi

- Path: `commit_source(src=0) -> record_target(token=0, tgt=0)`
- State: `source_truth=[True, False] source_meta=[True, False] target_truth=[[True, False], [False, False]] target_meta=[[True, False], [False, False]] current_epoch=[[0, 0], [0, 0]] witness_epoch=[[0, 0], [0, 0]] permission=[[True, True], [True, True]] source_queue=[] target_queue=[] overflow=0`
- Event: `tlbi_global`
- Query: `valid=1 src=0 token=0 tgt=0`

### same_cycle_permission_downgrade

- Path: `commit_source(src=0) -> record_target(token=0, tgt=0)`
- State: `source_truth=[True, False] source_meta=[True, False] target_truth=[[True, False], [False, False]] target_meta=[[True, False], [False, False]] current_epoch=[[0, 0], [0, 0]] witness_epoch=[[0, 0], [0, 0]] permission=[[True, True], [True, True]] source_queue=[] target_queue=[] overflow=0`
- Event: `permission_downgrade(token=0, tgt=0)`
- Query: `valid=1 src=0 token=0 tgt=0`

### same_cycle_target_remap

- Path: `commit_source(src=0) -> record_target(token=0, tgt=0)`
- State: `source_truth=[True, False] source_meta=[True, False] target_truth=[[True, False], [False, False]] target_meta=[[True, False], [False, False]] current_epoch=[[0, 0], [0, 0]] witness_epoch=[[0, 0], [0, 0]] permission=[[True, True], [True, True]] source_queue=[] target_queue=[] overflow=0`
- Event: `target_remap(token=0, tgt=0)`
- Query: `valid=1 src=0 token=0 tgt=0`

### same_cycle_token_tlbi

- Path: `commit_source(src=0) -> record_target(token=0, tgt=0)`
- State: `source_truth=[True, False] source_meta=[True, False] target_truth=[[True, False], [False, False]] target_meta=[[True, False], [False, False]] current_epoch=[[0, 0], [0, 0]] witness_epoch=[[0, 0], [0, 0]] permission=[[True, True], [True, True]] source_queue=[] target_queue=[] overflow=0`
- Event: `tlbi_token(token=0)`
- Query: `valid=1 src=0 token=0 tgt=0`

## Precision Witness

The full contract permits a valid candidate while an unrelated
revocation exists. A global revocation hold would unnecessarily
block it, but the conflict-scoped rule keeps the safe issue open.

- Path: `commit_source(src=0) -> record_target(token=0, tgt=0)`
- State: `source_truth=[True, False] source_meta=[True, False] target_truth=[[True, False], [False, False]] target_meta=[[True, False], [False, False]] current_epoch=[[0, 0], [0, 0]] witness_epoch=[[0, 0], [0, 0]] permission=[[True, True], [True, True]] source_queue=[] target_queue=[] overflow=0`
- Event: `dma_write(src=1)`
- Query: `valid=1 src=0 token=0 tgt=0`

## Interpretation

The full TLB/coherence contract has no bounded stale-authority
counterexample and retains a precision witness against global
revocation hold. Removing source pending hold, target remap/TLBI
hold or clearing, permission gating, exact target-line witnessing,
or queued-target hold produces a short counterexample. This artifact
does not prove a commercial ARM memory hierarchy, but it turns the
production-integration boundary into an executable rule with explicit
weakened-variant failures.

Full contract status: PASS
status=PASS

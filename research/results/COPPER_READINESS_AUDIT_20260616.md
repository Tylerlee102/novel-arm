# COPPER/SCOOP Readiness Audit

Date: 2026-06-17

## Current Verdict

**Evidence-bounded regular-conference or artifact-track candidate; acceptance is not guaranteed.**

The project is materially stronger than the 2026-06-15 state. The biggest
improvement is that SCOOP is no longer just a plausible hybrid idea: it now has
gem5 integration, AArch64 full-system workload results, an adversarial fake-only
control, traffic-only and cache-observer DMP oracles, a three-seed observer
sweep, a split scan/probe audit, official GAPBS AArch64 full-system scaling
through g14, a bounded arbitration checker, and a Vivado XSim RTL arbiter test.
A new LSQ-style source-tag tracker and an LSQ-to-CEPF-to-line-gate end-to-end
harness also reduce the prior backend-integration gap. The newest refresh adds
a medium-scale Duktape public-runtime workload and a timed AMBA-frontdoor ->
SARI-RQ -> CLPD -> CTLW -> authority RTL path, which reduces the prior
SoC/coherence-integration objection. A follow-on unified LSQ-to-AMBA authority
top now composes the backend source-tag tracker, commit-epoch proof bridge,
AMBA/SARI revocation frontdoor, SARI-RQ, CLPD, CTLW witness directory, and final
authority gate in one synthesized/tested RTL path. The newest hardware cleanup
adds a one-cycle revocation slice whose invariant is that retimed SoC clears are
legal only while DMP issue authority remains closed over the slice.
The 2026-06-17 refresh closes a baseline-fairness gap in the public application
suite: SQLite, Lua, Duktape, and yyjson medium/stress runs now include stride,
DCPT, SPP, and AMPM. SPP is the best conventional baseline on all eight points,
while SPP+COPPER slack has an average signed gap of -0.006 percentage points
and a 0.360-point worst absolute gap, with zero translation faults and 92.9%
CTLW reduction versus naive DMP. A follow-on repeated public-app seed portfolio adds medium and stress
layout evidence for SQLite, Lua, and Duktape: 15 engine-seed points and 75
policy rows pass checksum and `rc=0`, translation faults remain zero,
standalone COPPER beats unsafe naive DMP on 9/15 points, COPPER cuts aggregate
naive CTLW misses by 90.706%, and SPP+COPPER slack stays within 0.760
percentage points of SPP. A bounded OoO-LSQ proof-contract checker now targets
the production-backend objection directly: the full contract has a reachable
legal proof witness and zero bounded unsafe proof creations, while every
weakened variant has a short counterexample.
A bounded TLB/coherence authority-contract checker now targets the stale
target-witness objection directly: the full rule explores 39,098 states with
zero bounded stale-authority issues and covers source revocation, queued target
revocation, remap, token TLBI, global TLBI, and permission downgrade. Page-level
witness, source-only authority, missed queue hold, missed TLBI/remap clearing,
and missed permission-gate variants all fail with short counterexamples.
A matching TLB/coherence issue-side RTL filter now passes 27 directed plus
10,000 randomized Vivado XSim checks with `errors=0` and synthesizes on
`xc7a35tcpg236-1` with 332 LUTs, 167 FFs, no BRAM/DSP, and +6.898 ns WNS at a
10 ns constraint.
A gem5-counter energy/pollution proxy scorecard now quantifies side effects
instead of leaving them qualitative. Standalone COPPER has a 2.105% mean
pressure score versus 2.364% for naive DMP, a 10.9% lower proxy pollution score,
while reducing CTLW misses by 90.3%. SPP+COPPER slack is within 0.5% runtime of
SPP on all eight public app points and adds 0.071 bus-byte-delta points plus
0.628 pressure-score points over SPP on average.

## What Is Strong Now

- **Named hybrid mechanism:** SCOOP, Slack-only COPPER Companion Prefetching.
- **Core invariant:** primary conventional prefetcher has strict issue
  priority; COPPER companion can issue only in primary slack cycles.
- **Direct security oracle:** unsafe DMP shows PF delta 32,760 and allowed delta
  32,760 when `secret=1`; COPPER and SCOOP allowed deltas are 0.
- **Observable cache oracle:** unsafe DMP reduces observer L1D misses by 14 and
  shifts relative timing by -4.906 pp; SCOOP companion allowed delta is 0.
- **Reproducibility:** three observer seeds show unsafe allowed deltas 63..65
  and L1D miss deltas -14..-9; SCOOP allowed delta set is 0.
- **Phase localization:** split scan/probe audit shows unsafe scan allowed delta
  66, while COPPER and SCOOP scan allowed deltas are both 0.
- **Public workloads:** SQLite, Lua, Duktape, yyjson, Olden, GAPBS, and heap/fake-only
  controls now run in the AArch64 full-system path.
- **Eight-point application baseline matrix:** SQLite/Lua/Duktape/yyjson medium and
  stress runs now include stride, DCPT, SPP, and AMPM. SPP wins raw timing on
  all eight points; SCOOP keeps SPP-class timing while preserving COPPER's
  content-derived authority checks.
- **Repeated public-engine layouts:** SQLite, Lua, and Duktape now run
  repeated medium and stress layout seeds with matching per-point checksums and
  `rc=0`. Across 15 engine-seed points, COPPER cuts naive CTLW misses by
  90.706% and SPP+COPPER slack stays within 0.760 percentage points of SPP.
- **Duktape medium scale:** a larger Duktape 2.7.0 public-runtime workload
  completes for `none`, `naive`, `copper_clpd64k_peb`, `spp`, and
  `spp_copper_slack` with matching checksum `0x2e53ef0`, zero COPPER
  translation faults, 90.8% COPPER reduction in naive CTLW misses, and
  `spp_copper_slack` at -6.950% versus -6.732% for SPP alone.
- **yyjson medium/stress scale:** a public yyjson JSON-parser workload completes
  all eight policy runs at both scales with matching checksums, zero COPPER
  translation faults, and 98.9% standalone COPPER reduction in naive CTLW
  misses on both medium and stress inputs.
- **Official GAPBS scale:** public GAPBS C++ AArch64/Linux full-system runs now
  cover BFS/CC/PR/SSSP across g10/g12/g14. At g14, COPPER blocks 453,375
  unproven candidates, keeps translation faults at 0, and reduces naive CTLW
  misses by 99.908%, with near-neutral aggregate timing (+0.029%).
- **RTL/checking:** SCOOP bounded checker passes to depth 10; Vivado XSim
  arbiter run passes 6 directed plus 10,000 randomized cases with `errors=0`.
- **Backend proof path:** a new LSQ-style source-tag tracker passes 21 directed
  plus 10,000 randomized Vivado XSim tests; the integrated LSQ -> CEPF -> line
  gate harness passes 33 directed plus 10,000 randomized tests with `errors=0`.
- **OoO-LSQ proof contract:** a bounded production-style backend contract
  checker requires dependent-memory retirement, older retired source load,
  live epoch/value-matched source tag, no backend flush, and target
  translation/permission success. The full contract passes with a legal proof
  witness and zero unsafe proofs; execute-stage proof, unretired source,
  no-flush-clear, no-source-revocation, no-CEPF-epoch/value, and no-permission
  variants all fail with short counterexamples.
- **TLB/coherence contract:** a bounded target-witness and revocation contract
  checker explores 39,098 full-contract states, covers seven stale-authority
  hazard classes, and shows that page-level target witnesses, source-only
  authority, missed queue hold, missed remap/TLBI clearing, and missed
  permission gating are unsafe in the model.
- **TLB/coherence RTL filter:** the synthesizable issue-side filter covers the
  same source/target/permission revocation contract at RTL, passes 27 directed
  plus 10,000 randomized Vivado XSim checks, and synthesizes with 332 LUTs /
  167 FFs / 0 BRAM / 0 DSP and +6.898 ns WNS at 10 ns.
- **Energy/pollution proxy:** a gem5-counter pressure scorecard over public
  SQLite/Lua/Duktape/yyjson full-system runs shows standalone COPPER has 10.9% lower
  mean proxy pollution than naive DMP while cutting CTLW misses by 90.3%; it
  also quantifies SCOOP's incremental traffic over SPP.
- **Backend path synthesis:** the LSQ tracker uses 217 LUTs / 312 FFs with
  +5.937 ns setup slack at 10 ns on `xc7a35tcpg236-1`; the integrated wrapper
  uses 1,960 LUTs / 1,336 FFs with +2.176 ns setup slack and no BRAM/DSP.
- **SoC authority path:** the AMBA-style SARI frontdoor passes 10 directed plus
  10,000 randomized Vivado XSim cases. Its registered timing slice uses 8 LUTs
  / 160 FFs and meets 10 ns with +7.525 ns WNS. The composed AMBA-frontdoor ->
  SARI-RQ -> CLPD -> CTLW -> authority bridge passes 15 directed plus 10,000
  randomized XSim cases and synthesizes with 4,106 LUTs / 3,130 FFs, no
  BRAM/DSP, zero warnings, and +1.082 ns WNS after replacing the original shift
  queue with SARI-RQ.
- **Unified LSQ-to-SoC authority RTL:** a full composed path from LSQ
  source-tag capture through CEPF, AMBA/SARI revocation, SARI-RQ, CLPD/CTLW,
  and the final DMP authority gate passes 18 directed plus 10,000 randomized
  Vivado XSim tests with `errors=0`. It synthesizes on `xc7a35tcpg236-1` with
  4,692 LUTs / 3,547 FFs / 0 BRAM / 0 DSP, zero warnings, and meets a 10 ns
  clock with +0.473 ns setup slack after the revocation-slice retiming.
- **SARI-RQ bounded check:** the new state-space checker explores 40
  ready-respecting states and confirms bounded ring/shift queue equivalence plus
  conservative overflow fallback under protocol violation.
- **Focused paper artifact:** `research/COPPER_SCOOP_CONFERENCE_DRAFT.docx`
  is an 8-page Word-counted draft integrating the new evidence.
- **Claim-to-evidence ledger:** `COPPER_CLAIM_EVIDENCE_MATRIX_20260617.md`
  maps the major paper claims to exact local artifacts, and
  `COPPER_TOP_TIER_GATE_AUDIT_20260617.md` separates focused-conference
  readiness from the still-unproven top-tier guarantee.

## Remaining Reviewer Risks

| Risk | Severity | Current response |
|---|---:|---|
| "Not enough real applications" | Medium | Public engines now include SQLite/Lua/Duktape/yyjson medium/stress full-system runs, repeated SQLite/Lua/Duktape layout sweeps, and official GAPBS g10/g12/g14; SPEC-like, database-scale, runtime-scale, and crypto-adjacent workloads remain valuable. |
| "Conventional prefetchers already win" | Medium | SCOOP reframes COPPER as a safe companion lane, not a replacement for SPP/DCPT/AMPM. |
| "Just metadata plus a prefetcher" | Medium | The paper must emphasize the committed-source authority invariant and differential oracle behavior, not novelty of generic metadata. |
| "Production backend integration missing" | Medium-low | New LSQ source-tag tracker, LSQ -> CEPF -> line-gate harness, full LSQ-to-AMBA authority-top Vivado evidence, bounded OoO-LSQ proof-contract counterexamples, a bounded TLB/coherence contract, and a synthesizable TLB/coherence issue filter exist; still not a full production OoO ARM LSQ or memory hierarchy. |
| "SoC revocation path incomplete" | Medium-low | AMBA-style frontdoor, SARI-RQ bounded checker, bridge XSim, full composed LSQ-to-SoC timing evidence, TLB/coherence contract counterexamples, and TLB/coherence RTL filter evidence now exist; still not a production ARM CHI/ACE/AXI implementation. |
| "Energy/pollution model is weak" | Medium-low | A transparent gem5-counter scorecard now covers bus bytes, DRAM reads, L2 replacements, and L1D replacements; calibrated power modeling or real hardware counters remain future work. |
| "Renderer QA missing" | Low | The direct PDF rebuild renders to 8 pages and passes text/audit checks; it remains dense and would still need camera-ready formatting polish. |

## Scores

| Dimension | Score |
|---|---:|
| Novelty risk | 3/10 for the public COPPER/SCOOP authority invariant; higher if reviewers treat it as generic metadata |
| Feasibility | 8/10 |
| Measurability | 9.2/10 |
| Hardware cost | 7.7/10 |
| Paper strength | 8.8/10 focused conference, 8.0/10 top-tier today |
| Publish-worthiness | 8/10 for workshop/focused venue; 7/10 for top-tier architecture/security |

## Submission Recommendation

Submit only after one more cleanup pass if targeting a serious workshop or
focused architecture/security venue. For a top-tier PhD conference, do not
promise acceptance; the backend proof-path objection is weaker now, while the
largest remaining gap is not basic Linux/GAPBS feasibility anymore. It is
SPEC-like or production-service application evidence plus a production-grade
OoO/coherence integration story. The eight-point app baseline matrix,
medium/stress SQLite/Lua/Duktape seed portfolio, yyjson medium/stress,
SARI-RQ evidence, the OoO-LSQ proof-contract checker, the TLB/coherence
contract checker, the TLB/coherence RTL filter, and the energy/pollution
scorecard move those gaps in the right direction, but do not eliminate them.

status=PASS_WITH_LIMITATIONS

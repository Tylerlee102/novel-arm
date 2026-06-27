# Numerical Validity Audit

Audit date: 2026-06-23

Scope: local COPPER/SCOOP research scripts, markdown result artifacts, claim gates, and packaged artifact copies under `research/`. I focused on unit/conditioning assumptions, hidden defaults, independence assumptions, stale claims, and whether refreshed claims are backed by regenerated outputs.

## Findings and Fixes

### 1. Pressure-score headline depended on one uncalibrated weighting

Severity: medium-high.

The energy/pollution scorecard reported a single mean pressure score, originally using one fixed weighted proxy over bus bytes, DRAM reads, L2 replacements, and L1D replacements. That base score was transparent, but the headline "18.8% lower proxy pollution score" could be overread as robust or calibrated.

Fix:

- `research/analyze_copper_energy_pollution_scorecard.py:41` now names the base weights explicitly.
- `research/analyze_copper_energy_pollution_scorecard.py:47` adds six checked weight scenarios.
- `research/analyze_copper_energy_pollution_scorecard.py:154` computes a weight-sensitivity table.
- `research/analyze_copper_energy_pollution_scorecard.py:308` writes `research/results/copper_energy_pollution_weight_sensitivity_20260617.csv`.
- `research/results/COPPER_ENERGY_POLLUTION_SCORECARD_20260617.md:25` now reports that COPPER is 18.1% to 20.6% lower than naive DMP across the checked weights, and lower-or-equal on 20/22 points under every checked weighting.

Updated interpretation: the 18.8% number is now clearly a base-weight result, not a calibrated silicon or platform-power result.

### 2. Synthetic cross-domain leakage count was tied to a hidden default

Severity: medium.

The main synthetic trace used `cross_domain_secret_rate=0.50`, so the previously reported cross-domain count looked like a single measured property of the mechanism rather than a parameterized workload mix.

Fix:

- `research/copper_final_eval.py:239` adds a report table builder for cross-domain mix sensitivity.
- `research/copper_final_eval.py:363` adds the `domain_mix_sweep` experiment over rates 0.00, 0.25, 0.50, 0.75, and 1.00.
- `research/results/COPPER_RESULTS.md:46` now includes the sensitivity section.
- `research/results/COPPER_RESULTS.md:54` and `research/results/COPPER_RESULTS.md:58` show the endpoints: naive cross-domain prefetches move from 0.0 at rate 0.00 to 2048.0 at rate 1.00, while COPPER-LINE stays at 0.0 in this model.

Updated interpretation: the cross-domain count is now presented as a workload-mix sensitivity result.

### 3. CS-SARI source/target revocations assumed independent event streams

Severity: medium.

The CS-SARI GAPBS proxy separately sampled source-line and target-witness revocations. That was useful, but it hid an independence assumption: real DMA/remap/TLBI bursts may correlate source and target hazards.

Fix:

- `research/copper_cs_sari_gapbs_revocation_eval.py:47` adds `source_target_correlation`.
- `research/copper_cs_sari_gapbs_revocation_eval.py:195` uses that parameter to force correlated target conflicts when a source conflict arrives.
- `research/copper_cs_sari_sensitivity_sweep.py:52` adds rho values 0.00 to 1.00.
- `research/copper_cs_sari_sensitivity_sweep.py:53` and `research/copper_cs_sari_sensitivity_sweep.py:54` make the addendum sampled and two-pass, while reusing the existing full queue/profile CSV when present.
- `research/results/cs_sari_gapbs_revocation/sensitivity/CS_SARI_SENSITIVITY_SWEEP.md:24` records that the correlation addendum uses `kron_g13` and `kron_g14`.
- `research/results/cs_sari_gapbs_revocation/sensitivity/CS_SARI_SENSITIVITY_SWEEP.md:27` and `research/results/cs_sari_gapbs_revocation/sensitivity/CS_SARI_SENSITIVITY_SWEEP.md:28` report zero scoped unsafe modeled issues, 15,481 no-hold unsafe issues, and 83.57% to 84.04% scoped-hold reduction across rho.

Updated interpretation: the sampled correlated case did not collapse the precision win in this balanced profile, mostly because the extra target conflicts overlap candidates already scoped-held by source conflicts. This remains a proxy, not a full-system CHI/DMA experiment.

### 4. Stale claim text could resurrect old 12-point/13.3% numbers

Severity: medium-low.

`research/build_copper_scoop_conference_docx.py` still contained older generated-paper text claiming a 13.3% lower mean pollution proxy, 1.460% versus 1.684%, 12 scorecard points, and older SPP+COPPER incremental traffic costs.

Fix:

- `research/build_copper_scoop_conference_docx.py:252` now says the 22-point scorecard gives an 18.8% base-weighted reduction and 18.1%-20.6% across checked weights.
- `research/build_copper_scoop_conference_docx.py:417` now uses 0.879% versus 1.083%, all 22 points, and the current 0.093 bus-byte and 0.222 pressure-score average increments.
- `research/build_copper_scoop_conference_docx.py:522` updates the evidence table blurb.
- Matching refreshed files were synced into `research/results/copper_public_artifact_package_20260620/research/`.

## Documentation and Gate Updates

- `research/COPPER_FULL_PAPER.md:5` and `research/COPPER_FINAL_OUTPUT.md:5` now include audit-refresh notes for the pressure weighting, cross-domain sensitivity, and CS-SARI correlation addendum.
- `research/build_copper_claim_evidence_matrix.py:153` narrows C5 to a base-weighted pressure claim with a sensitivity range.
- `research/build_copper_claim_evidence_matrix.py:169` and `research/verify_copper_artifacts.py:97` require the weight-sensitivity sentence as evidence.
- `research/results/COPPER_CLAIM_EVIDENCE_MATRIX_20260617.md:13` regenerated with C5 passing under the tightened wording.

## Verification Run

Completed:

- Python compilation for the patched scripts.
- `research/analyze_copper_energy_pollution_scorecard.py`
- `research/copper_final_eval.py`
- `research/copper_cs_sari_sensitivity_sweep.py`
- `research/build_copper_claim_evidence_matrix.py`
- `research/verify_copper_artifacts.py`

Verifier result:

- `research/results/COPPER_ARTIFACT_AUDIT_20260616.md` reports `Passed 177/177 artifact checks.`

Search checks:

- Before writing this report, active and packaged claim/generator/result files had no remaining hits for the stale strings `13.3% lower`, `1.460% versus 1.684%`, `0.184 bus-byte-delta`, or `COPPER 13.3%` outside inaccessible vendor directories. This report now mentions those strings only as historical audit findings.

## Remaining Caveats

- The pressure score is still a gem5-counter proxy, not calibrated energy or silicon power.
- The CS-SARI correlation addendum is sampled over two GAPBS topologies and still models revocation behavior; it does not replace a real coherent interconnect/DMA/TLBI trace.
- The existing full CS-SARI queue/profile sweep was reused from its CSV because two full interactive rerun attempts timed out at 120 seconds and 600 seconds before the script was changed to cache the base sweep.
- The synthetic cross-domain sweep varies one rate parameter; it does not exhaust all adversarial data-layout or domain-mixing distributions.

# COPPER Full-Core Integration Status

This directory exists to make the full-core PPA blocker explicit. The public
artifact now includes a PicoRV32 accepted open-source core-wrapper with both
baseline prefetch and COPPER integrated under the same mapped FPGA flow. That
evidence is labeled `accepted_core_wrapper`, not `full_core`.

`research/scripts/run_fullcore_synthesis.py` still writes BLOCKED rows for true
full-core designs instead of fabricating full-core area, timing, or power
numbers. Runnable open-source hardware evidence is limited to explicitly
labeled `near_core_stub` and `accepted_core_wrapper` rows.

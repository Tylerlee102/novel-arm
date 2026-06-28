# COPPER Full-Core Integration Status

This directory exists to make the full-core PPA blocker explicit. The public
artifact does not currently include a real CPU core wrapper with both baseline
prefetch and COPPER integrated under the same mapped timing/power flow.

`research/scripts/run_fullcore_synthesis.py` therefore writes BLOCKED rows for
`baseline_core_wrapper`, `core_wrapper_plus_baseline_prefetch`, and
`core_wrapper_plus_copper` instead of fabricating full-core area, timing, or
power numbers. The runnable open-source hardware evidence is limited to the
explicitly labeled `near_core_stub` rows.

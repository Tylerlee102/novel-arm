# COPPER Full-Core Integration Status

This directory contains two PicoRV32-based hardware targets:

- `picorv32_copper_wrapper.sv`: the older accepted open-source core-wrapper
  target. It instantiates PicoRV32, but keeps a simple NOP memory tie-off, so
  its evidence remains labeled `accepted_core_wrapper`.
- `picorv32_full_core_soc.sv`: the open-source PicoRV32 tiny-SoC full-core
  harness. It instantiates PicoRV32 with synthesizable local instruction/data
  memory and matched `full_core_baseline` / `full_core_plus_copper` top modules.

The tiny-SoC target is suitable for scoped `full_core` synthesis and mapped-FPGA
PPA rows when the generated CSVs show PASS. It is still not a production ARM
core, out-of-order backend, silicon result, or ASIC/foundry signoff flow.

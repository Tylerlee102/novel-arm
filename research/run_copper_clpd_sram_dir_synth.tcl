read_verilog -sv research/copper_clpd_sram_dir.sv
read_xdc research/copper_clpd_constraints.xdc
synth_design -top copper_clpd_sram_dir -part xc7a35tcpg236-1
report_utilization -file research/copper_clpd_sram_dir_utilization.rpt
report_timing_summary -file research/copper_clpd_sram_dir_timing.rpt
write_checkpoint -force research/copper_clpd_sram_dir_synth.dcp
quit

read_verilog -sv research/copper_provenance_epoch_boundary.sv
read_xdc research/copper_clpd_constraints.xdc
synth_design -top copper_provenance_epoch_boundary -part xc7a35tcpg236-1
report_utilization -file research/results/copper_peb_utilization.rpt
report_timing_summary -file research/results/copper_peb_timing.rpt
write_checkpoint -force research/results/copper_peb_synth.dcp
quit

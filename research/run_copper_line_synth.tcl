read_verilog -sv research/copper_line_provenance_gate.sv
read_xdc research/copper_line_constraints.xdc
synth_design -top copper_line_provenance_gate -part xc7a35tcpg236-1
report_utilization -file research/copper_line_utilization.rpt
report_timing_summary -file research/copper_line_timing.rpt
write_checkpoint -force research/copper_line_synth.dcp
quit

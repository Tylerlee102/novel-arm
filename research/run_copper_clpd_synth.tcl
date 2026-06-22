read_verilog -sv research/copper_clpd_gate.sv
read_xdc research/copper_clpd_constraints.xdc
synth_design -top copper_clpd_gate -part xc7a35tcpg236-1
report_utilization -file research/copper_clpd_utilization.rpt
report_timing_summary -file research/copper_clpd_timing.rpt
write_checkpoint -force research/copper_clpd_synth.dcp
quit

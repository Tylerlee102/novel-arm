source research/vivado_tclstore_bootstrap.tcl
read_verilog research/copper_sari_scoped_revoker_v.v
create_clock -period 10.000 -name clk [get_ports clk]
synth_design -top copper_sari_scoped_revoker -part xc7a35tcpg236-1
report_utilization -file research/results/copper_cs_sari_utilization.rpt
report_timing_summary -file research/results/copper_cs_sari_timing.rpt
write_checkpoint -force research/results/copper_cs_sari_synth.dcp
quit

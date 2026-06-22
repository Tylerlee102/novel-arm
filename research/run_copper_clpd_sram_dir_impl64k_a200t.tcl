read_verilog -sv research/copper_clpd_sram_dir.sv
read_xdc research/copper_clpd_constraints.xdc
set gen_list [list \
    BANKS=32 \
    BANK_IDX_W=5 \
    SETS_PER_BANK=2048 \
    SET_IDX_W=11 \
]
synth_design -top copper_clpd_sram_dir -part xc7a200tfbg676-2 -generic $gen_list -mode out_of_context
opt_design
place_design
route_design
report_utilization -file research/results/copper_clpd_sram_dir_clpd64k_a200t_impl_utilization.rpt
report_timing_summary -file research/results/copper_clpd_sram_dir_clpd64k_a200t_impl_timing.rpt
report_route_status -file research/results/copper_clpd_sram_dir_clpd64k_a200t_route_status.rpt
write_checkpoint -force research/results/copper_clpd_sram_dir_clpd64k_a200t_impl.dcp
quit

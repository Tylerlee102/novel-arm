proc run_copper_clpd_sram_cfg {name banks bank_idx_w sets_per_bank set_idx_w} {
    read_verilog -sv research/copper_clpd_sram_dir.sv
    read_xdc research/copper_clpd_constraints.xdc
    set gen_list [list \
        BANKS=$banks \
        BANK_IDX_W=$bank_idx_w \
        SETS_PER_BANK=$sets_per_bank \
        SET_IDX_W=$set_idx_w \
    ]
    synth_design -top copper_clpd_sram_dir -part xc7a35tcpg236-1 -generic $gen_list
    report_utilization -file research/results/copper_clpd_sram_dir_${name}_utilization.rpt
    report_timing_summary -file research/results/copper_clpd_sram_dir_${name}_timing.rpt
    write_checkpoint -force research/results/copper_clpd_sram_dir_${name}_synth.dcp
    close_design
}

run_copper_clpd_sram_cfg clpd8k 8 3 1024 10
run_copper_clpd_sram_cfg clpd16k 16 4 1024 10
quit

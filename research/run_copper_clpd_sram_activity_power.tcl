set results_dir "research/results"
file mkdir $results_dir

read_verilog -sv research/copper_clpd_sram_dir.sv
read_xdc research/copper_clpd_constraints.xdc

set gen_list [list \
    LINE_TAG_W=12 \
    WORDS_PER_LINE=16 \
    WORD_OFF_W=4 \
    TOKEN_W=4 \
    EPOCH_W=4 \
    BANKS=4 \
    BANK_IDX_W=2 \
    SETS_PER_BANK=16 \
    SET_IDX_W=4 \
]

synth_design -top copper_clpd_sram_dir -part xc7a35tcpg236-1 -generic $gen_list -mode out_of_context
opt_design
place_design
route_design

set vcd "$results_dir/copper_clpd_sram_dir_activity.vcd"
set activity_status "NO_VCD"
set activity_message "vcd_not_found"

if {[file exists $vcd]} {
    if {[catch {
        read_vcd \
            -strip_path copper_clpd_sram_dir_tb/dut \
            -out_file "$results_dir/copper_clpd_sram_dir_activity_vcd_unmatched.txt" \
            $vcd
    } err]} {
        set activity_status "READ_VCD_FAILED"
        set activity_message [string map {"," ";" "\n" " " "\r" " "} $err]
    } else {
        set activity_status "READ_VCD_OK"
        set activity_message ""
    }
}

report_power -file "$results_dir/copper_clpd_sram_dir_activity_power.rpt"
report_utilization -file "$results_dir/copper_clpd_sram_dir_activity_utilization.rpt"
report_timing_summary -file "$results_dir/copper_clpd_sram_dir_activity_timing.rpt"
write_checkpoint -force "$results_dir/copper_clpd_sram_dir_activity_impl.dcp"

set manifest [open "$results_dir/copper_clpd_sram_dir_activity_power_manifest_20260618.csv" "w"]
puts $manifest "activity_status,activity_message,vcd,report"
puts $manifest "$activity_status,$activity_message,$vcd,$results_dir/copper_clpd_sram_dir_activity_power.rpt"
close $manifest

quit

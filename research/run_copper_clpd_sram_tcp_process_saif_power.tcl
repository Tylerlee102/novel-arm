set results_dir "research/results"
file mkdir $results_dir

read_verilog -sv research/copper_clpd_sram_dir.sv
read_xdc research/copper_clpd_constraints.xdc

set gen_list [list \
    LINE_TAG_W=32 \
    WORDS_PER_LINE=16 \
    WORD_OFF_W=4 \
    TOKEN_W=8 \
    EPOCH_W=8 \
    BANKS=4 \
    BANK_IDX_W=2 \
    SETS_PER_BANK=256 \
    SET_IDX_W=8 \
]

set status "NO_SAIF"
set message "saif_not_found"
set saif "$results_dir/copper_clpd_sram_tcp_process_activity.saif"
set report "$results_dir/copper_clpd_sram_tcp_process_activity_saif_power.rpt"
set unmatched "$results_dir/copper_clpd_sram_tcp_process_activity_saif_unmatched.txt"
set manifest_path "$results_dir/copper_clpd_sram_tcp_process_activity_saif_power_manifest_20260620.csv"

if {[catch {
    synth_design -top copper_clpd_sram_dir -part xc7a35tcpg236-1 -generic $gen_list -mode out_of_context
    opt_design
    place_design
    route_design

    if {[file exists $saif]} {
        read_saif \
            -strip_path copper_clpd_sram_workload_activity_tb/dut \
            -out_file $unmatched \
            $saif
        set status "READ_SAIF_OK"
        set message ""
    }

    report_power -file $report
    report_utilization -file "$results_dir/copper_clpd_sram_tcp_process_activity_utilization.rpt"
    report_timing_summary -file "$results_dir/copper_clpd_sram_tcp_process_activity_timing.rpt"
    write_checkpoint -force "$results_dir/copper_clpd_sram_tcp_process_activity_impl.dcp"
} err]} {
    set status "FAILED"
    set message [string map {"," ";" "\n" " " "\r" " "} $err]
}

set manifest [open $manifest_path "w"]
puts $manifest "status,message,saif,report,unmatched"
puts $manifest "$status,$message,$saif,$report,$unmatched"
close $manifest

quit

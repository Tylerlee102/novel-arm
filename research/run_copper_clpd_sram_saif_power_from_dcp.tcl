set results_dir "research/results"
set dcp "$results_dir/copper_clpd_sram_dir_activity_impl.dcp"
set saif "$results_dir/copper_clpd_sram_dir_activity.saif"
set report "$results_dir/copper_clpd_sram_dir_activity_saif_power.rpt"
set unmatched "$results_dir/copper_clpd_sram_dir_activity_saif_unmatched.txt"
set manifest_path "$results_dir/copper_clpd_sram_dir_activity_saif_power_manifest_20260618.csv"

set status "NO_DCP"
set message "dcp_not_found"

if {[file exists $dcp] && [file exists $saif]} {
    if {[catch {
        open_checkpoint $dcp
        read_saif \
            -strip_path copper_clpd_sram_dir_tb/dut \
            -out_file $unmatched \
            $saif
        report_power -file $report
        close_design
    } err]} {
        set status "FAILED"
        set message [string map {"," ";" "\n" " " "\r" " "} $err]
        catch {close_design}
    } else {
        set status "READ_SAIF_OK"
        set message ""
    }
} elseif {![file exists $saif]} {
    set status "NO_SAIF"
    set message "saif_not_found"
}

set manifest [open $manifest_path "w"]
puts $manifest "status,message,dcp,saif,report,unmatched"
puts $manifest "$status,$message,$dcp,$saif,$report,$unmatched"
close $manifest

quit

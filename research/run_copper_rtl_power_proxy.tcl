set results_dir "research/results"

file mkdir $results_dir

set designs [list \
    [list copper_clpd_sram_dir_clpd1k_synth "$results_dir/copper_clpd_sram_dir_clpd1k_synth.dcp"] \
    [list copper_clpd_sram_dir_clpd2k_synth "$results_dir/copper_clpd_sram_dir_clpd2k_synth.dcp"] \
    [list copper_clpd_sram_dir_clpd4k_synth "$results_dir/copper_clpd_sram_dir_clpd4k_synth.dcp"] \
    [list copper_clpd_sram_dir_clpd8k_synth "$results_dir/copper_clpd_sram_dir_clpd8k_synth.dcp"] \
    [list copper_clpd_sram_dir_clpd16k_a200t_synth "$results_dir/copper_clpd_sram_dir_clpd16k_a200t_synth.dcp"] \
    [list copper_clpd_sram_dir_clpd64k_a200t_synth "$results_dir/copper_clpd_sram_dir_clpd64k_a200t_synth.dcp"] \
    [list copper_clpd_sram_dir_clpd64k_a200t_impl "$results_dir/copper_clpd_sram_dir_clpd64k_a200t_impl.dcp"] \
    [list copper_peb_synth "$results_dir/copper_peb_synth.dcp"] \
    [list copper_tlb_coherence_authority_filter_synth "$results_dir/copper_tlb_coherence_authority_filter_synth.dcp"] \
    [list copper_lsq_source_tag_tracker_synth "$results_dir/copper_lsq_source_tag_tracker_synth.dcp"] \
    [list copper_lsq_cepf_line_e2e_top_synth "$results_dir/copper_lsq_cepf_line_e2e_top_synth.dcp"] \
    [list copper_amba_sari_frontdoor_synth "$results_dir/copper_amba_sari_frontdoor_synth.dcp"] \
    [list copper_amba_sari_frontdoor_regslice_synth "$results_dir/copper_amba_sari_frontdoor_regslice_synth.dcp"] \
    [list copper_amba_sari_authority_bridge_top_synth "$results_dir/copper_amba_sari_authority_bridge_top_synth.dcp"] \
    [list copper_full_lsq_amba_authority_top_synth "$results_dir/copper_full_lsq_amba_authority_top_synth.dcp"] \
]

set manifest_path "$results_dir/copper_rtl_power_proxy_manifest_20260618.csv"
set manifest [open $manifest_path "w"]
puts $manifest "design,dcp,report,status,message"

foreach design $designs {
    set name [lindex $design 0]
    set dcp [lindex $design 1]
    set report "$results_dir/${name}_power_proxy.rpt"

    if {![file exists $dcp]} {
        puts $manifest "$name,$dcp,$report,MISSING_DCP,dcp_not_found"
        continue
    }

    set status "OK"
    set message ""

    if {[catch {
        open_checkpoint $dcp
        report_power -file $report
        close_design
    } err]} {
        set status "FAILED"
        set message [string map {"," ";" "\n" " " "\r" " "} $err]
        catch {close_design}
    }

    puts $manifest "$name,$dcp,$report,$status,$message"
}

close $manifest
quit

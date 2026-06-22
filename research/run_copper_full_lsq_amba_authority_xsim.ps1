$VivadoBin = "C:\AMDDesignTools\2025.2\Vivado\bin"

if (!(Test-Path "$VivadoBin\xvlog.bat")) {
    Write-Error "xvlog.bat was not found. Edit `$VivadoBin in this script to match your Vivado install."
    exit 1
}

& "$VivadoBin\xvlog.bat" -sv `
    research\copper_lsq_source_tag_tracker.sv `
    research\copper_commit_epoch_proof_bridge.sv `
    research\copper_amba_sari_frontdoor.sv `
    research\copper_sari_ring_revoker.sv `
    research\copper_clpd_gate.sv `
    research\copper_ctlw_witness_dir.sv `
    research\copper_full_authority_gate.sv `
    research\copper_full_lsq_amba_authority_top.sv `
    research\copper_full_lsq_amba_authority_tb.sv
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

& "$VivadoBin\xelab.bat" copper_full_lsq_amba_authority_tb -s copper_full_lsq_amba_authority_tb_sim
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

& "$VivadoBin\xsim.bat" copper_full_lsq_amba_authority_tb_sim -runall
exit $LASTEXITCODE

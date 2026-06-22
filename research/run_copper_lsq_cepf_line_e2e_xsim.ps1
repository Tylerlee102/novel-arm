$VivadoBin = "C:\AMDDesignTools\2025.2\Vivado\bin"

if (!(Test-Path "$VivadoBin\xvlog.bat")) {
    Write-Error "xvlog.bat was not found. Edit `$VivadoBin in this script to match your Vivado install."
    exit 1
}

& "$VivadoBin\xvlog.bat" -sv `
    research\copper_lsq_source_tag_tracker.sv `
    research\copper_commit_epoch_proof_bridge.sv `
    research\copper_line_provenance_gate.sv `
    research\copper_lsq_cepf_line_e2e_tb.sv
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

& "$VivadoBin\xelab.bat" copper_lsq_cepf_line_e2e_tb -s copper_lsq_cepf_line_e2e_tb_sim
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

& "$VivadoBin\xsim.bat" copper_lsq_cepf_line_e2e_tb_sim -runall
exit $LASTEXITCODE

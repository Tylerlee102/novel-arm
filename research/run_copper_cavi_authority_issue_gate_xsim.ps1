$VivadoBin = "C:\AMDDesignTools\2025.2\Vivado\bin"

if (!(Test-Path "$VivadoBin\xvlog.bat")) {
    Write-Error "xvlog.bat was not found. Edit `$VivadoBin in this script to match your Vivado install."
    exit 1
}

if (!(Test-Path "research\results")) {
    New-Item -ItemType Directory -Path "research\results" | Out-Null
}

& "$VivadoBin\xvlog.bat" -sv `
    research\copper_rocca_clpd_commit_adapter.sv `
    research\copper_clpd_gate.sv `
    research\copper_tlb_coherence_authority_filter.sv `
    research\copper_cavi_authority_issue_gate.sv `
    research\copper_cavi_authority_issue_gate_tb.sv
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

& "$VivadoBin\xelab.bat" copper_cavi_authority_issue_gate_tb -s copper_cavi_authority_issue_gate_tb_sim
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

& "$VivadoBin\xsim.bat" copper_cavi_authority_issue_gate_tb_sim -runall -log research\results\copper_cavi_authority_issue_gate_xsim_20260620.log
exit $LASTEXITCODE

$VivadoBin = "C:\AMDDesignTools\2025.2\Vivado\bin\vivado.bat"

if (!(Test-Path $VivadoBin)) {
    Write-Error "vivado.bat was not found. Edit `$VivadoBin in this script to match your Vivado install."
    exit 1
}

& $VivadoBin -mode batch -source research\run_copper_cavi_authority_issue_gate_synth.tcl -journal research\results\copper_cavi_authority_issue_gate_synth.jou -log research\results\copper_cavi_authority_issue_gate_synth.log
exit $LASTEXITCODE

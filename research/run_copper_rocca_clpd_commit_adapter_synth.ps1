$VivadoBin = "C:\AMDDesignTools\2025.2\Vivado\bin\vivado.bat"

if (!(Test-Path $VivadoBin)) {
    Write-Error "vivado.bat was not found. Edit `$VivadoBin in this script to match your Vivado install."
    exit 1
}

& $VivadoBin -mode batch -source research\run_copper_rocca_clpd_commit_adapter_synth.tcl -journal research\results\copper_rocca_clpd_commit_adapter_synth.jou -log research\results\copper_rocca_clpd_commit_adapter_synth.log
exit $LASTEXITCODE

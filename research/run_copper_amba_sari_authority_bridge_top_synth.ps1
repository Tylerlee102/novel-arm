$VivadoBin = "C:\AMDDesignTools\2025.2\Vivado\bin"

if (!(Test-Path "$VivadoBin\vivado.bat")) {
    Write-Error "vivado.bat was not found. Edit `$VivadoBin in this script to match your Vivado install."
    exit 1
}

if (!(Test-Path "research\results")) {
    New-Item -ItemType Directory -Path "research\results" | Out-Null
}

& "$VivadoBin\vivado.bat" -mode batch -source research\run_copper_amba_sari_authority_bridge_top_synth.tcl -journal research\results\copper_amba_sari_authority_bridge_top_synth.jou -log research\results\copper_amba_sari_authority_bridge_top_synth.log
exit $LASTEXITCODE

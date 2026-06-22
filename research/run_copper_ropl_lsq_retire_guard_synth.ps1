$VivadoBin = "C:\AMDDesignTools\2025.2\Vivado\bin"

if (!(Test-Path "$VivadoBin\vivado.bat")) {
    Write-Error "vivado.bat was not found. Edit `$VivadoBin in this script to match your Vivado install."
    exit 1
}

if (!(Test-Path "research\results")) {
    New-Item -ItemType Directory -Path "research\results" | Out-Null
}

& "$VivadoBin\vivado.bat" -mode batch -source research\run_copper_ropl_lsq_retire_guard_synth.tcl -journal research\results\copper_ropl_lsq_retire_guard_synth.jou -log research\results\copper_ropl_lsq_retire_guard_synth.log
exit $LASTEXITCODE

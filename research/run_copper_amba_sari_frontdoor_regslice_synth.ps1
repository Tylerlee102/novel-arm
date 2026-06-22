$Vivado = "C:\AMDDesignTools\2025.2\Vivado\bin\vivado.bat"
$CleanAppData = Join-Path (Resolve-Path ".").Path "research\results\vivado_clean_appdata"

if (!(Test-Path $Vivado)) {
    Write-Error "vivado.bat was not found. Edit `$Vivado in this script to match your Vivado install."
    exit 1
}

New-Item -ItemType Directory -Force -Path $CleanAppData | Out-Null
New-Item -ItemType Directory -Force -Path "research\results" | Out-Null
$env:XILINX_TCLAPP_REPO = "C:\AMDDesignTools\2025.2\Vivado\data\XilinxTclStore"
$env:APPDATA = $CleanAppData

& $Vivado -mode batch `
    -log research\results\copper_amba_sari_frontdoor_regslice_synth.log `
    -journal research\results\copper_amba_sari_frontdoor_regslice_synth.jou `
    -source research\run_copper_amba_sari_frontdoor_regslice_synth.tcl
exit $LASTEXITCODE

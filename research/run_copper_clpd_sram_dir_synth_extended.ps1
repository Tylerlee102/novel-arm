$Vivado = "C:\AMDDesignTools\2025.2\Vivado\bin\vivado.bat"
$CleanAppData = Join-Path (Resolve-Path ".").Path "research\results\vivado_clean_appdata"

if (!(Test-Path $Vivado)) {
    Write-Error "vivado.bat was not found. Edit `$Vivado in this script to match your Vivado install."
    exit 1
}

New-Item -ItemType Directory -Force -Path $CleanAppData | Out-Null
$env:XILINX_TCLAPP_REPO = "C:\AMDDesignTools\2025.2\Vivado\data\XilinxTclStore"
$env:APPDATA = $CleanAppData

& $Vivado -mode batch `
    -log research\results\copper_clpd_sram_dir_synth_extended.log `
    -journal research\results\copper_clpd_sram_dir_synth_extended.jou `
    -source research\run_copper_clpd_sram_dir_synth_extended.tcl
exit $LASTEXITCODE
